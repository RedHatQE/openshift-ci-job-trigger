import os

from flask import Flask, request

from openshift_ci_job_trigger.libs.job_triggering import JobTriggering

FLASK_APP = Flask("openshift-ci-job-trigger")
APP_ROOT_PATH = "/openshift_ci_job_trigger"


@FLASK_APP.route(f"{APP_ROOT_PATH}/healthcheck")
def healthcheck():
    return "alive"


@FLASK_APP.route(APP_ROOT_PATH, methods=["POST"])
def process_webhook():
    process_failed_msg = "Process failed"
    try:
        job_triggering = JobTriggering(hook_data=request.json, flask_logger=FLASK_APP.logger)
        job_triggering.execute()
    except Exception as ex:
        FLASK_APP.logger.error(f"Error get JSON from request: {ex}")
        return process_failed_msg


def main():
    FLASK_APP.logger.info(f"Starting {FLASK_APP.name} app")
    FLASK_APP.run(
        port=int(os.environ.get("OPENSHIFT-CI-JOB-TRIGGER_PORT", 5000)),
        host="0.0.0.0",
        use_reloader=bool(os.environ.get("OPENSHIFT-CI-JOB-TRIGGER_USE_RELOAD")),
    )


if __name__ == "__main__":
    main()
