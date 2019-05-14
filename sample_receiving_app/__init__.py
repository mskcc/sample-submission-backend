from flask import Flask
from flask_cors import CORS
# from flask_sqlalchemy import SQLAlchemy
# from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
import logging
import os

from logging.config import dictConfig

dictConfig(
    {
        'version': 1,
        'formatters': {
            'default': {
                'format': '[%(asctime)s] HERA %(levelname)s in %(module)s: %(message)s'
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

# db = SQLAlchemy(app)


# login_manager = LoginManager()
# login_manager.init_app(app)
# login_manager.login_view = 'user.login'
# login_manager.login_message = ''


# User model/table creation
# from hera_app.auth import User

# SQLAlchemy only creates if not exist
# db.create_all()
# db.session.commit()

from .views.upload import upload

app.register_blueprint(upload)


from .views.common import common

app.register_blueprint(common)

# from .views.user import user
# app.register_blueprint(user)

# different blueprint naming because calling the blueprint and the view function 'dashboard'
# would mask the global name
# from .views.dashboard import dashboard_blueprint
# app.register_blueprint(dashboard_blueprint)
CORS(app)

csrf = CSRFProtect(app)
