import copy
import pathlib

import pytest
from simple_logger.logger import get_logger

from openshift_ci_job_trigger.libs.job_triggering import JobTriggering
import xmltodict

LOGGER = get_logger(name=__name__)


@pytest.fixture()
def junit_file(request):
    with open(request.param) as fd:
        return xmltodict.parse(fd.read())


@pytest.fixture()
def hook_data_dict():
    return copy.deepcopy({"job_name": "periodic-test-job", "build_id": "1", "prow_job_id": "123456", "token": "token"})


@pytest.fixture()
def job_triggering(hook_data_dict):
    return JobTriggering(hook_data=hook_data_dict, flask_logger=LOGGER)


@pytest.mark.parametrize("param", ["job_name", "build_id", "prow_job_id", "token"])
def test_verify_job_trigger_mandatory_params(hook_data_dict, param):
    hook_data_dict.pop(param)

    with pytest.raises(ValueError):
        JobTriggering(hook_data=hook_data_dict, flask_logger=LOGGER)


@pytest.mark.parametrize("junit_file", ["tests/manifests/junit_operator_failed_pre_phase.xml"], indirect=True)
def test_failed_job_in_pre_phase(junit_file, job_triggering):
    tests_dict = job_triggering.get_testsuites_testcase_from_junit_operator(junit_xml=junit_file)
    assert job_triggering.is_build_failed_on_setup(tests_dict=tests_dict), "Job should fail on pre phase but did not"


@pytest.mark.parametrize("junit_file", ["tests/manifests/junit_operator_failed_test_phase.xml"], indirect=True)
def test_failed_job_in_tests_phase(junit_file, job_triggering):
    tests_dict = job_triggering.get_testsuites_testcase_from_junit_operator(junit_xml=junit_file)
    assert not job_triggering.is_build_failed_on_setup(
        tests_dict=tests_dict
    ), "Job should fail on test phase but did not"


class TestJobTriggering:
    JOB_NAME = "periodic-ci-CSPI-QE-MSI-openshift-ci-trigger-poc-test-fail-setup"
    PROW_JOB_ID = "123456"

    @pytest.mark.parametrize("junit_file", ["tests/manifests/junit_operator_failed_pre_phase.xml"], indirect=True)
    def test_add_job_trigger(self, tmpdir, mocker, junit_file, job_triggering):
        job_trigger_module_path = "openshift_ci_job_trigger.libs.job_triggering.JobTriggering"
        mocker.patch(
            f"{job_trigger_module_path}.trigger_job",
            return_value=TestJobTriggering.PROW_JOB_ID,
        )
        mocker.patch(
            f"{job_trigger_module_path}.wait_for_job_completed",
            return_value=True,
        )
        mocker.patch(
            f"{job_trigger_module_path}.get_tests_from_junit_operator_by_build_id",
            return_value=junit_file,
        )

        assert job_triggering.execute_trigger(
            job_db_path=pathlib.Path(tmpdir, "job_triggering_test.db")
        ), "Job should be triggered"

    def test_already_triggered(self, hook_data_dict):
        hook_data_dict["prow_job_id"] = TestJobTriggering.PROW_JOB_ID
        job_triggering = JobTriggering(hook_data=hook_data_dict, flask_logger=LOGGER)
        assert not job_triggering.execute_trigger(), "Job should not be triggered"
