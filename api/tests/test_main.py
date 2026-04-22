import os
import sys
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

# Ensure the `api` package path is importable when pytest's root differs.
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import app


client = TestClient(app)


def test_create_job():
    with patch("main.r") as mock_redis:
        mock_redis.lpush = MagicMock()
        mock_redis.hset = MagicMock()

        resp = client.post("/jobs")
        assert resp.status_code == 200
        body = resp.json()
        assert "job_id" in body
        mock_redis.lpush.assert_called()
        mock_redis.hset.assert_called()


def test_get_job_status():
    with patch("main.r") as mock_redis:
        mock_redis.hget = MagicMock(return_value="queued")

        resp = client.get("/jobs/test-job-id")
        assert resp.status_code == 200
        body = resp.json()
        assert body["job_id"] == "test-job-id"
        assert body["status"] == "queued"


def test_invalid_job_id_returns_404():
    with patch("main.r") as mock_redis:
        mock_redis.hget = MagicMock(return_value=None)

        resp = client.get("/jobs/does-not-exist")
        assert resp.status_code == 404
        body = resp.json()
        assert "error" in body
