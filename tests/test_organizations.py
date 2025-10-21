from types import SimpleNamespace
from unittest.mock import AsyncMock

import orjson


def make_building(building_id=10):
    return SimpleNamespace(
        id=building_id,
        address=f"addr {building_id}",
        latitude=1.1,
        longitude=2.2,
    )


def make_activity(activity_id=5, name=None):
    return SimpleNamespace(
        id=activity_id,
        name=name or f"activity {activity_id}",
        parent_id=None,
        level=1,
    )


def make_phone(phone_id=7, org_id=1):
    return SimpleNamespace(
        id=phone_id,
        number=f"+100000{phone_id}",
        organization_id=org_id,
    )


def make_org(org_id=1, building_id=10):
    building = make_building(building_id)
    return SimpleNamespace(
        id=org_id,
        name=f"Org {org_id}",
        building_id=building_id,
        building=building,
        phones=[make_phone(org_id=org_id)],
        activities=[make_activity()],
    )


def test_get_organizations_by_building_uses_cache(monkeypatch, test_app, test_headers):
    cached = [{"id": 1, "name": "Org 1", "building_id": 10}]

    async def fake_get_cache(client, key):
        return orjson.dumps(cached)

    async def fake_set_cache(*args, **kwargs):
        raise AssertionError("set_cache should not be called")

    class RepoStub:
        def __init__(self, session):
            raise AssertionError("repository should not be instantiated")

    monkeypatch.setattr("api.organizations.get_cache", fake_get_cache)
    monkeypatch.setattr("api.organizations.set_cache", fake_set_cache)
    monkeypatch.setattr("api.organizations.CrudRepository", RepoStub)

    response = test_app.get(
        "/organizations/by-building/10",
        headers=test_headers,
    )
    assert response.status_code == 200
    assert response.json() == cached


def test_get_organizations_by_building_success(monkeypatch, test_app, test_headers):
    building = make_building(3)
    organizations = [
        SimpleNamespace(id=1, name="Org 1", building_id=building.id),
        SimpleNamespace(id=2, name="Org 2", building_id=building.id),
    ]

    async def fake_get_cache(client, key):
        return None

    cache_spy = AsyncMock(return_value=True)

    class RepoStub:
        def __init__(self, session):
            self.session = session

        async def get_building_by_id(self, building_id):
            return building

        async def get_organizations_by_building(
            self, building_id, limit=None, offset=None
        ):
            assert building_id == building.id
            assert limit == 5
            assert offset == 2
            return organizations

    monkeypatch.setattr("api.organizations.get_cache", fake_get_cache)
    monkeypatch.setattr("api.organizations.set_cache", cache_spy)
    monkeypatch.setattr("api.organizations.CrudRepository", RepoStub)

    response = test_app.get(
        f"/organizations/by-building/{building.id}",
        headers=test_headers,
        params={"limit": 5, "offset": 2},
    )
    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "name": "Org 1", "building_id": building.id},
        {"id": 2, "name": "Org 2", "building_id": building.id},
    ]
    assert cache_spy.await_count == 1
    assert cache_spy.await_args.kwargs["ttl"] == 300


def test_get_organizations_by_building_not_found(monkeypatch, test_app, test_headers):
    async def fake_get_cache(client, key):
        return None

    cache_spy = AsyncMock()

    class RepoStub:
        def __init__(self, session):
            self.session = session

        async def get_building_by_id(self, building_id):
            return None

        async def get_organizations_by_building(self, *args, **kwargs):
            raise AssertionError("should not fetch organizations")

    monkeypatch.setattr("api.organizations.get_cache", fake_get_cache)
    monkeypatch.setattr("api.organizations.set_cache", cache_spy)
    monkeypatch.setattr("api.organizations.CrudRepository", RepoStub)

    response = test_app.get(
        "/organizations/by-building/999",
        headers=test_headers,
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Building not found"}
    assert cache_spy.await_count == 0


def test_get_organizations_by_activity_success(monkeypatch, test_app, test_headers):
    activity = make_activity(11, "Consulting")
    organizations = [
        SimpleNamespace(id=1, name="Org A", building_id=4),
    ]

    async def fake_get_cache(client, key):
        return None

    cache_spy = AsyncMock(return_value=True)

    class RepoStub:
        def __init__(self, session):
            self.session = session

        async def get_activity_by_id(self, activity_id):
            assert activity_id == activity.id
            return activity

        async def get_organizations_by_activity(
            self, activity_id, limit=None, offset=None
        ):
            assert activity_id == activity.id
            assert limit == 10
            assert offset == 0
            return organizations

    monkeypatch.setattr("api.organizations.get_cache", fake_get_cache)
    monkeypatch.setattr("api.organizations.set_cache", cache_spy)
    monkeypatch.setattr("api.organizations.CrudRepository", RepoStub)

    response = test_app.get(
        f"/organizations/by-activity/{activity.id}",
        headers=test_headers,
        params={"limit": 10, "offset": 0},
    )
    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "name": "Org A", "building_id": 4},
    ]
    assert cache_spy.await_count == 1
    assert cache_spy.await_args.kwargs["ttl"] == 300


