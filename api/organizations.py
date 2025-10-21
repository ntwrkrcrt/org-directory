from typing import Any, Optional, Sequence

import orjson
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from loguru import logger
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import handle_api_key
from core.cache.redis import get_redis_client
from core.cache.utils import build_get_query_cache_key, get_cache, set_cache
from core.repository.repository import CrudRepository
from models import Activity, Building, Organization, get_session
from schemas.organization import (
    ActivityResponse,
    OrganizationListResponse,
    OrganizationResponse,
)

router = APIRouter(
    prefix="/organizations",
    tags=["organizations"],
    dependencies=[Depends(handle_api_key)],
)


@router.get("/by-building/{building_id}", response_model=list[OrganizationListResponse])
async def get_organizations_by_building(
    request: Request,
    building_id: int,
    limit: Optional[int] = Query(None, description="Query limit"),
    offset: Optional[int] = Query(None, description="Query offset"),
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_redis_client),
):
    cache_key: str = build_get_query_cache_key(
        prefix="orgs_by_building", url=request.url
    )

    try:
        cached: Optional[str] = await get_cache(client=cache, key=cache_key)
        if cached:
            return orjson.loads(cached)
    except Exception as e:
        logger.warning(f"Cache get failed for {cache_key}: {e}")

    repository = CrudRepository(session=session)

    building: Optional[Building] = await repository.get_building_by_id(
        building_id,
    )
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")

    result: Sequence[Organization] = await repository.get_organizations_by_building(
        building_id, limit=limit, offset=offset
    )

    response: list[dict[str, Any]] = [
        OrganizationListResponse.model_validate(i).model_dump() for i in result
    ]

    try:
        await set_cache(
            client=cache, key=cache_key, value=orjson.dumps(response), ttl=300
        )
    except Exception as e:
        logger.warning(f"Cache set failed for {cache_key}: {e}")

    return response


@router.get("/by-activity/{activity_id}", response_model=list[OrganizationListResponse])
async def get_organizations_by_activity(
    request: Request,
    activity_id: int,
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_redis_client),
    limit: Optional[int] = Query(None, description="Query limit"),
    offset: Optional[int] = Query(None, description="Query offset"),
):
    cache_key: str = build_get_query_cache_key(
        prefix="orgs_by_activity", url=request.url
    )

    try:
        cached: Optional[str] = await get_cache(client=cache, key=cache_key)
        if cached:
            return orjson.loads(cached)
    except Exception as e:
        logger.warning(f"Cache get failed for {cache_key}: {e}")

    repository = CrudRepository(session=session)

    activity: Optional[Activity] = await repository.get_activity_by_id(activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    result = await repository.get_organizations_by_activity(
        activity_id, limit=limit, offset=offset
    )

    response: list[dict[str, Any]] = [
        OrganizationListResponse.model_validate(i).model_dump() for i in result
    ]

    try:
        await set_cache(
            client=cache, key=cache_key, value=orjson.dumps(response), ttl=300
        )
    except Exception as e:
        logger.warning(f"Cache set failed for {cache_key}: {e}")

    return response


@router.get("/by-location", response_model=list[OrganizationListResponse])
async def get_organizations_by_location(
    request: Request,
    latitude: float = Query(..., description="Center point latitude", ge=-90, le=90),
    longitude: float = Query(
        ..., description="Center point longitude", ge=-180, le=180
    ),
    radius: Optional[float] = Query(None, description="Search radius in meters", gt=0),
    min_lat: Optional[float] = Query(
        None, description="Minimum latitude for rectangle", ge=-90, le=90
    ),
    max_lat: Optional[float] = Query(
        None, description="Maximum latitude for rectangle", ge=-90, le=90
    ),
    min_lon: Optional[float] = Query(
        None, description="Minimum longitude for rectangle", ge=-180, le=180
    ),
    max_lon: Optional[float] = Query(
        None, description="Maximum longitude for rectangle", ge=-180, le=180
    ),
    limit: Optional[int] = Query(None, description="Query limit"),
    offset: Optional[int] = Query(None, description="Query offset"),
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_redis_client),
):
    cache_key: str = build_get_query_cache_key(
        prefix="orgs_by_location", url=request.url
    )

    try:
        cached: Optional[str] = await get_cache(client=cache, key=cache_key)
        if cached:
            return orjson.loads(cached)
    except Exception as e:
        logger.warning(f"Cache get failed for {cache_key}: {e}")

    repository = CrudRepository(session=session)

    if radius is not None:
        result: Sequence[Organization] = await repository.get_organizations_by_radius(
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius,
            limit=limit,
            offset=offset,
        )

        response: list[dict[str, Any]] = [
            OrganizationListResponse.model_validate(i).model_dump() for i in result
        ]

        try:
            await set_cache(
                client=cache, key=cache_key, value=orjson.dumps(response), ttl=300
            )
        except Exception as e:
            logger.warning(f"Cache set failed for {cache_key}: {e}")

        return response

    elif all(
        [
            min_lat is not None,
            max_lat is not None,
            min_lon is not None,
            max_lon is not None,
        ]
    ):
        if min_lat >= max_lat:
            raise HTTPException(
                status_code=400,
                detail="Min latitude should be lower than max latutide",
            )

        if min_lon >= max_lon:
            raise HTTPException(
                status_code=400,
                detail="Min longitude should be lower than max longitude",
            )

        return await repository.get_organizations_by_area(
            min_latitude=min_lat,
            max_latitude=max_lat,
            min_longitude=min_lon,
            max_longitude=max_lon,
        )

    else:
        raise HTTPException(
            status_code=400,
            detail="Please provide either 'radius' or all rectangle parameters (min_lat, max_lat, min_lon, max_lon)",
        )


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization_by_id(
    request: Request,
    organization_id: int,
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_redis_client),
):
    cache_key: str = build_get_query_cache_key(
        prefix="organization_id", url=request.url
    )

    try:
        cached: Optional[str] = await get_cache(client=cache, key=cache_key)
        if cached:
            return orjson.loads(cached)
    except Exception as e:
        logger.warning(f"Cache get failed for {cache_key}: {e}")

    repository = CrudRepository(session=session)

    result: Optional[Organization] = await repository.get_organization_by_id(
        organization_id
    )
    if not result:
        raise HTTPException(status_code=404, detail="Organization not found")

    response: dict[str, Any] = OrganizationResponse.model_validate(result).model_dump()

    try:
        await set_cache(
            client=cache, key=cache_key, value=orjson.dumps(response), ttl=180
        )
    except Exception as e:
        logger.warning(f"Cache set failed for {cache_key}: {e}")

    return response


