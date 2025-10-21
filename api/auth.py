from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from config import settings

api_key = APIKeyHeader(name="x-api-key", description="API key")


async def handle_api_key(key: str = Security(api_key)):
    if key == settings.API_KEY:
        return api_key

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid API key"
    )
