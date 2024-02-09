import os

import click
from simple_logger.logger import get_logger


@click.option(
    "--openshift-ci-token",
    help="Openshift ci token, needed to trigger jobs.",
    default=os.environ.get("OPENSHIFT_CI_TOKEN"),
)
@click.option("--openshift-ci-job-name", help="Openshift ci job name", show_default=True, type=click.STRING)
@click.option(
    "--triggering-job-id",
    help="ID of the job to be re-triggered. If empty, the job will be triggered immediately.",
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
    kwargs.pop("pdb", None)


if __name__ == "__main__":
    should_raise = False
    _logger = get_logger(name="openshift-ci-job-trigger")
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
