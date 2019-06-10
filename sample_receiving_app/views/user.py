from flask import (
    Flask,
    session,
    render_template,
    Blueprint,
    request,
    make_response,
    jsonify,
)
import json, re, time, sys, os, yaml

import ldap
import hashlib
from datetime import timedelta

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
from flask_login import current_user, login_user, logout_user, login_required
from flask_wtf.csrf import generate_csrf
from flask_jwt_extended import (
    JWTManager,
    jwt_required,
    get_raw_jwt,
    create_access_token,
    jwt_refresh_token_required,
    create_refresh_token,
    get_jwt_identity,
)

from sample_receiving_app import app, login_manager, db
from sample_receiving_app.logger import log_info, log_error
from sample_receiving_app.models import User, BlacklistToken, Submission
from sample_receiving_app.possible_fields import submission_columns
from sample_receiving_app.views.upload import load_submissions, load_all_submissions

user = Blueprint('user', __name__)

VERSION = app.config["VERSION"]
AUTHORIZED_GROUP = app.config["AUTHORIZED_GROUP"]

version_md5 = hashlib.md5(app.config["VERSION"].encode("utf-8")).hexdigest()


# @user.before_request
# def make_session_permanent():
#     session.permanent = True
#     app.permanent_session_lifetime = timedelta(minutes=30)


@user.route("/")
def welcome():
    return "SampleReceiving v2"


@user.route("/getVersion", methods=["GET"])
def get_version():
    return app.config["VERSION"]


@user.route("/checkVersion", methods=["GET"])
def check_version():
    client_version = request.args["version"]
    version_comparison = compare_version(client_version)
    if version_comparison == False:
        return make_response(
            json.dumps({"message": version_mismatch_message}), 418, None
        )
    else:
        return make_response(json.dumps({"version": version_md5}), 200, None)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def load_username(username):
    return User.query.filter_by(username=username).first()


# @user.route("/login")
# def login():
#     username = request.args["username"]
#     password = request.args["password"]
#     return username


@user.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        try:
            try:
                payload = request.get_json()['data']
                username = payload["username"]
                password = payload["password"]
            except:
                responseObject = {
                    'message': 'Missing username or password. Please try again.'
                }
                return make_response(jsonify(responseObject), 401, None)
            try:
                result = User.try_login(username, password)
            except ldap.INVALID_CREDENTIALS:
                log_error(
                    "user " + username + " trying to login with invalid credentials"
                )
                responseObject = {
                    'message': 'Invalid username or password. Please try again.'
                }
                return make_response(jsonify(responseObject), 401, None)

            if is_authorized(result):
                log_info('authorized user loaded: ' + username)
                # load or register user
                user = load_username(username)
                # Create our JWTs
                access_token = create_access_token(identity=username)
                refresh_token = create_refresh_token(identity=username)

                responseObject = {
                    'status': 'success',
                    'message': 'Hello, '
                    + username
                    + '. You have successfully logged in.',
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'username': username,
                    'submissions': load_submissions(username),
                    'submission_columns': submission_columns,
                }

                log_info("user " + username + " logged in successfully")
                return make_response(jsonify(responseObject), 200, None)
            else:
                log_error(
                    "user "
                    + username
                    + " AD authenticated but not in GRP_SKI_Haystack_NetIQ"
                )
                return make_response(
                    'Your user role is not authorized to view this webiste. Please email <a href="mailto:wagnerl@mkscc.org">sample intake support</a> if you need any assistance.',
                    403,
                    None,
                )
        except Exception as e:
            print(e)
            responseObject = {
                'status': 'fail',
                'message': 'Our backend is experiencing some issues, please try again later or email an admin.',
            }
            return make_response(jsonify(responseObject)), 500
    return make_response(
        'Something went wrong, please try to login again or contact an admin.',
        401,
        None,
    )


