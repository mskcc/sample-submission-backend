import sys
import ssl, copy, operator
import hashlib
import re
import datetime
from pytz import timezone
from tzlocal import get_localzone
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
import urllib.request, urllib.parse, urllib.error

from sample_submission_app.possible_fields import (
    possible_fields,
    submission_columns,
    human_applications,
    mouse_applications,
    human_or_mouse_applications,
    containers_for_material,
)
from sample_submission_app.logger import log_lims, log_info
from sample_submission_app.models import User, Submission

import uwsgi, pickle
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager

from sample_submission_app import app, db


VERSION = app.config["VERSION"]
CRDB_URL = app.config["CRDB_URL"]
CRDB_PASSWORD = app.config["CRDB_PASSWORD"]
CRDB_USERNAME = app.config["CRDB_USERNAME"]

version_md5 = hashlib.md5(VERSION.encode("utf-8")).hexdigest()


LIMS_API_ROOT = app.config["LIMS_API_ROOT"]
LIMS_USER = app.config["LIMS_USER"]
LIMS_PW = app.config["LIMS_PW"]

is_dev = True

upload = Blueprint('upload', __name__)


class MyAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_version=ssl.PROTOCOL_SSLv23,
        )


s = requests.Session()
s.mount("https://", MyAdapter())

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
    url = LIMS_API_ROOT + "/getIntakeTerms?"
    new_args = request.args.copy()
    r = s.get(url, params=new_args, auth=(LIMS_USER, LIMS_PW), verify=False)
    log_lims(r)
    columns = r.json()
    # if request was made for getting applications/recipes for selected material/type or vice versa
    if "type" not in request.args or "recipe" not in request.args:
        formatted_choices = []
        for value in r.json()[0]:
            formatted_choices.append({"id": value, "value": value})
        # some types/applications can only be submitted in specific containers
        #  and for specific species
        if "recipe" not in request.args and "type" in request.args:
            material = request.args["type"].replace('_PIPI_SLASH_', '/')
            containers = get_containers_for_material(material)
            return jsonify(choices=formatted_choices, containers=containers)
        if "recipe" in request.args and "type" not in request.args:
            application = request.args["recipe"]
            species = get_species_for_application(application)
            return jsonify(choices=formatted_choices, species=species)

        return jsonify(choices=formatted_choices)

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

        if column["data"] == "index":
            column["barcodeHash"] = barcode_hash()

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
        if "type" in column and column["type"] in ["autocomplete", "dropdown"]:
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

    serviceId = form_values['service_id']
    recipe = form_values['application']
    sampleType = form_values['material']
    transaction_id = payload['transaction_id']

    submission = Submission(
        username=get_jwt_identity(),
        service_id=form_values['service_id'],
        transaction_id=transaction_id,
        material=form_values['material'],
        application=form_values['application'],
        form_values=json.dumps(form_values),
        grid_values=json.dumps(grid_values),
        submitted=True,
        submitted_on=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        version=VERSION,
    )
    commit_submission(submission)

    for table_row in payload['grid_values']:
        sample_record = table_row
        if ("X-Mskcc-Username" in request.headers) or is_dev:

            #  TODO LDAP AUTH
            sample_record["igoUser"] = user.username
            sample_record["investigator"] = user.username

            sample_record.update(table_row)
            print(sample_record)
        else:
            return make_response("IT IS FORBIDDEN!", 401, None)

        # API user for auditing
        sample_record["user"] = "Sampletron9000"
        sample_record["concentrationUnits"] = "ng/uL"
        if "wellPosition" in sample_record:
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
        # if "cancerType" in sample_record:
        #     sample_record["cancerType"] = table_row["cancerType"].rsplit(' ID: ')[-1]

        sample_record['serviceId'] = serviceId
        sample_record['recipe'] = recipe
        sample_record['sampleType'] = sampleType
        sample_record["transactionId"] = transaction_id
        final_sample_record = MultiDict()
        final_sample_record.update(sample_record)

        data = final_sample_record
        r = requests.post(
            url=LIMS_API_ROOT + "/setBankedSample?",
            data=data,
            auth=(LIMS_USER, LIMS_PW),
            verify=False,
        )

        # TODO sort? by well position?
        # log_error(LIMS_API_ROOT + "/setBankedSample?" + sample_record_url)
        # r = s.post(
        #     LIMS_API_ROOT + "/setBankedSample?" + sample_record_url,
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


