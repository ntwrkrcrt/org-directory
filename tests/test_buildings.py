from types import SimpleNamespace
from unittest.mock import AsyncMock

import orjson


def make_building():
    return SimpleNamespace(id=1, address="addr", latitude=1.1, longitude=2.2)


def test_list_buildings_returns_cached_data(monkeypatch, test_app, test_headers):
    cached = [{"id": 1, "address": "addr", "latitude": 1.1, "longitude": 2.2}]

    async def fake_get_cache(client, key):
        return orjson.dumps(cached)

    async def fake_set_cache(*args, **kwargs):
        raise AssertionError("set_cache should not be called")

    monkeypatch.setattr("api.buildings.get_cache", fake_get_cache)
    monkeypatch.setattr("api.buildings.set_cache", fake_set_cache)

    response = test_app.get("/buildings/", headers=test_headers)
    assert response.status_code == 200
    assert response.json() == cached


def test_list_buildings_fetches_repository(monkeypatch, test_app, test_headers):
    building = make_building()

    async def fake_get_cache(client, key):
        return None

    cache_spy = AsyncMock(return_value=True)

    class RepoStub:
        def __init__(self, session):
            self.session = session

        async def get_all_buildings(self, limit=None, offset=None):
            return [building]

    monkeypatch.setattr("api.buildings.get_cache", fake_get_cache)
    monkeypatch.setattr("api.buildings.set_cache", cache_spy)
    monkeypatch.setattr("api.buildings.CrudRepository", RepoStub)

    response = test_app.get("/buildings/", headers=test_headers, params={"limit": 5})
    assert response.status_code == 200
    assert response.json() == [
        {
            "id": building.id,
            "address": building.address,
            "latitude": building.latitude,
            "longitude": building.longitude,
        }
    ]
    assert cache_spy.await_count == 1
    assert cache_spy.await_args.kwargs["ttl"] == 180
    assert cache_spy.await_args.kwargs["client"] is not None


def test_get_building_by_id_uses_cache(monkeypatch, test_app, test_headers):
    cached = {"id": 7, "address": "cached", "latitude": 3.3, "longitude": 4.4}

    async def fake_get_cache(client, key):
        return orjson.dumps(cached)

    async def fake_set_cache(*args, **kwargs):
        raise AssertionError("set_cache should not be called")

    class RepoStub:
        def __init__(self, session):
            raise AssertionError("repository should not be used")

    monkeypatch.setattr("api.buildings.get_cache", fake_get_cache)
    monkeypatch.setattr("api.buildings.set_cache", fake_set_cache)
    monkeypatch.setattr("api.buildings.CrudRepository", RepoStub)

    response = test_app.get("/buildings/7", headers=test_headers)
    assert response.status_code == 200
    assert response.json() == cached


def test_get_building_by_id_fetches_repository(monkeypatch, test_app, test_headers):
    building = make_building()

    async def fake_get_cache(client, key):
        return None

    cache_spy = AsyncMock(return_value=True)

    class RepoStub:
        def __init__(self, session):
            self.session = session

        async def get_building_by_id(self, building_id):
            assert building_id == building.id
            return building

    monkeypatch.setattr("api.buildings.get_cache", fake_get_cache)
    monkeypatch.setattr("api.buildings.set_cache", cache_spy)
    monkeypatch.setattr("api.buildings.CrudRepository", RepoStub)

    response = test_app.get("/buildings/1", headers=test_headers)
    assert response.status_code == 200
    assert response.json() == {
        "id": building.id,
        "address": building.address,
        "latitude": building.latitude,
        "longitude": building.longitude,
    }
    assert cache_spy.await_count == 1
    assert cache_spy.await_args.kwargs["ttl"] == 180


def test_get_building_by_address_uses_cache(monkeypatch, test_app, test_headers):
    cached = {"id": 5, "address": "cached addr", "latitude": 3.0, "longitude": 4.0}

    async def fake_get_cache(client, key):
        return orjson.dumps(cached)

    async def fake_set_cache(*args, **kwargs):
        raise AssertionError("set_cache should not be called")

    class RepoStub:
        def __init__(self, session):
            raise AssertionError("repository should not be used")

    monkeypatch.setattr("api.buildings.get_cache", fake_get_cache)
    monkeypatch.setattr("api.buildings.set_cache", fake_set_cache)
    monkeypatch.setattr("api.buildings.CrudRepository", RepoStub)

    response = test_app.get(
        "/buildings/search/by-address",
        headers=test_headers,
        params={"address": "cached addr"},
    )
    assert response.status_code == 200
    assert response.json() == cached


def test_get_building_by_address_fetches_repository(
    monkeypatch, test_app, test_headers
):
    building = make_building()

    async def fake_get_cache(client, key):
        return None

    cache_spy = AsyncMock(return_value=True)

    class RepoStub:
        def __init__(self, session):
            self.session = session

        async def get_building_by_address(self, address):
            assert address == building.address
            return building

    monkeypatch.setattr("api.buildings.get_cache", fake_get_cache)
    monkeypatch.setattr("api.buildings.set_cache", cache_spy)
    monkeypatch.setattr("api.buildings.CrudRepository", RepoStub)

    response = test_app.get(
        "/buildings/search/by-address",
        headers=test_headers,
        params={"address": building.address},
    )
    assert response.status_code == 200
    assert response.json() == {
        "id": building.id,
        "address": building.address,
        "latitude": building.latitude,
        "longitude": building.longitude,
    }
    assert cache_spy.await_count == 1
    assert cache_spy.await_args.kwargs["ttl"] == 180
