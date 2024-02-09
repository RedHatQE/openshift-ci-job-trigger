import os

import click
import requests
import yaml
from simple_logger.logger import get_logger
from timeout_sampler import TimeoutSampler


LOGGER = get_logger(name=os.path.split(__file__)[-1])


def get_prow_job_status(openshift_ci_token, triggering_job_id):
    response = requests.get(
        url=f"https://gangway-ci.apps.ci.l2s4.p1.openshiftapps.com/v1/executions/{triggering_job_id}",
        headers={"Authorization": f"Bearer {openshift_ci_token}"},
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
        url=f"https://gangway-ci.apps.ci.l2s4.p1.openshiftapps.com/v1/executions/{openshift_ci_job_name}",
        headers={"Authorization": f"Bearer {openshift_ci_token}"},
    )

    response_text = yaml.safe_load(response.text)
    if response.ok:
        return response_text["job_status"]

    LOGGER.error(f"Failed to get job status: {response_text}")
    raise click.Abort()


@click.command("job-trigger`")
@click.option(
    "--openshift-ci-token",
    help="Openshift ci token, needed to trigger jobs.",
    default=os.environ.get("OPENSHIFT_CI_TOKEN"),
)
@click.option("--openshift-ci-job-name", help="Openshift ci job name", show_default=True, type=click.STRING)
@click.option(
    "--prow-triggering-job-id",
    help="Prow ID (prowjobid) of the job to be re-triggered. If empty, the job will be triggered immediately.",
    show_default=True,
    type=click.STRING,
)
@click.option(
    "--job-yaml-config-file",
    help="""
    \b
    YAML file with configuration for job triggering.
    See manifests/config.example.yaml for example.
    """,
    type=click.Path(exists=True),
)
@click.option(
    "--pdb",
    help="Drop to `ipdb` shell on exception",
    is_flag=True,
    show_default=True,
)
def main(**kwargs):
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
