from sample_receiving_app import app
from flask import request
import inspect


def log_lims(lims_response):
    msg = (
        "\n---Lims Request Url---\n"
        + str(lims_response.url)
        + "\n---Lims Response---\nStatus code: "
        + str(lims_response.status_code)
        + "\n"
        + "Data: "
        + lims_response.text
    )
    app.logger.info(
        msg,
        # extra={
        #     "user_name": str(get_mskcc_username(request)),
        #     "function_name": inspect.stack()[1][3],
        #     "call_type": request.method,
        #     "flask_endpoint": request.path,
        # },
    )


def log_info(msg):
    info = (
        "FLASK_ENDPOINT: "
        + "\n"
        + str(request.path)
        + "\n"
        + "\nFUNCTION_NAME: "
        + inspect.stack()[1][3]
        + "\n"
        + "MESSAGE: "
        + str(msg)
    )

    #     # 'user_name': str(get_mskcc_username(request)),
    #     'function_name': inspect.stack()[1][3],
    #     'location': inspect.stack()[1][3],
    #     'call_type': request.method,
    #     'flask_endpoint': request.path,
    # }
    app.logger.info(info)



def log_error(msg):
    error = (
        "FLASK_ENDPOINT: "
        + "\n"
        + str(request.path)
        + "\n"
        + "\nFUNCTION_NAME: "
        + inspect.stack()[1][3]
        + "\n"
        + "MESSAGE: "
        + str(msg)
    )

    #     # 'user_name': str(get_mskcc_username(request)),
    #     'function_name': inspect.stack()[1][3],
    #     'location': inspect.stack()[1][3],
    #     'call_type': request.method,
    #     'flask_endpoint': request.path,
    # }
    app.logger.error(error)
