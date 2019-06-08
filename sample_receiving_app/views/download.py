from flask import Flask, render_template, Blueprint, request, make_response, jsonify
import json, re, time, sys, os, yaml
from openpyxl import Workbook
from openpyxl.writer.excel import save_virtual_workbook

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
from flask_jwt_extended import (
    JWTManager,
    jwt_required,
    get_raw_jwt,
    create_access_token,
    jwt_refresh_token_required,
    create_refresh_token,
    get_jwt_identity,
)

from sample_receiving_app import app, db
from sample_receiving_app.logger import log_info, log_error
from sample_receiving_app.models import Submission

download = Blueprint('download', __name__)

VERSION = app.config["VERSION"]


@download.route('/download', methods=['GET'])
@jwt_required
def download_receipt():
    # payload = request.get_json()['data']
    # print(payload)
    submission = Submission.query.filter(
        Submission.username == request.args.get("username"),
        Submission.igo_request_id == request.args.get("igo_request_id"),
    ).first()
    wb = create_excel(submission)
    # responseObject = {
    #     # 'submissions': load_submissions(username),
    #     'user': payload["username"],
    #     # 'submission_columns': submission_columns,
    # }

    output = make_response(save_virtual_workbook(wb), 200)
    # output.headers["Content-Disposition"] = "attachment; filename=" + "sheet.xlsx"
    # output.headers[
    #     "Content-type"
    # ] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    # return make_response(jsonify(responseObject), 200, None)
    # response = HttpResponse(content=wb, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    # response['Content-Disposition'] = 'attachment; filename=myexport.xlsx'
    return output


# HELPERS


def is_authorized(result):
    return AUTHORIZED_GROUP in format_result(result)


def create_excel(submission):
    wb = Workbook()
    filename = submission.igo_request_id + ".xlsx"
    ws = wb.active

    form = json.loads(submission.form_values)
    grid = json.loads(submission.grid_values)
    form_cols =  list(form.keys())
    grid_cols = list(grid[0].keys())
    columns =  form_cols + grid_cols
    # columns.append(list(grid[0].keys()))
    ws.append(columns)
    for i, row in enumerate(grid):
        ws.append(list(form.values()) + list(grid[i].values()))
    
   
    return wb

    # for row in json.loads(submission.form_values).values():

    #     print(row)

    # ws.append(col)
    # print(ws)
