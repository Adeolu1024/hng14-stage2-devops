import pytest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))

from main import app


@pytest.fixture
def mock_redis():
    with patch("main.get_redis") as mock:
        redis_instance = MagicMock()
        mock.return_value = redis_instance
        yield redis_instance


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    return TestClient(app)


def test_create_job(mock_redis, client):
    mock_redis.lpush.return_value = 1
    mock_redis.hset.return_value = 1

    response = client.post("/jobs")

    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "queued"
    mock_redis.lpush.assert_called_once()
    mock_redis.hset.assert_called_once()


def test_get_job_exists(mock_redis, client):
    mock_redis.hgetall.return_value = {b"status": b"completed", b"job_id": b"test-123"}

    response = client.get("/jobs/test-123")

    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == "test-123"
    assert data["status"] == "completed"


def test_get_job_not_found(mock_redis, client):
    mock_redis.hgetall.return_value = {}

    response = client.get("/jobs/nonexistent")

    assert response.status_code == 200
    data = response.json()
    assert "error" in data
    assert data["error"] == "not found"


def test_health_check_ok(mock_redis, client):
    mock_redis.ping.return_value = True

    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_health_check_redis_down(mock_redis, client):
    import redis as redis_lib
    mock_redis.ping.side_effect = redis_lib.ConnectionError("Connection refused")

    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