def test_get_organizations_by_activity_not_found(monkeypatch, test_app, test_headers):
    async def fake_get_cache(client, key):
        return None

    cache_spy = AsyncMock()

    class RepoStub:
        def __init__(self, session):
            self.session = session

        async def get_activity_by_id(self, activity_id):
            return None

        async def get_organizations_by_activity(self, *args, **kwargs):
            raise AssertionError("should not fetch organizations")

    monkeypatch.setattr("api.organizations.get_cache", fake_get_cache)
    monkeypatch.setattr("api.organizations.set_cache", cache_spy)
    monkeypatch.setattr("api.organizations.CrudRepository", RepoStub)

    response = test_app.get(
        "/organizations/by-activity/55",
        headers=test_headers,
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert cache_spy.await_count == 0


def test_get_organizations_by_location_radius(monkeypatch, test_app, test_headers):
    organizations = [
        SimpleNamespace(id=1, name="Org R", building_id=2),
    ]

    async def fake_get_cache(client, key):
        return None

    cache_spy = AsyncMock(return_value=True)

    class RepoStub:
        def __init__(self, session):
            self.session = session

        async def get_organizations_by_radius(
            self, latitude, longitude, radius_meters, limit=None, offset=None
        ):
            assert latitude == 10.0
            assert longitude == 20.0
            assert radius_meters == 1000.0
            assert limit == 1
            assert offset == 0
            return organizations

        async def get_organizations_by_area(self, *args, **kwargs):
            raise AssertionError("area path should not be used")

    monkeypatch.setattr("api.organizations.get_cache", fake_get_cache)
    monkeypatch.setattr("api.organizations.set_cache", cache_spy)
    monkeypatch.setattr("api.organizations.CrudRepository", RepoStub)

    response = test_app.get(
        "/organizations/by-location",
        headers=test_headers,
        params={
            "latitude": 10.0,
            "longitude": 20.0,
            "radius": 1000,
            "limit": 1,
            "offset": 0,
        },
    )
    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "name": "Org R", "building_id": 2},
    ]
    assert cache_spy.await_count == 1
    assert cache_spy.await_args.kwargs["ttl"] == 300


def test_get_organizations_by_location_area(monkeypatch, test_app, test_headers):
    async def fake_get_cache(client, key):
        return None

    async def fake_set_cache(*args, **kwargs):
        raise AssertionError("set_cache should not be called")

    class RepoStub:
        def __init__(self, session):
            self.session = session

        async def get_organizations_by_area(
            self, min_latitude, max_latitude, min_longitude, max_longitude
        ):
            assert min_latitude == 9.0
            assert max_latitude == 11.0
            assert min_longitude == 19.0
            assert max_longitude == 21.0
            return [{"id": 1, "name": "Org A", "building_id": 2}]

        async def get_organizations_by_radius(self, *args, **kwargs):
            raise AssertionError("radius path should not be used")

    monkeypatch.setattr("api.organizations.get_cache", fake_get_cache)
    monkeypatch.setattr("api.organizations.set_cache", fake_set_cache)
    monkeypatch.setattr("api.organizations.CrudRepository", RepoStub)

    response = test_app.get(
        "/organizations/by-location",
        headers=test_headers,
        params={
            "latitude": 10.0,
            "longitude": 20.0,
            "min_lat": 9.0,
            "max_lat": 11.0,
            "min_lon": 19.0,
            "max_lon": 21.0,
        },
    )
    assert response.status_code == 200
    assert response.json() == [{"id": 1, "name": "Org A", "building_id": 2}]


def test_get_organizations_by_location_missing_params(
    monkeypatch, test_app, test_headers
):
    async def fake_get_cache(client, key):
        return None

    cache_spy = AsyncMock()

    class RepoStub:
        def __init__(self, session):
            self.session = session

    monkeypatch.setattr("api.organizations.get_cache", fake_get_cache)
    monkeypatch.setattr("api.organizations.set_cache", cache_spy)
    monkeypatch.setattr("api.organizations.CrudRepository", RepoStub)

    response = test_app.get(
        "/organizations/by-location",
        headers=test_headers,
        params={
            "latitude": 10.0,
            "longitude": 20.0,
        },
    )
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Please provide either 'radius' or all rectangle parameters (min_lat, max_lat, min_lon, max_lon)"
    }
    assert cache_spy.await_count == 0


