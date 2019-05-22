from flask import Flask, render_template, Blueprint, json, jsonify, request, make_response
from flask_login import current_user, login_user, logout_user, login_required


import sys
import ssl, copy, operator
from sample_receiving_app.possible_fields import possible_fields
from sample_receiving_app.logger import log_lims, log_info

import uwsgi, pickle
import requests


from sample_receiving_app import app

s = requests.Session()

LIMS_API_ROOT = app.config["LIMS_API_ROOT"]
LIMS_USER = app.config["LIMS_USER"]
LIMS_PW = app.config["LIMS_PW"]

is_dev = True

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
            "\n---Flask Request---\n"
            + "\n".join(request_args)
            + "\n---Flask Response---\n"
            + str(response.headers)
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
            "\n---Flask Request---\n"
            + "\n".join(request_args)
            # + "\n---Flask Response---\n"
            # + str(response.headers)
            + "Data: "
            + "File Data"
            + "\n"
        )
    else:
        response_message = (
            "\n---Flask Request---\n"
            + 'Args: '
            + "\n".join(request_args)
            + "\n"
            # + "\n---Flask Response---\n"
            # + str(response.headers)
            + "Data: "
            + str(response.data)
            + "\n"
        )
    app.logger.info(response_message)
    return response



@upload.route("/upload/initialState", methods=["GET"])
# @login_required
def initialState():
    
    applications = get_picklist("Recipe")
    materials = get_picklist("Exemplar+Sample+Types")
    species = get_picklist("Species")

    # send back error msg on case of sapio error?
    # {"applications":[{"id":"ERROR: com.velox.sapioutils.client.standalone.VeloxConnectionException: java.rmi.UnmarshalException:
    # if applications.match("C-[A-Z0-9]{6}", r.text):
    #    return make_response(r.text, 400, None)
    
    #  picklist?
    containers = [
        {"id": "Plates", "value": "Plates"},
        {"id": "Micronic Barcoded Tubes", "value": "Micronic Barcoded Tubes"},
        {"id": "Blocks/Slides/Tubes", "value": "Blocks/Slides/Tubes"},
    ]

    responseObject = {
        "applications":applications,
        "materials":materials,
        "species":species,
        "containers":containers,
        }

    return make_response(json.dumps(responseObject)), 200


    # return jsonify(
    #     applications=applications,
    #     materials=materials,
    #     species=species,
    #     containers=containers,
    #     # patientIdFormats=patientIdFormats,
    # )


@app.route("/columnDefinition", methods=["GET"])
@login_required
def getColumns():
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
            # log_info(possible_fields[column[0]])
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




@app.route("/addBankedSamples", methods=["POST"])
def add_banked_samples():

    payload = request.get_json()['data']
    return_text = ""
    print(payload)

    if "version" in payload:
        print(payload['version'])
        version_comparison = compare_version(payload["version"])
        if version_comparison == False:
            return make_response(version_mismatch_message, 401, None)
    else:
        return make_response(version_mismatch_message, 401, None)

    serviceId = payload['form']['igo_request_id']
    recipe = payload['form']['application']
    sampleType = payload['form']['material']

    transactionId = payload['transactionId']
    for table_row in payload['grid']:
        sample_record = table_row
        print(type(table_row))
        print(table_row)
        if ("X-Mskcc-Username" in request.headers) or is_dev:

            #  TODO LDAP AUTH
            sample_record["igoUser"] = get_mskcc_username(request)
            sample_record["investigator"] = get_mskcc_username(request)

            sample_record.update(table_row)
            print(sample_record)
        else:
            return make_response("IT IS FORBIDDEN!", 401, None)

        # API user for auditing
        sample_record["user"] = "Sampletron9000"
        sample_record["concentrationUnits"] = "ng/uL"
        if "wellPosition" in sample_record:
            m = re.search("([A-Za-z]+)(\d+)", table_row["wellPosition"])
            if not m:
                response = make_response(
                    "Unable to split wellPosition: %s" % table_row["wellPosition"],
                    400,
                    None,
                )
            else:
                sample_record["rowPos"] = m.group(1)
                sample_record["colPos"] = m.group(2)
                del sample_record["wellPosition"]
        for key, value in list(sample_record.items()):
            if value == "":
                del table_row[key]
        if "indexSequence" in sample_record:
            # don't send this back, we already know it, it was just for the user
            del sample_record["indexSequence"]
        # fix assay now
        sample_record["rowIndex"] = 1

        sample_record['serviceId'] = serviceId
        sample_record['recipe'] = recipe
        sample_record['sampleType'] = sampleType
        sample_record["transactionId"] = transactionId
        final_sample_record = MultiDict()
        final_sample_record.update(sample_record)
        try:
            # TODO multiselect assays in frontend
            assay_string = sample_record["assay"].replace("'", "")
            assay_array = assay_string.split(",")
            del final_sample_record["assay"]
            final_sample_record.setlist("assay", assay_array)
        except:
            pass
        # sample_record_url = url_encode(final_sample_record)
        data = final_sample_record
        r = requests.post(
            url=LIMS_API_ROOT + "/LimsRest/setBankedSample?",
            data=data,
            auth=(USER, PASSWORD),
            verify=False,
        )

        # TODO sort? by well position?
        # log_error(LIMS_API_ROOT + "/LimsRest/setBankedSample?" + sample_record_url)
        # r = s.post(
        #     LIMS_API_ROOT + "/LimsRest/setBankedSample?" + sample_record_url,
        #     auth=(USER, PASSWORD),
        #     verify=False,
        # )
        # print(sample_record_url)
        log_lims(r)
        if r.status_code == 200:
            return_text += r.text
        else:
            # not 200, something went wrong saving that record, bail out during save
            response = make_response(r.text, r.status_code, None)
            return response
    # must've got all 200!
    response = make_response(return_text, 200, None)
    return response


# -----------------HELPERS-----------------

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



def get_mskcc_username(request):
    if is_dev:
        return "wagnerl"
    else:
        request.headers["X-Mskcc-Username"]
