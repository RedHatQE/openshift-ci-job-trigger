import json
import os
from json import JSONDecodeError

import requests
import xmltodict
import yaml
from timeout_sampler import TimeoutSampler


class JobTriggering:
    def __init__(self, hook_data, flask_logger):
        self.logger = flask_logger

        self.hook_data = hook_data
        self.token = self.hook_data.get("token")
        self.build_id = self.hook_data.get("build_id")
        self.job_name = self.hook_data.get("job_name")
        self.prow_job_id = self.hook_data.get("prow_job_id")
        self.verify_hook_data()

        self.gangway_api_url = "https://gangway-ci.apps.ci.l2s4.p1.openshiftapps.com/v1/executions/"
        self.triggered_jobs_filepath = os.path.join("/tmp", "openshift_ci_triggered_jobs.json")
        self.authorization_header = {"Authorization": f"Bearer {self.token}"}

    def verify_hook_data(self):
        if not self.token:
            self.logger.error("openshift ci token is mandatory.")

        if not self.job_name:
            self.logger.error("openshift ci job name is mandatory.")

        if not self.build_id:
            self.logger.error("openshift ci build id is mandatory.")

        if not self.prow_job_id:
            self.logger.error("openshift ci prow job id is mandatory.")

        if not all((self.token, self.job_name, self.build_id, self.prow_job_id)):
            raise ValueError("Missing parameters")

    def execute(self):
        if self.prow_job_id in self.read_job_triggering_file().get(self.job_name, []):
            self.logger.warning(
                f"Job {self.job_name} with prow job id {self.prow_job_id} was already auto-triggered. Exiting."
            )
            return

        self.wait_for_job_completed()

        tests_dict = self.get_tests_from_junit_operator_by_build_id()
        if self.is_build_failed_on_setup(tests_dict=tests_dict):
            self.trigger_job()

    def get_prow_job_status(self):
        response = requests.get(
            url=f"{self.gangway_api_url}{self.prow_job_id}",
            headers=self.authorization_header,
        )

        return yaml.safe_load(response.text).get("job_status")

    def wait_for_job_completed(self):
        self.logger.info(f"Waiting for build {self.prow_job_id} to end.")
        current_job_status = None
        for job_status in TimeoutSampler(
            wait_timeout=600,
            sleep=60,
            print_log=False,
            func=self.get_prow_job_status,
        ):
            if job_status:
                if job_status != "PENDING":
                    return
                if current_job_status != job_status:
                    current_job_status = job_status
                    self.logger.info(f"Job status: {current_job_status}")

    def save_job_data_to_file(self, prow_job_id):
        data = self.read_job_triggering_file()

        with open(self.triggered_jobs_filepath, "w") as fd_write:
            new_data = data.setdefault(self.job_name, []).append(prow_job_id)
            data.update(new_data)
            fd_write.write(json.dumps(data))

    def read_job_triggering_file(self):
        with open(self.triggered_jobs_filepath) as fd_read:
            try:
                data = json.loads(fd_read.read())
            except JSONDecodeError:
                data = {}
        return data

    def trigger_job(self):
        response = requests.post(
            url=f"{self.gangway_api_url}{self.job_name}",
            headers=self.authorization_header,
            json={"job_execution_type": "1"},
        )

        if not response.ok:
            self.logger.error(f"Failed to get job status: {response.headers['grpc-message']}")

        prow_job_id = json.loads(response.content.decode())["id"]
        self.logger.success(f"Successfully triggered job {self.job_name}, prow job id: {prow_job_id}")
        self.save_job_data_to_file(prow_job_id=prow_job_id)

    def get_tests_from_junit_operator_by_build_id(self):
        response = requests.get(
            "https://gcsweb-ci.apps.ci.l2s4.p1.openshiftapps.com/gcs/test-platform-results/logs/"
            f"{self.job_name}/{self.build_id}/artifacts/junit_operator.xml"
        )
        return xmltodict.parse(response.text)["testsuites"]["testsuite"]["testcase"]

    @staticmethod
    def is_build_failed_on_setup(tests_dict):
        for test in tests_dict:
            if test.get("failure") and test["@name"] == "Run multi-stage test pre phase":
                return True

        return False