def test_get_organization_by_id_success(monkeypatch, test_app, test_headers):
    organization = make_org(42, 7)

    async def fake_get_cache(client, key):
        return None

    cache_spy = AsyncMock(return_value=True)

    class RepoStub:
        def __init__(self, session):
            self.session = session

        async def get_organization_by_id(self, organization_id):
            assert organization_id == organization.id
            return organization

    monkeypatch.setattr("api.organizations.get_cache", fake_get_cache)
    monkeypatch.setattr("api.organizations.set_cache", cache_spy)
    monkeypatch.setattr("api.organizations.CrudRepository", RepoStub)

    response = test_app.get(
        f"/organizations/{organization.id}",
        headers=test_headers,
    )
    assert response.status_code == 200
    assert response.json() == {
        "id": organization.id,
        "name": organization.name,
        "building_id": organization.building_id,
        "building": {
            "id": organization.building.id,
            "address": organization.building.address,
            "latitude": organization.building.latitude,
            "longitude": organization.building.longitude,
        },
        "phones": [
            {
                "id": organization.phones[0].id,
                "number": organization.phones[0].number,
                "organization_id": organization.phones[0].organization_id,
            }
        ],
        "activities": [
            {
                "id": organization.activities[0].id,
                "name": organization.activities[0].name,
                "parent_id": organization.activities[0].parent_id,
                "level": organization.activities[0].level,
            }
        ],
    }
    assert cache_spy.await_args.kwargs["ttl"] == 180


def test_get_organization_by_id_not_found(monkeypatch, test_app, test_headers):
    async def fake_get_cache(client, key):
        return None

    cache_spy = AsyncMock()

    class RepoStub:
        def __init__(self, session):
            self.session = session

        async def get_organization_by_id(self, organization_id):
            return None

    monkeypatch.setattr("api.organizations.get_cache", fake_get_cache)
    monkeypatch.setattr("api.organizations.set_cache", cache_spy)
    monkeypatch.setattr("api.organizations.CrudRepository", RepoStub)

    response = test_app.get(
        "/organizations/9999",
        headers=test_headers,
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Organization not found"}
    assert cache_spy.await_count == 0


def test_search_organizations_by_name(monkeypatch, test_app, test_headers):
    class RepoStub:
        def __init__(self, session):
            self.session = session

        async def get_organization_by_name(self, name):
            assert name == "Target"
            return [{"id": 1, "name": "Target", "building_id": 3}]

    monkeypatch.setattr("api.organizations.CrudRepository", RepoStub)

    response = test_app.get(
        "/organizations/search/by-name",
        headers=test_headers,
        params={"name": "Target"},
    )
    assert response.status_code == 200
    assert response.json() == [{"id": 1, "name": "Target", "building_id": 3}]


def test_list_all_organizations(monkeypatch, test_app, test_headers):
    organizations = [
        SimpleNamespace(id=1, name="Org 1", building_id=1),
        SimpleNamespace(id=2, name="Org 2", building_id=2),
    ]

    async def fake_get_cache(client, key):
        return None

    cache_spy = AsyncMock(return_value=True)

    class RepoStub:
        def __init__(self, session):
            self.session = session

        async def get_all_organizations(self, limit=None, offset=None):
            assert limit == 2
            assert offset == 1
            return organizations

    monkeypatch.setattr("api.organizations.get_cache", fake_get_cache)
    monkeypatch.setattr("api.organizations.set_cache", cache_spy)
    monkeypatch.setattr("api.organizations.CrudRepository", RepoStub)

    response = test_app.get(
        "/organizations/",
        headers=test_headers,
        params={"limit": 2, "offset": 1},
    )
    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "name": "Org 1", "building_id": 1},
        {"id": 2, "name": "Org 2", "building_id": 2},
    ]
    assert cache_spy.await_args.kwargs["ttl"] == 180


def test_get_activity_ids(monkeypatch, test_app, test_headers):
    activities = [
        {
            "id": 1,
            "name": "Consulting",
            "parent_id": None,
            "level": 1,
        },
        {
            "id": 2,
            "name": "Support",
            "parent_id": None,
            "level": 1,
        },
    ]

    async def fake_get_cache(client, key):
        return None

    cache_spy = AsyncMock(return_value=True)

    class RepoStub:
        def __init__(self, session):
            self.session = session

        async def get_activity_ids(self, limit=None, offset=None):
            assert limit == 5
            assert offset == 0
            return activities

    monkeypatch.setattr("api.organizations.get_cache", fake_get_cache)
    monkeypatch.setattr("api.organizations.set_cache", cache_spy)
    monkeypatch.setattr("api.organizations.CrudRepository", RepoStub)

    response = test_app.get(
        "/organizations/activities/all",
        headers=test_headers,
        params={"limit": 5, "offset": 0},
    )
    assert response.status_code == 200
    assert response.json() == activities
    assert cache_spy.await_args.kwargs["ttl"] == 600


def test_protected_endpoint_requires_valid_api_key(test_app):
    response = test_app.get("/buildings/", headers={"X-API-KEY": "wrong"})
    assert response.status_code == 401
    assert response.json() == {"detail": "invalid API key"}
