import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def mock_redis():
    with patch("main.get_redis") as mock:
        redis_instance = MagicMock()
        mock.return_value = redis_instance
        yield redis_instance


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)
