import os

import click
import requests
import yaml
from simple_logger.logger import get_logger
from timeout_sampler import TimeoutSampler
from pyaml_env import parse_config


LOGGER = get_logger(name=os.path.split(__file__)[-1])
GANGWAY_API_URL = "https://gangway-ci.apps.ci.l2s4.p1.openshiftapps.com/v1/executions/"


def authorization_header(openshift_ci_token):
    return {"Authorization": f"Bearer {openshift_ci_token}"}


def get_prow_job_status(openshift_ci_token, triggering_job_id):
    response = requests.get(
        url=f"{GANGWAY_API_URL}{triggering_job_id}",
        headers=authorization_header(openshift_ci_token=openshift_ci_token),
    )

    response_text = yaml.safe_load(response.text)
    if response.ok:
        return response_text["job_status"]

    LOGGER.error(f"Failed to get job status: {response_text}")
    raise click.Abort()


def wait_for_job_completed(openshift_ci_token, triggering_job_id):
    for sample in TimeoutSampler(
        wait_timeout=600,
        sleep=60,
        print_log=False,
        func=get_prow_job_status,
        openshift_ci_token=openshift_ci_token,
        triggering_job_id=triggering_job_id,
    ):
        if sample and sample == "SUCCESS":
            return


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

    LOGGER.success(f"Successfully triggered job {openshift_ci_job_name}")


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
        # Update CLI user input from YAML file if exists
        # Since CLI user input has some defaults, YAML file will override them
        user_kwargs.update(parse_config(path=job_yaml_config_file, default_value=""))

    openshift_ci_token = kwargs.get("openshift_ci_token")
    openshift_ci_job_name = kwargs.get("openshift_ci_job_name")
    triggering_job_id = kwargs.get("prow_triggering_job_id")
    if triggering_job_id:
        wait_for_job_completed(
            openshift_ci_token=openshift_ci_token,
            triggering_job_id=triggering_job_id,
        )

    # TODO: Check only one trigger per job.
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
