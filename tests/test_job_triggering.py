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


class TestJobTriggering:
    JOB_NAME = "periodic-ci-CSPI-QE-MSI-openshift-ci-trigger-poc-test-fail-setup"
    PROW_JOB_ID = "123456"

    def test_add_job_trigger(self, mocker, get_junit_file, request_json):
        job_triggering = JobTriggering(hook_data=request_json, flask_logger=LOGGER)
        mocker.patch(
            "openshift_ci_job_trigger.libs.job_triggering.JobTriggering.trigger_job",
            return_value=TestJobTriggering.PROW_JOB_ID,
        )
        mocker.patch(
            "openshift_ci_job_trigger.libs.job_triggering.JobTriggering.wait_for_job_completed",
            return_value=True,
        )
        mocker.patch(
            "openshift_ci_job_trigger.libs.job_triggering.JobTriggering.get_tests_from_junit_operator_by_build_id",
            return_value=get_junit_file(filepath="tests/manifests/junit_operator_failed_pre_phase.xml"),
        )

        assert job_triggering.execute_trigger(), "Job should be triggered"

    def test_already_triggered(request_json):
        job_triggering = JobTriggering(hook_data=request_json, flask_logger=LOGGER)
        assert not job_triggering.execute_trigger(), "Job should not be triggered"
