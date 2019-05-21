from flask import Flask, session, render_template, Blueprint, request, make_response
import json, re, time, sys, os, yaml

import ldap
import hashlib
from datetime import timedelta

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
from flask_login import current_user, login_user, logout_user, login_required
from flask_wtf.csrf import generate_csrf


from sample_receiving_app import app, login_manager, db
from sample_receiving_app.logger import log_info, log_error
from sample_receiving_app.auth import User

common = Blueprint('common', __name__)

VERSION = app.config["VERSION"]
AUTHORIZED_GROUP = app.config["AUTHORIZED_GROUP"]

version_md5 = hashlib.md5(app.config["VERSION"].encode("utf-8")).hexdigest()


@common.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=30)


@common.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE")
    # response.set_cookie('csrf_token', generate_csrf())

    request_args = {key + ":" + request.args[key] for key in request.args}
    mrn_redacted_args = {}
    if request.path == "/CreateAnonID":
        for single_arg_key in request.args:
            single_arg = request.args[single_arg_key]
            mrn_redacted_args[single_arg_key] = re.sub("\d{8}", "********", single_arg)
        request_args = {key + ":" + mrn_redacted_args[key] for key in mrn_redacted_args}

    elif response.is_streamed == True:
        response_message = (
            "\n---Flask Request Args---\n"
            + "\n".join(request_args)
            + "\n---Flask Response---\n"
            + str(response.headers)
            + "\n"
            + "Streamed Data"
        )
    elif (
        request.path == "/getExcelFromColumnDef"
        or request.path == "/storeReceipt"
        or request.path == "/getReceipt"
        # or request.path == "/exportExcel"
    ):
        response_message = (
            "\n---Flask Request Args---\n"
            + "\n".join(request_args)
            + "\n---Flask Response---\n"
            + str(response.headers)
            + "\n"
            + "File Data"
        )
    else:
        response_message = (
            "\n---Flask Request Args---\n"
            + "\n".join(request_args)
            + "\n---Flask Response---\n"
            + str(response.headers)
            + "\n"
            + str(response.data)
        )
    # if request.path != "/login":
    log_info(response_message)
    return response


@common.route("/")
def welcome():
    return "SampleReceiving v2"


@common.route("/getVersion", methods=["GET"])
def get_version():
    return app.config["VERSION"]


@common.route("/checkVersion", methods=["GET"])
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


# @common.route("/login")
# def login():
#     username = request.args["username"]
#     password = request.args["password"]
#     return username


@common.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('You are already logged in')
        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        try:
            payload = request.get_json()['data']

            # print(payload)

            username = payload["username"]
            password = payload["password"]
        except:
            return make_response(
                'Missing username or password. Please try again.', 401, None
            )
        try:
            user = User.try_login(username, password)
            
        except ldap.INVALID_CREDENTIALS:
            log_error("user " + username + " trying to login with invalid credentials")
            return make_response(
                'Invalid username or password. Please try again.', 401, None
            )
        
        if is_authorized(user):
            log_info('authorized user loaded: ' + username)
            user = load_username(username)
            login_user(user)
            log_info("user " + username + " logged in successfully")

            return make_response(
                'You were logged in. Welcome to Sample Receiving.', 200, None
            )

        else:
            log_error("user " + username + " AD authenticated but not in GRP_SKI_Haystack_NetIQ")   
            return make_response(
                'Your user role is not authorized to view this webiste. Please email <a href="mailto:wagnerl@mkscc.org">delphi support</a> if you need any assistance.',
                403,
                None,
            )

        # user = load_username(username)
        # if not user:
        #     #  TODO change to role based
        #     log_error("user " + username + " AD authenticated but not in users table")

        #     return make_response(
        #         'Your user role is not authorized to view this webiste. Please email <a href="mailto:wagnerl@mkscc.org">delphi support</a> if you need any assistance.',
        #         403,
        #         None,
        #     )
        
           

    return make_response('r.text', 200, None)

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


def load_username(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(username)
        db.session.add(user)
        db.session.commit()
        log_info("New user added to users table: " + username )
    else: 
        log_info("Existing user retrieved: " + username )
    return user
