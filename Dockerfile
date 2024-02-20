FROM python:3.12
EXPOSE 5000

ENV APP_DIR=/openshift-ci-job-re-trigger

RUN ln -s /usr/bin/python3 /usr/bin/python

RUN python -m pip install --no-cache-dir pip --upgrade \
  && python -m pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock README.md $APP_DIR/
COPY openshift_ci_job_re_trigger $APP_DIR/openshift_ci_job_re_trigger/

WORKDIR $APP_DIR

RUN poetry config cache-dir $APP_DIR \
  && poetry config virtualenvs.in-project true \
  && poetry config installer.max-workers 10 \
  && poetry install

HEALTHCHECK CMD curl --fail http://127.0.0.1:5000/openshift_ci_job_re_trigger/healthcheck || exit 1
ENTRYPOINT ["poetry", "run", "python3", "openshift_ci_job_re_trigger/app.py"]
