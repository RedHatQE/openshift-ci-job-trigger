import pytest
import xmltodict


@pytest.fixture(scope="session")
def get_junit_file(filepath):
    with open(filepath) as fd:
        return xmltodict.parse(fd.read())
