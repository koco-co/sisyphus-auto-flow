import pytest
import requests


@pytest.fixture
def api_client():
    session = requests.Session()
    session.headers.update({"Authorization": "Bearer test"})
    return session
