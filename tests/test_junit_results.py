import pytest
import xmltodict

from openshift_ci_job_trigger.libs.job_triggering import JobTriggering
from tests.constants import REQUEST_JSON
from tests.test_job_triggering import LOGGER


@pytest.fixture(scope="class")
def job_trigger():
    return JobTriggering(hook_data=REQUEST_JSON, flask_logger=LOGGER)


def get_junit_file(filepath):
    with open(filepath) as fd:
        return xmltodict.parse(fd.read())


class TestFailedJobXML:
    def test_failed_job_in_pre_phase(self, job_trigger):
        tests_dict = job_trigger.get_testsuites_testcase_from_junit_operator(
            junit_xml=get_junit_file(filepath="tests/manifests/junit_operator_failed_pre_phase.xml")
        )
        assert job_trigger.is_build_failed_on_setup(tests_dict=tests_dict), "Job should fail on pre phase but did not"

    def test_failed_job_in_tests_phase(self, job_trigger):
        tests_dict = job_trigger.get_testsuites_testcase_from_junit_operator(
            junit_xml=get_junit_file(filepath="tests/manifests/junit_operator_failed_test_phase.xml")
        )
        assert not job_trigger.is_build_failed_on_setup(
            tests_dict=tests_dict
        ), "Job should fail on test phase but did not"
