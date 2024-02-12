from flask import request

from openshift_ci_job_trigger.libs.job_triggering import JobTriggering
import os


from openshift_ci_job_trigger.utils.logger_utils import FLASK_APP

APP_ROOT_PATH = "/openshift_ci_job_trigger"


@FLASK_APP.route(f"{APP_ROOT_PATH}/healthcheck")
def healthcheck():
    return "alive"


@FLASK_APP.route(APP_ROOT_PATH, methods=["POST"])
def process_webhook():
    try:
        job_triggering = JobTriggering(hook_data=request.json, flask_logger=FLASK_APP.logger)
        job_triggering.execute()
        return "Process ended successfully."

    except Exception as ex:
        FLASK_APP.logger.error(f"Error get JSON from request: {ex}")
        return "Process failed"


def main():
    FLASK_APP.logger.info(f"Starting {FLASK_APP.name} app")
    FLASK_APP.run(
        port=int(os.environ.get("OPENSHIFT_CI_JOB_TRIGGER_PORT", 5000)),
        host="0.0.0.0",
        use_reloader=True if os.environ.get("OPENSHIFT_CI_JOB_TRIGGER_USE_RELOAD") else False,
    )


if __name__ == "__main__":
    main()