@router.get("/search/by-name", response_model=list[OrganizationListResponse])
async def search_organizations_by_name(
    name: str = Query(..., description="Organization name to search", min_length=1),
    session: AsyncSession = Depends(get_session),
):
    repository = CrudRepository(session=session)

    return await repository.get_organization_by_name(name)


@router.get("/", response_model=list[OrganizationListResponse])
async def list_all_organizations(
    request: Request,
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_redis_client),
    limit: Optional[int] = Query(None, description="Query limit"),
    offset: Optional[int] = Query(None, description="Query offset"),
):
    cache_key: str = build_get_query_cache_key(prefix="all_orgs", url=request.url)

    try:
        cached: Optional[str] = await get_cache(client=cache, key=cache_key)
        if cached:
            return orjson.loads(cached)
    except Exception as e:
        logger.warning(f"Cache get failed for {cache_key}: {e}")

    repository = CrudRepository(session=session)
    result: Sequence[Organization] = await repository.get_all_organizations(
        limit=limit, offset=offset
    )

    response: list[dict[str, Any]] = [
        OrganizationListResponse.model_validate(i).model_dump() for i in result
    ]

    try:
        await set_cache(
            client=cache, key=cache_key, value=orjson.dumps(response), ttl=180
        )
    except Exception as e:
        logger.warning(f"Cache set failed for {cache_key}: {e}")

    return response


@router.get("/activities/all", response_model=list[ActivityResponse])
async def get_activity_ids(
    request: Request,
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_redis_client),
    limit: Optional[int] = Query(None, description="Query limit"),
    offset: Optional[int] = Query(None, description="Query offset"),
):
    cache_key: str = build_get_query_cache_key(prefix="all_activities", url=request.url)

    try:
        cached: Optional[str] = await get_cache(client=cache, key=cache_key)
        if cached:
            return orjson.loads(cached)
    except Exception as e:
        logger.warning(f"Cache get failed for {cache_key}: {e}")

    repository = CrudRepository(session=session)
    result: list[tuple[Any]] = await repository.get_activity_ids(
        limit=limit, offset=offset
    )

    response: list[dict[str, Any]] = [
        ActivityResponse.model_validate(i).model_dump() for i in result
    ]

    try:
        await set_cache(
            client=cache, key=cache_key, value=orjson.dumps(response), ttl=600
        )
    except Exception as e:
        logger.warning(f"Cache set failed for {cache_key}: {e}")

    return response
