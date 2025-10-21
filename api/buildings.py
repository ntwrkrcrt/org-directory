from typing import Any, Optional, Sequence

import orjson
from fastapi import APIRouter, Depends, Query, Request
from loguru import logger
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import handle_api_key
from core.cache.redis import get_redis_client
from core.cache.utils import build_get_query_cache_key, get_cache, set_cache
from core.repository.repository import CrudRepository
from models import Building, get_session
from schemas.building import BuildingResponse

router = APIRouter(
    prefix="/buildings",
    tags=["buildings"],
    dependencies=[Depends(handle_api_key)],
)


@router.get("/", response_model=list[BuildingResponse])
async def list_buildings(
    request: Request,
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_redis_client),
    limit: Optional[int] = Query(None, description="Query limit"),
    offset: Optional[int] = Query(None, description="Query offset"),
):
    cache_key: str = build_get_query_cache_key(prefix="buildings", url=request.url)

    try:
        cached: Optional[str] = await get_cache(client=cache, key=cache_key)
        if cached:
            return orjson.loads(cached)
    except Exception as e:
        logger.warning(f"Cache get failed for {cache_key}: {e}")

    repository = CrudRepository(session)
    result: Sequence[Building] = await repository.get_all_buildings(
        limit=limit, offset=offset
    )

    response: list[dict[str, Any]] = [
        BuildingResponse.model_validate(i).model_dump() for i in result
    ]

    try:
        await set_cache(
            client=cache, key=cache_key, value=orjson.dumps(response), ttl=180
        )
    except Exception as e:
        logger.warning(f"Cache set failed for {cache_key}: {e}")

    return response


@router.get("/{building_id}", response_model=BuildingResponse)
async def get_building_by_id(
    request: Request,
    building_id: int,
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_redis_client),
):
    cache_key: str = build_get_query_cache_key(prefix="building_id", url=request.url)

    try:
        cached: Optional[str] = await get_cache(client=cache, key=cache_key)
        if cached:
            return orjson.loads(cached)
    except Exception as e:
        logger.warning(f"Cache get failed for {cache_key}: {e}")

    repository = CrudRepository(session)
    result: Optional[Building] = await repository.get_building_by_id(
        building_id=building_id
    )
    response: dict[str, Any] = BuildingResponse.model_validate(result).model_dump()

    try:
        await set_cache(
            client=cache, key=cache_key, value=orjson.dumps(response), ttl=180
        )
    except Exception as e:
        logger.warning(f"Cache set failed for {cache_key}: {e}")

    return response


@router.get("/search/by-address", response_model=BuildingResponse)
async def get_building_by_address(
    request: Request,
    address: str,
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_redis_client),
):
    cache_key: str = build_get_query_cache_key(
        prefix="building_address", url=request.url
    )

    try:
        cached: Optional[str] = await get_cache(client=cache, key=cache_key)
        if cached:
            return orjson.loads(cached)
    except Exception as e:
        logger.warning(f"Cache get failed for {cache_key}: {e}")

    repository = CrudRepository(session)
    result: Optional[Building] = await repository.get_building_by_address(address)

    response: dict[str, Any] = BuildingResponse.model_validate(result).model_dump()

    try:
        await set_cache(
            client=cache, key=cache_key, value=orjson.dumps(response), ttl=180
        )
    except Exception as e:
        logger.warning(f"Cache set failed for {cache_key}: {e}")

    return response
