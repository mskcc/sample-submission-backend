editableCellTemplate = """<div><form name="inputForm"><input class="form-control inputheight" type="INPUT_TYPE" ng-class="'colt' + col.uid" ui-grid-editor ng-model="MODEL_COL_FIELD" ng-paste="grid.appScope.handleCellPaste($event)"></form></div>"""
editableNumberCellTemplate = """<div><form name="inputForm"><input class="form-control inputheight" type="INPUT_TYPE" ng-class="'colt' + col.uid" ui-grid-editor ng-model="MODEL_COL_FIELD" ng-paste="grid.appScope.handleCellPaste($event)"></form></div>"""

percent_tumor_options = [
    {"id": "Normal", "value": "Normal"},
    {"id": ".01", "value": "1%"},
    {"id": ".05", "value": "5%"},
    {"id": ".1", "value": "10%"},
    {"id": ".15", "value": "15%"},
    {"id": ".20", "value": "20%"},
    {"id": ".30", "value": "30%"},
    {"id": ".40", "value": "40%"},
    {"id": ".50", "value": "50%"},
    {"id": ".60", "value": "60%"},
    {"id": ".70", "value": "70%"},
    {"id": ".80", "value": "80%"},
    {"id": ".90", "value": "90%"},
    {"id": ".95", "value": "95%"},
    {"id": "1.0", "value": "100%"},
]


validation_patterns = {
    "userId": "^[A-Za-z0-9](?!.*__)[A-Za-z0-9\\,_-]{2}[A-Za-z0-9\\,_-]*$",
    "patientId": "^[A-Za-z0-9][A-Za-z0-9\\,_-]*$",
    "number": "^[0-9.]*$",
    "collectionYear": "\d{4}|^$",
    "wellPosition": "[A-Za-z]+\d+|^$",
    "micronicTubeBarcode": "^[0-9]{10}$",
    "alphanum": "[0-9a-zA-Z]",
    # "mskPatients": "d{8}",
    # "nonMSKPatients": "[0-9a-zA-Z]{4,}",
    # "bothMSKAndNonMSKPatients": "[0-9a-zA-Z]{4,}|d{8}",
}

human_applications = [
    'expanded_genomics ',
    'msk-access',
    'hemepact',
    'archer',
    'impact',
    'humanwholegenome',
]

mouse_applications = ['mousewholegenome ', 'm-impact_v1']


human_or_mouse_applications = ['wholeexomesequencing']


submission_columns = [
    {'name': 'Service ID', 'data': 'igo_request_id', 'readOnly': 'true'},
    {'name': 'User ID', 'data': 'username', 'readOnly': 'true'},
    {'name': 'Sample Type', 'data': 'sample_type', 'readOnly': 'true'},
    {'name': 'Application', 'data': 'application', 'readOnly': 'true'},
    {
        'name': 'Submitted to IGO?',
        'data': 'submitted',
        'readOnly': 'true',
        'renderer': 'html',
    },
    {'name': 'Date Created', 'data': 'created_on', 'readOnly': 'true'},
    {'name': 'Date Submitted', 'data': 'submitted_on', 'readOnly': 'true'},
    {'name': 'Transaction ID', 'data': 'transaction_id', 'readOnly': 'true'},
    {'name': 'App Version', 'data': 'version', 'readOnly': 'true'},
    {'name': 'Edit', 'data': 'edit', 'renderer': 'html'},
    {'name': 'Receipt', 'data': 'receipt', 'renderer': 'html'},
    {'name': 'Delete', 'data': 'delete', 'renderer': 'html'},
]


