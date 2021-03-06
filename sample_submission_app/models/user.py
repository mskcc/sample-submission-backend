import ldap
import jwt
import datetime
from flask_sqlalchemy import event

# from flask_login import UserMixin
from sample_submission_app import app, db
import sample_submission_app.models
from sample_submission_app.logger import log_info, log_error

ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)


def get_ldap_connection():
    conn = ldap.initialize(app.config['AUTH_LDAP_URL'])
    conn.set_option(ldap.OPT_REFERRALS, 0)
    return conn


# three roles:
# user: can submit
# member: can see all submissions
# super: can promote
supers = [
    'bourquec',
    'chend',
    'cobbsc',
    'duniganm',
    'hubermak',
    'kochr1',
    'kumarn1',
    'lingL',
    'mcmanamd',
    'meadea',
    'melcerm',
    'pantanom',
    'patrunoa',
    'raop',
    'rezae',
    'selcukls',
    'sharmaa1',
    'vannessk',
    'vialea',
    'wagnerl',
    'zimelc',
]
members = [
    'cavatorm',
    'chenj3',
    'driscolk',
    'guzowskd',
    'hongr',
    'hwangk2',
    'jingx',
    'lauj',
    'lia1',
    'lij',
    'michaeea',
    'mohibuln',
    'murakamis',
    'naborsd',
    'patelr1',
    'pereze1',
    'ramakris',
    'scacalod',
    'scaglion',
    'sonir1',
    'sunl',
    'wenrichr',
    'youd',
]


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
        # attrs = ['memberOf']
        attrs = ['sAMAccountName', 'displayName', 'memberOf', 'title']
        result = conn.search_s(
            'DC=MSKCC,DC=ROOT,DC=MSKCC,DC=ORG',
            ldap.SCOPE_SUBTREE,
            'sAMAccountName='+username,
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


def insert_initial_values(*args, **kwargs):
    for user in supers:
        db.session.add(User(username=user, role='super'))
    for user in members:
        db.session.add(User(username=user, role='member'))
    db.session.commit()


event.listen(User.__table__, 'after_create', insert_initial_values)
