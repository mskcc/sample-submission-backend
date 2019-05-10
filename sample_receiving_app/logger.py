
from sample_receiving_app import app

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