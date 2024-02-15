import copy

import pytest
from simple_logger.logger import get_logger

from openshift_ci_job_trigger.libs.job_db import DB
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
    with DB() as database:
        assert not database.check_prow_job_id_in_db(
            job_name="periodic-ci-CSPI-QE-MSI-openshift-ci-trigger-poc-test-fail-setup",
            prow_job_id="2Q9mghKLbecrCkxNZuJZkQ",
        ), "Job exist in DB"
