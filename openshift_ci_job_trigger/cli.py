import os

import click
import requests
import yaml
from simple_logger.logger import get_logger
from timeout_sampler import TimeoutSampler
from pyaml_env import parse_config
import json
import re


LOGGER = get_logger(name=os.path.split(__file__)[-1])
GANGWAY_API_URL = "https://gangway-ci.apps.ci.l2s4.p1.openshiftapps.com/v1/executions/"


def authorization_header(openshift_ci_token):
    return {"Authorization": f"Bearer {openshift_ci_token}"}


def get_prow_job_status(openshift_ci_token, triggering_job_id):
    response = requests.get(
        url=f"{GANGWAY_API_URL}{triggering_job_id}",
        headers=authorization_header(openshift_ci_token=openshift_ci_token),
    )

    return yaml.safe_load(response.text).get("job_status")


def wait_for_job_completed(openshift_ci_token, triggering_job_id):
    LOGGER.info(f"Waiting for build {triggering_job_id} to end.")
    current_job_status = None
    for job_status in TimeoutSampler(
        wait_timeout=600,
        sleep=60,
        print_log=False,
        func=get_prow_job_status,
        openshift_ci_token=openshift_ci_token,
        triggering_job_id=triggering_job_id,
    ):
        if job_status:
            if job_status != "PENDING":
                return
            if current_job_status != job_status:
                current_job_status = job_status
                LOGGER.info(f"Job status: {current_job_status}")


def verify_no_running_jobs(openshift_ci_job_name):
    response = requests.get(f"https://prow.ci.openshift.org/job-history/gs/origin-ci-test/logs/{openshift_ci_job_name}")

    if job_all_builds := re.search(r"allBuilds = (.*?);", response.text):
        all_builds = json.loads(job_all_builds.group(1))
        if pending_jobs := [(job["ID"], job["Started"]) for job in all_builds if job["Result"] == "PENDING"]:
            LOGGER.error(f"Job {openshift_ci_job_name} already has some runnig jobs: {pending_jobs}")
            raise click.Abort()


def triger_openshift_ci_job(
    openshift_ci_token,
    openshift_ci_job_name,
):
    response = requests.post(
        url=f"{GANGWAY_API_URL}{openshift_ci_job_name}",
        headers=authorization_header(openshift_ci_token=openshift_ci_token),
        json={"job_execution_type": "1"},
    )

    if not response.ok:
        LOGGER.error(f"Failed to get job status: {response.headers["grpc-message"]}")
        raise click.Abort()

    LOGGER.success(
        f"Successfully triggered job {openshift_ci_job_name}, prow job id: {json.loads(response.content.decode())['id']}"
    )


@click.command("job-trigger`")
@click.option(
    "-t",
    "--openshift-ci-token",
    help="Openshift ci token, needed to trigger jobs.",
    default=os.environ.get("OPENSHIFT_CI_TOKEN"),
)
@click.option(
    "-n",
    "--openshift-ci-job-name",
    help="Openshift ci job name",
    default=os.environ.get("JOB_NAME"),
    show_default=True,
    type=click.STRING,
)
@click.option(
    "-id",
    "--prow-triggering-job-id",
    help="Prow ID (prowjobid) of the job to be re-triggered. If empty, the job will be triggered immediately.",
    default=os.environ.get("PROW_JOB_ID"),
    show_default=True,
    type=click.STRING,
)
@click.option(
    "--job-yaml-config-file",
    help="YAML file with configuration for job triggering. See manifests/config.example.yaml for example.",
    type=click.Path(exists=True),
)
@click.option(
    "--pdb",
    help="Drop to `ipdb` shell on exception",
    is_flag=True,
    show_default=True,
)
def main(**kwargs):
    user_kwargs = kwargs
    if job_yaml_config_file := user_kwargs.get("job_yaml_config_file"):
        user_kwargs.update(parse_config(path=job_yaml_config_file, default_value=""))

    if not (openshift_ci_token := kwargs.get("openshift_ci_token")):
        LOGGER.error(
            "openshift ci token is mandatory. Either set `OPENSHIFT_CI_TOKEN` environment variable or pass `--openshift-ci-token`"
        )
        raise click.Abort()

    if not (openshift_ci_job_name := kwargs.get("openshift_ci_job_name")):
        LOGGER.error(
            "openshift ci job name is mandatory. Either set `JOB_NAME` environment variable or pass `--openshift-ci-job-name`"
        )
        raise click.Abort()

    if triggering_job_id := kwargs.get("prow_triggering_job_id"):
        wait_for_job_completed(
            openshift_ci_token=openshift_ci_token,
            triggering_job_id=triggering_job_id,
        )

    # TODO: If need to wait - where do we run? A job in PSI? can we do that from openshift ci?
    verify_no_running_jobs(openshift_ci_job_name=openshift_ci_job_name)
    triger_openshift_ci_job(
        openshift_ci_token=openshift_ci_token,
        openshift_ci_job_name=openshift_ci_job_name,
    )


if __name__ == "__main__":
    should_raise = False
    _logger = get_logger(name="main-openshift-ci-job-trigger")
    try:
        main()
    except Exception as ex:
        import sys
        import traceback

        ipdb = __import__("ipdb")  # Bypass debug-statements pre-commit hook

        if "--pdb" in sys.argv:
            extype, value, tb = sys.exc_info()
            traceback.print_exc()
            ipdb.post_mortem(tb)
        else:
            _logger.error(ex)
            should_raise = True
    finally:
        if should_raise:
            sys.exit(1)
