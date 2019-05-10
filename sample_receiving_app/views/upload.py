from flask import Flask, render_template, Blueprint

import sys
import sample_receiving_app.possible_fields


upload = Blueprint('upload', __name__)



@upload.route("/upload/materialsAndApplications", methods=["GET"])
def materialsAndApplications():
    applications = get_picklist("Recipe")
    materials = get_picklist("Exemplar+Sample+Types")
    return jsonify(applications=applications, materials=materials)


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
                auth=(USER, PASSWORD),
                verify=False,
            )
            log_lims(r)
            picklist = []
            for value in json.loads(r.content.decode('utf-8')):
                picklist.append({"id": value, "value": value})
            uwsgi.cache_set(listname, pickle.dumps(picklist), 900)
        return pickle.loads(uwsgi.cache_get(listname))
