import ldap
import jwt
import datetime

# from flask_login import UserMixin
from sample_receiving_app import app, db
from sample_receiving_app.models.blacklist_tokens import BlacklistToken

ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)


def get_ldap_connection():
    conn = ldap.initialize(app.config['AUTH_LDAP_URL'])
    conn.set_option(ldap.OPT_REFERRALS, 0)
    return conn


class User(db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(40), nullable=True)
    username = db.Column(db.String(40), nullable=False, unique=True)
    msk_group = db.Column(db.String(40), nullable=True)
    role = db.Column(db.String(40), nullable=True)

    def __init__(self, username, full_name=None, msk_group=None, role='user'):
        self.username = username
        self.msk_group = msk_group
        self.role = role
        self.full_name = full_name

    @staticmethod
    def try_login(username, password):
        conn = get_ldap_connection()

        conn.simple_bind_s('%s@mskcc.org' % username, password)
        attrs = ['memberOf']
        attrs = ['sAMAccountName', 'displayName', 'memberOf', 'title']
        result = conn.search_s(
            'DC=MSKCC,DC=ROOT,DC=MSKCC,DC=ORG',
            ldap.SCOPE_SUBTREE,
            'sAMAccountName=wagnerl',
            attrs,
        )

        conn.unbind_s()
        return result

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    @property
    def is_active(self):
        return True

    def get_id(self):
        return str(self.id)

    def get_user_name(self):
        return str(self.user_name)

    def get_full_name(self):
        return str(self.full_name)

    def get_msk_group(self):
        return str(self.msk_group)

    def get_role(self):
        return str(self.role)

    @property
    def serialize(self):
        """Return object data in easily serializable format"""
        return {
            'id': self.id,
            'username': self.username,
            'msk_group': self.msk_group,
            'role': self.role,
        }

    def encode_auth_token(self, user_id):
        """
        Generates the Auth Token
        :return: string
        """
        print(user_id)
        try:
            payload = {
                'exp': datetime.datetime.utcnow()
                + datetime.timedelta(days=0, seconds=5),
                'iat': datetime.datetime.utcnow(),
                'sub': user_id,
            }
            return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
        except Exception as e:
            return e

    @staticmethod
    def decode_auth_token(auth_token):
        """
        Validates the auth token
        :param auth_token:
        :return: integer|string
        """
        try:
            payload = jwt.decode(auth_token, app.config['SECRET_KEY'])
            is_blacklisted_token = BlacklistToken.check_blacklist(auth_token)
            if is_blacklisted_token:
                return 'Token blacklisted. Please log in again.'
            else:
                return payload['sub']
        except jwt.ExpiredSignatureError:
            return 'Signature expired. Please log in again.'
        except jwt.InvalidTokenError:
            return 'Invalid token. Please log in again.'


# class LoginForm(FlaskForm):
#     username = StringField('Username', [InputRequired('MSK username is required')])
#     password = PasswordField('Password', [InputRequired('Password is required')])
