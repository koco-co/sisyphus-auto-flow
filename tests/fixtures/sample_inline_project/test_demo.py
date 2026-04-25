import pytest
import requests


class TestDemo:
    def test_get_users(self, api_client):
        resp = requests.get("http://example.com/api/v1/users")
        assert resp.status_code == 200
        assert resp.json()["code"] == 0

    def test_create_user(self, api_client):
        resp = requests.post("http://example.com/api/v1/users", json={"name": "test"})
        assert resp.json().get("id") is not None
