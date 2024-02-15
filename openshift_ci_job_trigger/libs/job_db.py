import random
import sqlite3
from pathlib import Path

from timeout_sampler import TimeoutSampler


class DB:
    def __init__(self, job_db_path=None):
        self.db_path = job_db_path or Path("/tmp", "openshift_ci_job_trigger.db")
        self.connection = None
        self.cursor = None

        self.table_name = "jobs"
        self.job_name_column = "job_name"
        self.prow_job_id_column = "prow_job_id"

    def __enter__(self):
        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()
        self.cursor.execute(
            f"CREATE TABLE if not exists {self.table_name}("
            f"{self.job_name_column} TEXT, {self.prow_job_id_column} TEXT)"
        )

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.close()

    def check_prow_job_id_in_db(self, job_name, prow_job_id):
        query = (
            f'SELECT EXISTS(SELECT "{prow_job_id}" FROM {self.table_name} '
            f'WHERE {self.job_name_column} == "{job_name}" '
            f'AND {self.prow_job_id_column} == "{prow_job_id}") LIMIT 1'
        )

        result = self.cursor.execute(query).fetchone()[0]

        return result

    def write(self, job_name, prow_job_id):
        def _insert_to_db(_job_name, _prow_job_id):
            self.cursor.execute(
                f"INSERT INTO {self.table_name} " f"(job_name, prow_job_id) VALUES ('{_job_name}', '{_prow_job_id}')"
            )

        for _ in TimeoutSampler(
            wait_timeout=20,
            sleep=random.randint(1, 5),
            func=_insert_to_db,
            _job_name=job_name,
            _prow_job_id=prow_job_id,
        ):
            return self.connection.commit()
