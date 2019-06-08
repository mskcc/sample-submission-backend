from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy, event
from flask_login import LoginManager, AnonymousUserMixin
from flask_wtf.csrf import CSRFProtect
from flask_jwt_extended import (
    JWTManager,
    jwt_required,
    create_access_token,
    get_jwt_identity,
)
import logging
import os, sys
sys.path.insert(0, os.path.abspath(".."))

from logging.config import dictConfig


dictConfig(
    {
        'version': 1,
        'formatters': {
            'default': {
                'format': '[%(asctime)s] %(message)s'
                # 'format': '[%(asctime)s] SAMPLE.REC.BE %(levelname)s in %(module)s: %(message)s'
            }
        },
        'handlers': {
            'wsgi': {
                'class': 'logging.StreamHandler',
                'stream': 'ext://flask.logging.wsgi_errors_stream',
                'formatter': 'default',
            }
        },
        'root': {'level': 'INFO', 'handlers': ['wsgi']},
    }
)


app = Flask(__name__)
app.config.from_pyfile("../secret_config.py")

db = SQLAlchemy(app)

app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']
jwt = JWTManager(app)

from sample_receiving_app.models import BlacklistToken, User, Submission

@jwt.token_in_blacklist_loader
def check_if_token_in_blacklist(decrypted_token):
    jti = decrypted_token['jti']
    return BlacklistToken.is_jti_blacklisted(jti)


class Anonymous(AnonymousUserMixin):
    def __init__(self):
        self.username = 'Anonymous'


login_manager = LoginManager()
login_manager.anonymous_user = Anonymous
login_manager.init_app(app)
# login_manager.login_view = 'user.login'
# login_manager.login_message = ''


# User model/table creation

# SQLAlchemy only creates if not exist
db.create_all()

# db.session.add(User(username='test'))
# db.session.add(User(username='test2'))
# db.session.add(User(username='test3'))

db.session.commit()


from .views.upload import upload

app.register_blueprint(upload)

from .views.download import download

app.register_blueprint(download)


from .views.user import user

app.register_blueprint(user)

# from .views.user import user
# app.register_blueprint(user)

# different blueprint naming because calling the blueprint and the view function 'dashboard'
# would mask the global name
# from .views.dashboard import dashboard_blueprint
# app.register_blueprint(dashboard_blueprint)
CORS(app)

# csrf = CSRFProtect(app)