@user.route('/logoutAccess')
@jwt_required
def logoutAccess():
    jti = get_raw_jwt()['jti']
    try:
        revoked_token = BlacklistToken(jti=jti)
        revoked_token.add()
        responseObject = {
            'status': 'success',
            'message': 'Access token has been revoked',
        }
        logout_user()
        return make_response(jsonify(responseObject)), 200

    except Exception as e:
        responseObject = {'status': 'fail', 'message': e}
        return make_response(jsonify(responseObject)), 200


@user.route('/logoutRefresh', methods=['GET'])
@jwt_refresh_token_required
def logoutRefresh():
    jti = get_raw_jwt()['jti']
    try:
        revoked_token = BlacklistToken(jti=jti)
        revoked_token.add()
        responseObject = {
            'status': 'success',
            'message': 'Refresh token has been revoked',
        }
        logout_user()
        return make_response(jsonify(responseObject)), 200

    except Exception as e:
        responseObject = {'status': 'fail', 'message': e}
        return make_response(jsonify(responseObject)), 200


@user.route('/refresh', methods=['GET'])
@jwt_refresh_token_required
def refresh():
    current_jwt_user = get_jwt_identity()
    access_token = create_access_token(identity=current_jwt_user)
    return jsonify({'access_token': access_token, 'username': current_jwt_user}), 201


# HELPERS


def compare_version(client_version):
    client_version_md5 = hashlib.md5(client_version.encode("utf-8")).hexdigest()
    if client_version_md5 != version_md5:
        return False
    else:
        return True


def is_authorized(result):
    return AUTHORIZED_GROUP in format_result(result)


def format_result(result):
    p = re.compile('CN=(.*?)\,')
    groups = re.sub('CN=Users', '', str(result))
    return p.findall(groups)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# @login_manager.request_loader
# def load_user_from_request(request):
#     auth_header = request.headers.get('Authorization')
#     if auth_header:
#         auth_token = auth_header.split(" ")[1]
#     else:
#         auth_token = ''
#     if auth_token:
#         resp = User.decode_auth_token(auth_token)
#         if not isinstance(resp, str):
#             user = User.query.filter_by(id=resp).first()
#             log_info('token okay ' + user.username)
#             return user
#     else:
#         log_info('token expired ')
#         return None


def load_username(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(username)
        db.session.add(User(username=username, role='user'))
        db.session.commit()
        log_info("New user added to users table: " + username)
    else:
        log_info("Existing user retrieved: " + username)
    return user


@app.after_request
def after_request(response):

    # response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE")
    request_args = {key + ":" + request.args[key] for key in request.args}
    mrn_redacted_args = {}
    if request.path == "/CreateAnonID":
        for single_arg_key in request.args:
            single_arg = request.args[single_arg_key]
            mrn_redacted_args[single_arg_key] = re.sub("\d{8}", "********", single_arg)
        request_args = {key + ":" + mrn_redacted_args[key] for key in mrn_redacted_args}
    if response.is_streamed == True:
        response_message = (
            "\n---Flask Request---\n"
            + "\n".join(request_args)
            + "\n"
            + "Streamed Data"
            + "\n"
        )
    elif (
        request.path == "/getExcelFromColumnDef"
        or request.path == "/storeReceipt"
        or request.path == "/getReceipt"
        or request.path == "/exportExcel"
    ):
        response_message = (
            "Args: "
            + "\n".join(request_args)
            + "Data: File Data"
            + "\n"
            + "User: "
            + str(get_jwt_identity())
            + "\n"
        )
    if  "/columnDefinition" in request.path :    
         response_message = (
            'Args: '
            + "\n".join(request_args)
            + "\n"
            + "User: "
            + str(get_jwt_identity())
            + "\n"
        )
    else:
        response_message = (
            'Args: '
            + "\n".join(request_args)
            + "\n"
            + "Data: "
            + str(response.data)
            + "\n"
            + "User: "
            + str(get_jwt_identity())
            + "\n"
        )
    log_info(response_message)
    return response