@app.route("/updateBankedSamples", methods=["POST"])
@jwt_required
def update_banked_samples():

    payload = request.get_json()['data']
    return_text = ""
    user = load_user(get_jwt_identity())
    grid_values = payload['grid_values']

    transaction_id = payload['transaction_id']

    for table_row in payload['grid_values']:
        sample_record = table_row
        if ("X-Mskcc-Username" in request.headers) or is_dev:

            #  TODO LDAP AUTH
            sample_record["igoUser"] = user.username
            sample_record["investigator"] = user.username

            sample_record.update(table_row)
            print(sample_record)
        else:
            return make_response("IT IS FORBIDDEN!", 401, None)

        # API user for auditing
        sample_record["user"] = "Sampletron9000"
        sample_record["concentrationUnits"] = "ng/uL"
        if "wellPosition" in sample_record:
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
        # if "cancerType" in sample_record:
        #     sample_record["cancerType"] = table_row["cancerType"].rsplit(' ID: ')[-1]

        sample_record["transactionId"] = transaction_id
        final_sample_record = MultiDict()
        final_sample_record.update(sample_record)

        data = final_sample_record
        r = requests.post(
            url=LIMS_API_ROOT + "/setBankedSample?",
            data=data,
            auth=(LIMS_USER, LIMS_PW),
            verify=False,
        )

        # TODO sort? by well position?
        # log_error(LIMS_API_ROOT + "/setBankedSample?" + sample_record_url)
        # r = s.post(
        #     LIMS_API_ROOT + "/setBankedSample?" + sample_record_url,
        #     auth=(USER, PASSWORD),
        #     verify=False,
        # )
        # print(sample_record_url)
        log_lims(r)
        if r.status_code == 200:
            return_text = json.dumps(payload['grid_values'])
        else:
            # not 200, something went wrong saving that record, bail out during save
            response = make_response(r.text, r.status_code, None)
            return response
    # must've got all 200!

    response = make_response(return_text, 200, None)
    return response


