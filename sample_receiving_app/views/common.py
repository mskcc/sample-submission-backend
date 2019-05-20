from flask import Flask, render_template, Blueprint, request, make_response
import json, re, time, sys, os, yaml


import hashlib
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager


from sample_receiving_app import app


common = Blueprint('common', __name__)


version_md5 = hashlib.md5(app.config["VERSION"].encode("utf-8")).hexdigest()


@common.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
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
        or request.path == "/exportExcel"
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
    app.logger.info(response_message)
    return response


@common.route("/")
def welcome():
    return "SampleTron 9000"



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

@common.route("/login")
def login():
        username = request.args["username"]
        password = request.args["password"]
        return username


def compare_version(client_version):
    client_version_md5 = hashlib.md5(client_version.encode("utf-8")).hexdigest()
    if client_version_md5 != version_md5:
        return False
    else:
        return True
