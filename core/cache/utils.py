import hashlib
from typing import Any, Optional

from redis.asyncio import Redis


async def get_cache(client: Redis, key: str) -> Optional[dict[str, Any]]:
    return await client.get(name=key)


async def set_cache(client: Redis, key: str, value: str, ttl: int) -> bool:
    return await client.setex(name=key, time=ttl, value=value)


async def delete_cache(client: Redis, key: str) -> None:
    await client.delete(key)


def build_get_query_cache_key(prefix: str, url: str) -> str:
    return f"{prefix}:{hashlib.sha256(str(url).encode()).hexdigest()}"
