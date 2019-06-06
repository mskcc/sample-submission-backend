import sys
import ssl, copy, operator
import hashlib
import re
import datetime
from werkzeug import MultiDict
from flask import (
    Flask,
    render_template,
    Blueprint,
    json,
    jsonify,
    request,
    make_response,
)
from flask_jwt_extended import (
    jwt_required,
    jwt_refresh_token_required,
    get_jwt_identity,
)


from sample_receiving_app.possible_fields import possible_fields, submission_columns
from sample_receiving_app.logger import log_lims, log_info
from sample_receiving_app.models import User, Submission

import uwsgi, pickle
import requests


from sample_receiving_app import app, db

s = requests.Session()

VERSION = app.config["VERSION"]
CRDB_URL = app.config["CRDB_URL"]

version_md5 = hashlib.md5(VERSION.encode("utf-8")).hexdigest()


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


@upload.route("/upload/initialState", methods=["GET"])
@jwt_required
def initialState():
    username = get_jwt_identity()
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

    submissions = load_submissions(username)

    responseObject = {
        "applications": applications,
        "materials": materials,
        "species": species,
        "containers": containers,
        "submissions": submissions,
        "submission_columns": submission_columns,
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
@jwt_required
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
            print(possible_fields)
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
@jwt_required
def add_banked_samples():

    payload = request.get_json()['data']
    return_text = ""
    print(payload)
    user = load_user(get_jwt_identity())
    form_values = payload['form_values']
    grid_values = payload['grid_values']

    if "version" in payload:
        print(payload['version'])
        version_comparison = compare_version(payload["version"])
        if version_comparison == False:
            return make_response(version_mismatch_message, 401, None)
    else:
        return make_response(version_mismatch_message, 401, None)

    serviceId = form_values['igo_request_id']
    recipe = form_values['application']
    sampleType = form_values['material']

    transactionId = payload['transactionId']
    for table_row in payload['grid_values']:
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
            print('well in record')
            m = re.search("([A-Za-z]+)(\d+)", sample_record["wellPosition"])
            print(m)
            if not m:
                return make_response(
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
            auth=(LIMS_USER, LIMS_PW),
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

    submission = Submission(
        username=get_jwt_identity(),
        igo_request_id=form_values['igo_request_id'],
        form_values=str(form_values),
        grid_values=str(grid_values),
        submitted=True,
        submitted_on=datetime.datetime.fromtimestamp(transactionId).strftime(
            '%Y-%m-%d %H:%M:%S'
        ),
        version=VERSION,
    )
    commit_submission(submission)
    response = make_response(return_text, 200, None)
    return response


@app.route("/patientIdConverter", methods=["POST"])
# @jwt_required
def patientIdConverterd():
    payload = request.get_json()['data']
    params = (('mrn', payload["patient_id"]), ('sid', 'P1'))
    response = requests.get(CRDB_URL, params=params, auth=('cmoint', 'cmointp'))
    crdb_resp = (response.json())
    print(crdb_resp['PRM_JOB_STATUS'])
    print(payload["patient_id"])
    print(crdb_resp)
    if crdb_resp['PRM_JOB_STATUS'] == '0':
        responseObject = {
                'patient_id': crdb_resp['PRM_PT_ID'],
                'sex': crdb_resp['PRM_JOB_STATUS']
                # todo set empty
            }
        return make_response(jsonify(responseObject), 200, None)
    elif crdb_resp['PRM_JOB_STATUS'] == '1':
        responseObject = {
            'message': 'MRN not recognized'
            # todo set empty
        }
        return make_response(jsonify(responseObject), 422, None)
    else :
        responseObject = {
                'message': "Something went wrong with the CRDB endpoint, please contact zzPDL_SKI_IGO_DATA@mskcc.org.",
            }
        return make_response(jsonify(responseObject), 500, None)
        
    

# rex working with hpc, anna has been doing a bunch of information agthering 
@app.route("/listValues/<listname>", methods=["GET", "POST"])
@jwt_required
def picklist(listname):
    get_picklist(listname)
    response = jsonify(
        listname=listname, values=pickle.loads(uwsgi.cache_get(listname))
    )
    return response


@upload.route('/saveSubmission', methods=['POST'])
@jwt_required
def save_submission():
    payload = request.get_json()['data']
    if "version" in payload:
        print(payload['version'])
        version_comparison = compare_version(payload["version"])
        if version_comparison == False:
            return make_response(version_mismatch_message, 401, None)
    else:
        return make_response(version_mismatch_message, 401, None)

    # user = User.query.filter_by(username=payload['username']).first()
    form_values = payload['form_values']
    grid_values = payload['grid_values']
    username = get_jwt_identity()
    # save version in case of later edits that aren't compatible anymore
    submission = Submission(
        username=username,
        igo_request_id=form_values['igo_request_id'],
        form_values=json.dumps(form_values),
        grid_values=json.dumps(grid_values),
        version=VERSION,
    )
    try:
        commit_submission(submission)
    except Exception as e:
        print(e)
        responseObject = {
            'status': 'fail',
            'message': 'Our backend is experiencing some issues, please try again later or email zzPDL_SKI_IGO_DATA@mskcc.org.',
        }
        return make_response(jsonify(responseObject)), 500
    responseObject = {
        'submissions': load_submissions(username),
        'submission_columns': submission_columns,
    }

    return make_response(jsonify(responseObject), 200, None)


# get submissions for logged in user or username (admins?)
@upload.route('/getSubmissions', methods=['GET'])
@upload.route('/getSubmissions/<username>', methods=['GET'])
@jwt_required
def get_submissions(username=None):
    # payload = request.get_json()['data']
    if username == None:
        username = get_jwt_identity()
    print(username)
    user = load_user(username)

    responseObject = {
        'submissions': load_submissions(username),
        'user': user.username,
        'submission_columns': submission_columns,
    }
    return make_response(jsonify(responseObject), 200, None)


@upload.route('/deleteSubmission', methods=['POST'])
@jwt_required
def delete_submission():
    payload = request.get_json()['data']
    igo_request_id = (payload['igo_request_id'],)

    Submission.query.filter(
        Submission.username == get_jwt_identity(),
        Submission.igo_request_id == igo_request_id,
    ).delete()

    submissions = Submission.query.filter(
        Submission.username == get_jwt_identity()
    ).all()
    db.session.flush()
    db.session.commit()
    submissions_response = []
    for submission in submissions:
        submissions_response.append(submission.serialize)
        # columnDefs.append(copy.deepcopy(possible_fields[column[0]]))

    responseObject = {
        'submissions': submissions_response,
        'submission_columns': submission_columns,
    }
    return make_response(jsonify(responseObject), 200, None)


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


def load_user(username):
    return User.query.filter_by(username=username).first()


def commit_submission(new_submission):

    sub = Submission.query.filter(
        Submission.igo_request_id == new_submission.igo_request_id,
        Submission.username == new_submission.username,
    ).first()
    if sub:
        sub.username = new_submission.username
        sub.igo_request_id = new_submission.igo_request_id
        sub.form_values = new_submission.form_values
        sub.grid_values = new_submission.grid_values
        sub.submitted = new_submission.submitted
        sub.submitted_on = new_submission.submitted_on
        sub.version = new_submission.version
        db.session.flush()

    else:
        db.session.add(new_submission)
    return db.session.commit()


def load_submissions(username):
    submissions = Submission.query.filter(Submission.username == username).all()

    submissions_response = []
    for submission in submissions:
        submissions_response.append(submission.serialize)
        # columnDefs.append(copy.deepcopy(possible_fields[column[0]]))
    return submissions_response


def get_mskcc_username(request):
    if is_dev:
        return "wagnerl"
    else:
        request.headers["X-Mskcc-Username"]


def compare_version(client_version):
    client_version_md5 = hashlib.md5(client_version.encode("utf-8")).hexdigest()
    if client_version_md5 != version_md5:
        return False
    else:
        return True


def cache_oncotree():
    r = s.get(
        'http://oncotree.mskcc.org/api/tumorTypes?version=oncotree_candidate_release&flat=true&deprecated=false'
    ).json()
    oncotree_cache = list()
    dict_of_values = {}
    list_of_duplicates = []
    for record in r:
        value = record['name']
        if value in dict_of_values:
            unique_value = record['name'] + '(' + record['tissue'] + ')'
            if value not in list_of_duplicates:
                list_of_duplicates.append(value)
            oncotree_cache.append({"id": record['code'], "value": unique_value})
        else:
            oncotree_cache.append({"id": record['code'], "value": value})
            dict_of_values[value] = (
                str(record['name']) + '(' + str(record['tissue']) + ')'
            )
    for single_record in oncotree_cache:
        single_value = single_record['value']
        if single_value in list_of_duplicates:
            single_record['value'] = dict_of_values[single_value]
    return sorted(oncotree_cache, key=lambda x: x["value"])


def cache_reads_coverage():
    picklist_values = get_picklist("Sequencing+Coverage+Requested")
    del picklist_values[-1]
    picklist_values = picklist_values + get_picklist("Sequencing+Reads+Requested")
    return picklist_values


def cache_barcodes():
    r = s.get(
        LIMS_API_ROOT + "/LimsRest/getBarcodeList?user=Sampletron9000",
        auth=(USER, PASSWORD),
        verify=False,
    )
    log_lims(r)
    json_r = json.loads(r.content.decode('utf-8'))
    for record in json_r:
        if "name" in record:
            del record["name"]
    return json_r