possible_fields = {
    "Service ID": {
        "name": "Service ID",
        "columnHeader": "Service ID",
        "data": "serviceId",
        "pattern": str(validation_patterns["alphanum"]),
        # "editable": "true",
        # "resizable":"true",
        # "width": 120,
        "editableCellTemplate": editableCellTemplate,
    },
    "Micronic Tube Barcode": {
        "name": "Micronic Tube Barcode",
        "columnHeader": "Micronic Tube Barcode",
        "data": "micronicTubeBarcode",
        "pattern": str(validation_patterns["micronicTubeBarcode"]),
        # "editable": "true",
        # "resizable":"true",
        # "width": 150,
        "editableCellTemplate": editableCellTemplate,
        "tooltip": "The Micronic Tube Barcode has been provided to you in advance by the sample receiving team.  If you cannot find it, the Micronic Tube Barcode is located on the side of the tube, and the 2D barcode can be scanned by a reade",
    },
    "Block/Slide/TubeID": {
        "name": "Block/Slide/TubeID",
        "columnHeader": "Block/Slide/TubeID",
        "data": "tubeId",
        "pattern": str(validation_patterns["alphanum"]),
        # "editable": "true",
        # "resizable":"true",
        "tooltip": "The identifier on your tube, block or slide.  You can paste in directly from excel, and there are no formatting rules.  Please be as correct as possible, and ensure your tubes, blocks and slides are labeled clearly.",
        "editableCellTemplate": editableCellTemplate,
        # "width": 150,
    },
    "Plate ID": {
        "name": "Plate ID",
        "columnHeader": "Plate ID",
        "data": "plateId",
        "pattern": str(validation_patterns["alphanum"]),
        # "editable": "true",
        # "resizable":"true",
        "tooltip": "The plate ID is the barcode on your plate.  Please scan, or carefully type, the barcode ID into this field for all samples on the plate",
        "editableCellTemplate": editableCellTemplate,
        # "width": 120,
    },
    "Well Position": {
        "name": "Well Position",
        "columnHeader": "Well Position",
        "data": "wellPosition",
        "pattern": str(validation_patterns["wellPosition"]),
        # "editable": "true",
        # "resizable":"true",
        "tooltip": "Fill Plate by Column. It must have at least one letter followed by a number",
        "error": "Well Position must have at least one letter followed by a number",
        "editableCellTemplate": editableCellTemplate,
        # "width": 120,
    },
    "Known Genetic Alterations": {
        "name": "Known Genetic Alterations",
        "columnHeader": "Known Genetic Alterations",
        "data": "knownGeneticAlteration",
        "pattern": str(validation_patterns["alphanum"]),
        # "editable": "true",
        # "resizable":"true",
        "editableCellTemplate": editableCellTemplate,
        # "width": 120,
    },
    "Sample ID": {
        "name": "Sample ID",
        "columnHeader": "Sample ID",
        "data": "userId",
        "pattern": str(validation_patterns["alphanum"]),
        # "editable": "true",
        # "resizable":"true",
        "tooltip": "The Sample ID stays with your sample for its lifetime. Letters, numbers, dashes, and underscores only, three char min. You cannot have more than one underscore consecutively.",
        "editableCellTemplate": editableCellTemplate,
        # "width": 120,
    },
    "Species": {
        "name": "Species",
        "columnHeader": "Species",
        "data": "organism",
        "readOnly": True,
        # "editable": "true",
        # "resizable":"true",
        "tooltip": "If your species is not available, please contact IGO immediately",
        "editableCellTemplate": "ui-grid/dropdownEditor",
        # editor select is a simpler version of type dropdown
        # "editor": "select",
        "type": "dropdown",
        # "width": 120,
        "picklistName": "Species",
    },
    "Nucleic Acid Type": {
        "name": "Nucleic Acid Type",
        "columnHeader": "Nucleic Acid Type",
        "data": "nucleicAcidType",
        # "editable": "true",
        # "resizable":"true",
        "editableCellTemplate": "ui-grid/dropdownEditor",
        # editor select is a simpler version of type dropdown
        # "editor": "select",
        "type": "dropdown",
        # "width": 120,
        "picklistName": "Exemplar+Sample+Types",
    },
    "Preservation": {
        "name": "Preservation",
        "columnHeader": "Preservation",
        "data": "preservation",
        # "editable": "true",
        # "resizable":"true",
        "tooltip": "The preservation method of your material is critical to understanding how to process your samples and anticipate issues.  Please complete as accurately as possible. If your preservation is not listed, please contact IGO",
        "editableCellTemplate": "ui-grid/dropdownEditor",
        # editor select is a simpler version of type dropdown
        # "editor": "select",
        "type": "dropdown",
        # "width": 120,
        "picklistName": "Preservation",
    },
    "Sample Origin": {
        "name": "Sample Origin",
        "columnHeader": "Sample Origin",
        "data": "sampleOrigin",
        # "editable": "true",
        # "resizable":"true",
        "tooltip": "The sample origin is important for analysis.  Please complete as accurately as possible.",
        "editableCellTemplate": "ui-grid/dropdownEditor",
        # editor select is a simpler version of type dropdown
        # "editor": "select",
        "type": "dropdown",
        "picklistName": "Sample+Origins",
        # "width": 120,
    },
    "Specimen Type": {
        "name": "Specimen Type",
        "columnHeader": "Specimen Type",
        "data": "specimenType",
        # "editable": "true",
        # "resizable":"true",
        "tooltip": "The specimen type is important for analysis.  Please complete as accurately as possible.",
        "editableCellTemplate": "ui-grid/dropdownEditor",
        # editor select is a simpler version of type dropdown
        # "editor": "select",
        "type": "dropdown",
        "picklistName": "Specimen+Types",
        # "width": 120,
    },
    "Sequencing Read Length": {
        "name": "Sequencing Read Length",
        "columnHeader": "Sequencing Read Length",
        "data": "sequencingReadLength",
        # "editable": "true",
        # "resizable":"true",
        "tooltip": "If you are unsure of what read length is needed, please contact your data analyst or IGO.  There are different read lengths for different applications and we are happy to suggest a length. If you do not see your read length listed, please contact IGO immediately",
        # FIXME
        "editableCellTemplate": "ui-grid/dropdownEditor",
        # editor select is a simpler version of type dropdown
        # "editor": "select",
        "type": "dropdown",
        "picklistName": "Illumina+Sequencing+Run+Types",
        # "width": 200,
    },
    "Reads Requested/Coverage": {
        "name": "Reads Requested/Coverage",
        "columnHeader": "Reads Requested/Coverage",
        "data": "requestedReads",
        # "editable": "true",
        # "resizable":"true",
        "tooltip": "Please tell us how many reads you would us to generate per sample.  If you are submitting for custom capture or whole exome capture, please tell us how much coverage you would like.  If you are submitting pre-made libraries, you must request by lane.  If you are using a custom sequencing primer, you must request an entire flow cell. Please contact IGO if you have any questions",
        "editableCellTemplate": "ui-grid/dropdownEditor",
        # editor select is a simpler version of type dropdown
        # "editor": "select",
        "type": "dropdown",
        "picklistName": "Reads+Coverage",
        # "width": 200,
    },
    "Index": {
        "name": "Index",
        "columnHeader": "Index",
        "data": "index",
        "pattern": str(validation_patterns["alphanum"]),
        # "editable": "true",
        # "resizable":"true",
        "tooltip": "This list represents barcodes that are already registered with IGO.  Please select from the list.  If you are submitting custom barcodes, you must pre-register them with IGO, and confirm your design and construct in advance.  Once you have identified the barcode by name, the sequence will appear in the adjacent field.  Please confirm that the sequence is expected based on your documentation.",
        "editableCellTemplate": editableCellTemplate,
        # "width": 150,
    },
    "Barcode Position": {
        "name": "Barcode Position",
        "columnHeader": "Barcode Position",
        "data": "barcodePosition",
        # "editable": "true",
        # "resizable":"true",
        "tooltip": "Please let us know what position the barcode is expected to be found.  Standard Illumina Index barcodes are located in position 42-46",
        "editableCellTemplate": editableCellTemplate,
        # "width": 150,
    },
    "Index Sequence": {
        "name": "Index Sequence",
        "columnHeader": "Index Sequence",
        "data": "indexSequence",
        "readOnly": True,
        # "editable": "true",
        # "resizable":"true",
        "tooltip": "Actual barcode sequence based on tag you choose display only",
        "editableCellTemplate": editableCellTemplate,
        "enableCellEdit": "false",
        # "width": 150,
    },
    "Nucleic Acid Type to Extract": {
        "name": "Nucleic Acid Type to Extract",
        "columnHeader": "Nucleic Acid Type to Extract",
        "data": "naToExtract",
        # "editable": "true",
        # "resizable":"true",
        "tooltip": "For samples submitted for extraction, please tell us what we should extract out of the material.",
        "editableCellTemplate": "ui-grid/dropdownEditor",
        # editor select is a simpler version of type dropdown
        # "editor": "select",
        "type": "dropdown",
        "picklistName": "Nucleic+Acid+Type+to+Extract",
        "width": 190,
    },
    "Cell Count": {
        "name": "Cell Count",
        "columnHeader": "Cell Count",
        "data": "cellCount",
        # "editable": "true",
        # "resizable":"true",
        "tooltip": "Please tell us the number of cells in your sorted population.  This number is important for us to provide you with the best extraction results.",
        "tooltip": "numberOfCells",
        "editableCellTemplate": editableCellTemplate,
        # "width": 150,
    },
    "Volume (uL)": {
        "name": "Volume (uL)",
        "columnHeader": "Volume (uL)",
        "data": "vol",
        "pattern": str(validation_patterns["number"]),
        "error": "Numbers only, please.",
        # "editable": "true",
        # "resizable":"true",
        "tooltip": "Please provide us with the volume of sample in microliters.  Please note there are different requirements for each application, and if you have any questions, please contact IGO.",
        "editableCellTemplate": editableCellTemplate,
        # "width": 150,
    },
    "Concentration (ng/uL)": {
        "name": "Concentration (ng/uL)",
        "columnHeader": "Concentration (ng/uL)",
        "data": "concentration",
        "pattern": str(validation_patterns["number"]),
        # "editable": "true",
        "error": "Numbers only, please.",
        "tooltip": "You must supply this in nanograms per microliter.  If you are unsure, please provide us with an approximation.",
        "editableCellTemplate": editableCellTemplate,
        # "width": 150,
    },
    "Quantity of Tubes": {
        "name": "Quantity of Tubes",
        "columnHeader": "Quantity of Tubes",
        "data": "numTubes",
        "pattern": str(validation_patterns["number"]),
        "error": "Numbers only, please.",
        # "editable": "true",
        # "resizable":"true",
        # "type": "number",
        "tooltip": "Number of Tubes per sample.  If you are submitting slides, please use this field to tell us how many slides per sample you will submit.",
        "editableCellTemplate": editableCellTemplate,
        # "width": 150,
    },
    "Assay(s)": {
        "name": "Assay(s)",
        "columnHeader": "Assay(s)",
        "data": "assay",
        # "editable": "true",
        # "resizable":"true",
        "type": "dropdown",
        "tooltip": "This field is multi-select.  If you are submitting one sample for multiple assays, please select the first, followed by the second, than the third, in the order of priority.",
        "editableCellTemplate": "uiMultiSelect",
        # "width": 300,
        "picklistName": "ddPCR+Assay",
    },
    "Estimated % Tumor": {
        "name": "Estimated % Tumor",
        "columnHeader": "Estimated % Tumor",
        "data": "estimatedPurity",
        # "editable": "true",
        # "resizable":"true",
        "editableCellTemplate": "ui-grid/dropdownEditor",
        # editor select is a simpler version of type dropdown, dropdown needs source instead of selectOptions
        # "editor": "select",
        "type": "dropdown",
        "source": percent_tumor_options,
        # "width": 150,
    },
    "Collection Year": {
        "name": "Collection Year",
        "columnHeader": "Collection Year",
        "data": "collectionYear",
        "pattern": str(validation_patterns["collectionYear"]),
        "error": "Numbers only, please.",
        # "editable": "true",
        # "resizable":"true",
        # "type": "number",
        "tooltip": "Years only, dates are PHI and are unacceptable",
        "editableCellTemplate": editableCellTemplate,
        # "width": 150,
    },
    "Tumor Type": {
        "name": "Tumor Type",
        "columnHeader": "Tumor Type",
        "data": "cancerType",
        # "editable": "true",
        # "resizable":"true",
        "editableCellTemplate": "ui-grid/dropdownEditor",
        # editor select is a simpler version of type dropdown
        # "editor": "select",
        "type": "dropdown",
        "picklistName": "tumorType",
        # "width": 150,
    },
    "Sample Class": {
        "name": "Sample Class",
        "columnHeader": "Sample Class",
        "data": "sampleClass",
        # "editable": "true",
        # "resizable":"true",
        "tooltip": "Please provide us with detailed information about the Tumor or Normal status, and please be as precise as possible.  This value is critical for data analysis.",
        "editableCellTemplate": "ui-grid/dropdownEditor",
        # editor select is a simpler version of type dropdown
        # "editor": "select",
        "type": "dropdown",
        "picklistName": "Sample+Class",
        # "width": 150,
    },
    "Tissue Site": {
        "name": "Tissue Site",
        "columnHeader": "Tissue Site",
        "data": "tissueType",
        "pattern": str(validation_patterns["alphanum"]),
        # "editable": "true",
        # "resizable":"true",
        "tooltip": "Site where tumor removed. If unknown, leave blank.",
        "editableCellTemplate": editableCellTemplate,
        # "width": 150,
    },
    "Patient ID": {
        "name": "Patient ID",
        "columnHeader": "Patient ID",
        "data": "patientId",
        "pattern": str(validation_patterns["alphanum"]),
        # "editable": "true",
        # "resizable":"true",
        #            "tooltip":"For MSKCC patients, please type or paste in the patient's mskPatients.  CRDB will provide IGO with de-identified patient ID's that will exist in a 1:1 fashion for perpetuity, across all submissions and studies.  For non-MSKCC patient samples, mouse samples, or cell lines without patient origin, please use this field to provide us with group names i.e. compare this group (A) with this group (B)",
        "tooltip": "For non-MSKCC patient samples, mouse samples, or cell lines without patient origin, please use this field to provide us with group names i.e. compare this group (A) with this group (B). For CMO projects, fill out something unique and correspond with your PM for more information.",
        "editableCellTemplate": editableCellTemplate,
        # "patterns": {
        #     "mskPatients": validation_patterns.mskPatients,
        #     "nonMSKPatients": validation_patterns.nonMSKPatients,
        #     "bothMSKAndNonMSKPatients": validation_patterns.bothMSKAndNonMSKPatients,
        # }
        # "width": 150,
    },
    "Normalized Patient Id": {
        "name": "Normalized Patient Id",
        "columnHeader": "Normalized Patient Id",
        "data": "normalizedPatientId",
        "readOnly": True,
        # "editable": "true",
        # "resizable":"true",
        "cellEditableCondition": False,
        "tooltip": "Normalized Patient Id that is sent to CMO service",
        "editableCellTemplate": editableCellTemplate,
        # "width": 150,
    },
    "CMO Patient Id": {
        "name": "CMO Patient Id",
        "columnHeader": "CMO Patient Id",
        "data": "cmoPatientId",
        "readOnly": True,
        # "editable": "true",
        # "resizable":"true",
        "cellEditableCondition": False,
        "tooltip": "CMO anonymized patient id",
        "editableCellTemplate": editableCellTemplate,
        # "width": 150,
    },
    "Sex": {
        "name": "Sex",
        "columnHeader": "Sex",
        "data": "gender",
        # "editable": "true",
        # "resizable":"true",
        "tooltip": "Sex information is important for calling Copy-Number Variations on sex chromosome (X,Y) genes.  Without this information, you may miss important data during analysis.  If you have any questions, please contact Platform Informatics",
        "editableCellTemplate": "ui-grid/dropdownEditor",
        # editor select is a simpler version of type dropdown
        # "editor": "select",
        "type": "dropdown",
        "picklistName": "Gender",
        # "width": 150,
    },
    "Known Genetic Alteration": {
        "name": "Known Genetic Alteration",
        "columnHeader": "Known Genetic Alteration",
        "data": "geneticAlterations",
        "pattern": str(validation_patterns["alphanum"]),
        # "editable": "true",
        # "resizable":"true",
        "tooltip": "If known, otherwise leave blank.",
        "editableCellTemplate": editableCellTemplate,
        "width": 190,
    },
    "Clinical Info": {
        "name": "Clinical Info",
        "columnHeader": "Clinical Info",
        "data": "clinicalInfo",
        # "editable": "true",
        # "resizable":"true",
        "editableCellTemplate": editableCellTemplate,
        # "width": 150,
    },
    "Sample Type": {
        "name": "Sample Type",
        "columnHeader": "Sample Type",
        "headerCellClass": "optional",
        "optional": "true",
        "data": "sampleType",
        "pattern": str(validation_patterns["alphanum"]),
        # "editable": "true",
        # "resizable":"true",
        "editableCellTemplate": editableCellTemplate,
        # "width": 120,
    },
    "Recipe": {
        "name": "Recipe",
        "columnHeader": "Recipe",
        "headerCellClass": "optional",
        "optional": "true",
        "data": "recipe",
        "pattern": str(validation_patterns["alphanum"]),
        # "editable": "true",
        # "resizable":"true",
        "editableCellTemplate": editableCellTemplate,
        # "width": 120,
    },
    "CMO Sample Type": {
        "name": "CMO Sample Type",
        "columnHeader": "CMO Sample Type",
        "headerCellClass": "optional",
        "optional": "true",
        "data": "specimenType",
        "pattern": str(validation_patterns["alphanum"]),
        # "editable": "true",
        # "resizable":"true",
        "editableCellTemplate": editableCellTemplate,
        # "width": 120,
    },
    "Spike In Genes": {
        "name": "Spike In Genes",
        "columnHeader": "Spike In Genes",
        "headerCellClass": "optional",
        "optional": "true",
        "data": "spikeInGenes",
        "pattern": str(validation_patterns["alphanum"]),
        # "editable": "true",
        # "resizable":"true",
        "editableCellTemplate": editableCellTemplate,
        # "width": 120,
    },
    "Platform": {
        "name": "Platform",
        "columnHeader": "Platform",
        "headerCellClass": "optional",
        "optional": "true",
        "pattern": str(validation_patterns["alphanum"]),
        "data": "platform",
        # "editable": "true",
        # "resizable":"true",
        "editableCellTemplate": editableCellTemplate,
        # "width": 120,
    },
}
