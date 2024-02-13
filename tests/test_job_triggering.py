import copy

import pytest
from simple_logger.logger import get_logger

from openshift_ci_job_trigger.libs.job_triggering import JobTriggering
from tests.constants import REQUEST_JSON

LOGGER = get_logger(name=__name__)


@pytest.fixture()
def request_json():
    return copy.deepcopy(REQUEST_JSON)


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


def test_get_triggered_jobs_filepath(request_json):
    filepath = JobTriggering(hook_data=request_json, flask_logger=LOGGER).get_triggered_jobs_filepath()
    assert filepath.exists(), f"File {filepath} does not exist"
