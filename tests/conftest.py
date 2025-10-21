from pathlib import Path

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

from config import settings
from core.cache.redis import get_redis_client
from main import app
from models import get_session

test_env_path = Path(__file__).parent.parent / ".env.test"
if test_env_path.exists():
    load_dotenv(test_env_path, override=True)


class DummyRedis:
    def __init__(self):
        self.storage: dict[str, str] = {}

    async def get(self, name: str):
        return self.storage.get(name)

    async def setex(self, name: str, time: int, value: str):
        self.storage[name] = value
        return True

    async def delete(self, name: str):
        self.storage.pop(name, None)


@pytest.fixture(scope="function")
def test_app(monkeypatch):
    async def fake_init_db():
        return None

    async def fake_shutdown_db():
        return None

    async def fake_init_redis():
        return None

    async def fake_shutdown_redis():
        return None

    monkeypatch.setattr("main.init_db", fake_init_db)
    monkeypatch.setattr("main.shutdown_db", fake_shutdown_db)
    monkeypatch.setattr("main.init_redis", fake_init_redis)
    monkeypatch.setattr("main.shutdown_redis", fake_shutdown_redis)

    redis_client = DummyRedis()

    async def override_session():
        yield None

    async def override_redis():
        return redis_client

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_redis_client] = override_redis

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.pop(get_session, None)
    app.dependency_overrides.pop(get_redis_client, None)


@pytest.fixture
def test_headers() -> dict[str, str]:
    return {"X-API-KEY": settings.API_KEY}
