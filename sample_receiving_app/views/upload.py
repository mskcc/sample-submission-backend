from flask import Flask, render_template, Blueprint, json, jsonify, request


import sys
import sample_receiving_app.possible_fields
from sample_receiving_app.logger import log_lims

import uwsgi, pickle
import requests


from sample_receiving_app import app

s = requests.Session()
# s.mount("https://", MyAdapter())

LIMS_API_ROOT = app.config["LIMS_API_ROOT"]
LIMS_USER = app.config["LIMS_USER"]
LIMS_PW = app.config["LIMS_PW"]


upload = Blueprint('upload', __name__)


# @upload.route("/upload/materialsAndApplications", methods=["GET"])
# def materialsAndApplications():
#     applications = get_picklist("Recipe")
#     materials = get_picklist("Exemplar+Sample+Types")
#     return jsonify(applications=applications, materials=materials)
@upload.after_request
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



@upload.route("/upload/initialState", methods=["GET"])
def initialState():
    applications = get_picklist("Recipe")
    materials = get_picklist("Exemplar+Sample+Types")
    species = get_picklist("Species")

    # send back error msg on case of sapio error?
    # {"applications":[{"id":"ERROR: com.velox.sapioutils.client.standalone.VeloxConnectionException: java.rmi.UnmarshalException:
    # if applications.match("C-[A-Z0-9]{6}", r.text):
    #    return make_response(r.text, 400, None)
    containers = [
        {"id": "Plates", "value": "Plates"},
        {"id": "Micronic Barcoded Tubes", "value": "Micronic Barcoded Tubes"},
        {"id": "Blocks/Slides/Tubes", "value": "Blocks/Slides/Tubes"},
    ]
    # patientIdFormats = [
    #     {"id": "MRN", "value": "MRN"},
    #     {"id": "User Provided Patient ID", "value": "User Provided Patient ID"},
    #     {
    #         "id": "Combination of MRN and User Provided",
    #         "value": "Combination of MRN and User Provided",
    #     },
    #     {"id": "Mouse Parental Strain ID", "value": "Mouse Parental Strain ID"},
    # ]

    return jsonify(
        applications=applications,
        materials=materials,
        species=species,
        containers=containers,
        # patientIdFormats=patientIdFormats,
    )


@app.route("/columnDefinition", methods=["GET"])
def submission():
    url = LIMS_API_ROOT + "/LimsRest/getIntakeTerms?"
    new_args = request.args.copy()
    r = s.get(url, params=new_args, auth=(LIMS_USER, LIMS_PW), verify=False)
    log_lims(r)
    columns = r.json()
    if "type" not in request.args or "recipe" not in request.args:
        formatted = []
        for value in r.json()[0]:
            formatted.append({"id": value, "value": value})
        return jsonify(choices=formatted)

    if len(columns) == 0:
        return make_response("Invalid Combination:", 400, None)
    columnDefs = []
    required_field_names = [d[0] for d in columns if (d[1] == "Required")]
    for column in columns:
        try:
            columnDefs.append(copy.deepcopy(possible_fields[column[0]]))
        except:
            log_info(column[0] + " not found in possible_fields")

    for column in columnDefs:
        # cell class styling based on what fields are required for this sequencinyg typing
        if column["name"] in required_field_names:
            column["optional"] = False
            if column["name"] == "Patient ID":
                column[
                    "helpText"
                ] = "For MSKCC patients, MRN is preferred. For non-MSKCC patient samples, mouse samples, or cell lines without patient origin, please use this field to provide us with group names i.e. compare this group (A) with this group (B). For CMO projects, fill out something unique and correspond with your PM for more information."
        else:
            column["optional"] = True
        # pull dropdowns from LIMS API and inject into column definition, unless already filled out
        if column["editableCellTemplate"] in [
            "uiSelect",
            "uiMultiSelect",
            "uiTagSelect",
            "ui-grid/dropdownEditor",
        ]:
            if "source" not in column:
                print(column)
                column["source"] = get_picklist(column["picklistName"])
            if column["optional"] == True:
                column["source"].append({"id": "", "value": "Clear Field"})
    # ordered_columns = fix_col_ordering(dream_order_sample_submission,columnDefs)
    response = jsonify(columnDefs=columnDefs)
    # for column in ordered_columns:
    #    print column['field']
    return response


# HELPERS


def get_picklist(listname):
    if uwsgi.cache_exists(listname):
        return pickle.loads(uwsgi.cache_get(listname))
    else:
        # three lists have special GETs but eventually they will be a picklist
        if listname == "tumorType":
            #            picklist_values['tumorType']={ "cache_date": time.time(), "values":cache_oncotree()}
            uwsgi.cache_set(listname, pickle.dumps(cache_oncotree()), 900)
        elif listname == "Tag":
            #            picklist_values['Tag']={ "cache_date": time.time(), "values": cache_barcodes()}
            uwsgi.cache_set(listname, pickle.dumps(cache_barcodes()), 900)
            if uwsgi.cache_get(listname) == None:
                return cache_barcodes()
        elif listname == "Reads+Coverage":
            uwsgi.cache_set("Reads+Coverage", pickle.dumps(cache_reads_coverage()), 900)
        else:
            r = s.get(
                LIMS_API_ROOT + "/LimsRest/getPickListValues?list=%s" % listname,
                auth=(LIMS_USER, LIMS_PW),
                verify=False,
            )
            log_lims(r)
            picklist = []
            for value in json.loads(r.content.decode('utf-8')):
                picklist.append({"id": value, "value": value})
            uwsgi.cache_set(listname, pickle.dumps(picklist), 900)
        return pickle.loads(uwsgi.cache_get(listname))
