import pytest
from simple_logger.logger import get_logger

from openshift_ci_job_trigger.libs.job_triggering import JobTriggering

LOGGER = get_logger(name=__name__)


@pytest.fixture()
def request_json():
    return {"job_name": "periodic-test-job", "build_id": "1", "prow_job_id": "123456", "token": "token"}


@pytest.mark.parametrize("param", ["job_name", "build_id", "prow_job_id", "token"])
def test_verify_job_trigger_mandatory_params(request_json, param):
    request_json.pop(param)

    with pytest.raises(ValueError):
        JobTriggering(hook_data=request_json, flask_logger=LOGGER)


def test_already_triggered(request_json):
    job_trigger = JobTriggering(
        hook_data=request_json,
        flask_logger=LOGGER,
        triggered_jobs_filepath="tests/manifests/openshift_ci_triggered_jobs.json",
    )
    assert not job_trigger.execute(), "Job was triggered but it should not"