@app.route("/patientIdConverter", methods=["POST"])
# @jwt_required
def patientIdConverterd():
    payload = request.get_json()['data']
    data = {
        "username": CRDB_USERNAME,
        "password": CRDB_PASSWORD,
        "mrn": payload["patient_id"],
        "sid": "P2",
    }
    headers = {'Content-type': 'application/json'}
    response = s.post(CRDB_URL, data=json.dumps(data), headers=headers)

    crdb_resp = response.json()
    if 'PRM_JOB_STATUS' in crdb_resp:
        if crdb_resp['PRM_JOB_STATUS'] == '0':
            responseObject = {
                'patient_id': crdb_resp['PRM_PT_ID'],
                'sex': crdb_resp['PRM_PT_GENDER']
                # todo set empty
            }
            return make_response(jsonify(responseObject), 200, None)
        elif crdb_resp['PRM_JOB_STATUS'] == '1':
            responseObject = {
                'message': 'MRN not recognized'
                # todo set empty
            }
            return make_response(jsonify(responseObject), 422, None)
    else:
        responseObject = {
            'message': "Something went wrong with the CRDB endpoint, please contact zzPDL_SKI_IGO_DATA@mskcc.org."
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
    transaction_id = payload['transaction_id']

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
        service_id=form_values['service_id'],
        transaction_id=None,
        material=form_values['material'],
        application=form_values['application'],
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
    if user.get_role() == 'member' or user.get_role() == 'super':
        submissions = load_all_submissions()
    else:
        submissions = load_submissions(username)
    responseObject = {
        'submissions': submissions,
        'user': user.username,
        'submission_columns': submission_columns,
    }
    return make_response(jsonify(responseObject), 200, None)


@upload.route('/deleteSubmission', methods=['POST'])
@jwt_required
def delete_submission():
    payload = request.get_json()['data']
    service_id = (payload['service_id'],)
    sub_username = (payload['username'],)

    Submission.query.filter(
        Submission.username == sub_username, Submission.service_id == service_id
    ).delete()

    db.session.flush()
    db.session.commit()

    user = load_user(get_jwt_identity())
    if user.get_role() == 'member' or user.get_role() == 'super':
        submissions_response = load_all_submissions()
    else:
        submissions_response = load_submissions(username)

    responseObject = {
        'submissions': submissions_response,
        'submission_columns': submission_columns,
    }
    return make_response(jsonify(responseObject), 200, None)


@upload.route('/allColumnsPromote', methods=['GET'])
def get_all_columns_promote_json():
    columns = get_all_columns_promote()
    return jsonify(columnDefs=columns)


def get_all_columns_promote():
    ordering = get_picklist("ReceiptPromote+Ordering")
    print(ordering)
    #    colDefs = copy.deepcopy(list(possible_fields.values()))
    all_columns = []
    #    for column in colDefs:
    for column_index in ordering:
        (_, column_name) = column_index['id'].split(":")
        try:
            print(column_name)
            column = copy.deepcopy(possible_fields[column_name])
        except:
            column = {
                "name": column_name,
                "columnHeader": column_name,
                "width": 150,
                "data": make_it_camel_case(column_name),
                # "editableCellTemplate": editableCellTemplate,
                "displayName": column_name,
            }
            print(column)
        column['headerCellClass'] = 'optional'
        # pull dropdowns from LIMS API and inject into column definition, unless already filled out
        # if column['editableCellTemplate'] in [
        #     'uiSelect',
        #     'uiMultiSelect',
        #     'uiTagSelect',
        #     'ui-grid/dropdownEditor',
        # ]:
        #     if 'editDropdownOptionsArray' not in column:
        #         column['editDropdownOptionsArray'] = get_picklist(
        #             column['picklistName']
        #         )
        if "type" in column and column["type"] in ["autocomplete", "dropdown"]:
            if "source" not in column:
                print(column)
                column["source"] = get_picklist(column["picklistName"])
            if "optional" in column and column["optional"] == True:
                column["source"].append({"id": "", "value": "Clear Field"})
        if column['data'] == 'investigator':
            column["cellEditableCondition"] = False
        all_columns.append(column)
    return all_columns


@app.route('/getSamples', methods=['GET'])
def get_samples():
    # investigator = request.args.get('investigator')
    requestId = request.args.get('serviceId')
    if not requestId:
        return make_response("Must supply request Id", 400, None)
    query = LIMS_API_ROOT + "/getBankedSamples?"
    query += urllib.parse.urlencode(request.args)
    # log_info(query)
    r = s.post(query, auth=(LIMS_USER, LIMS_PW), verify=False)
    log_lims(r)
    r_json = r.json()
    response_dict = []
    for single_sample in r_json:
        if 'readSummary' in single_sample:
            single_sample['requestedReads'] = single_sample.pop('readSummary')
        if 'barcodeId' in single_sample:
            single_sample['index'] = single_sample.pop('barcodeId')
        if 'concentration' in single_sample:
            single_sample['concentration'] = single_sample['concentration'].replace(
                'ng/uL', ''
            )
        response_dict.append(single_sample)
    return make_response(
        json.dumps(response_dict), r.status_code, {"mimetype": 'application/json'}
    )


@upload.route('/promoteBankedSample', methods=['POST'])
@jwt_required
def promote_sample():
    promote_urlargs = dict()
    payload = request.get_json()['data']
    print(payload)
    username = get_jwt_identity()
    print(username)
    promote_urlargs['bankedId'] = payload['bankedId']
    promote_urlargs['requestId'] = payload['requestId']
    promote_urlargs['serviceId'] = payload['serviceId']
    promote_urlargs['projectId'] = payload['projectId']
    promote_urlargs['dryrun'] = payload['dryrun']
    promote_urlargs['igoUser'] = username
    print(promote_urlargs)
    for key in list(promote_urlargs.keys()):
        if promote_urlargs[key] == None or promote_urlargs[key] == '':
            promote_urlargs[key] = "NULL"

    # try:
    #     promote_urlargs['igoUser'] = get_mskcc_username(request)
    # except:
    #     promote_urlargs['igoUser'] = 'dev_' + getpass.getuser()
    promote_urlargs['user'] = 'Sampletron9000'
    promote_url_root = LIMS_API_ROOT + "/promoteBankedSample"
    r = s.post(
        promote_url_root, data=promote_urlargs, auth=(LIMS_USER, LIMS_PW), verify=False
    )

    log_lims(r)
    if r.status_code == 200:
        return make_response(r.text, 200, None)
    else:
        return make_response(r.text, r.status_code, None)


# ---------------------HELPERS------------------------
# @app.route("/barcodeHash/", methods=["GET"])
def barcode_hash():
    barcode_list = get_picklist("Tag")
    barcode_hash = dict()
    for barcode in barcode_list:
        barcode_hash[barcode["barcodId"].lower()] = barcode
    return json.dumps(barcode_hash)


def get_species_for_application(application):
    application = application.lower()
    for hm in human_applications:
        if application in hm or hm in application:
            return [{'id': 'Human', 'value': 'Human'}]
    for mm in mouse_applications:
        if application in mm or mm in application:
            return [{'id': 'Mouse', 'value': 'Mouse'}]
    for hom in human_or_mouse_applications:
        if application in hom or hom in application:
            return [
                {'id': 'Human', 'value': 'Human'},
                {'id': 'Mouse', 'value': 'Mouse'},
            ]
    return []


def get_containers_for_material(material):
    if material in containers_for_material:
        return containers_for_material[material]["containers"]
    return []


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
                LIMS_API_ROOT + "/getPickListValues?list=%s" % listname,
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
        Submission.service_id == new_submission.service_id,
        Submission.username == new_submission.username,
    ).first()

    if sub:
        sub.username = new_submission.username
        sub.service_id = new_submission.service_id
        sub.transaction_id = new_submission.transaction_id
        sub.material = new_submission.material
        sub.application = new_submission.application
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


def load_all_submissions():
    submissions = Submission.query.all()

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
        LIMS_API_ROOT + "/getBarcodeList?user=Sampletron9000",
        auth=(LIMS_USER, LIMS_PW),
        verify=False,
    )
    log_lims(r)
    json_r = json.loads(r.content.decode('utf-8'))
    for record in json_r:
        if "name" in record:
            del record["name"]
    return json_r


def make_it_camel_case(word):
    notReallyCamelCase = ''.join(
        singleChar for singleChar in word.title() if not singleChar.isspace()
    )
    camelCase = notReallyCamelCase[0].lower() + notReallyCamelCase[1:]
    return camelCase
