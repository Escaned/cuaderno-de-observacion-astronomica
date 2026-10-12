from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from typing import Optional

from app.core.config import settings


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_api_key(api_key: Optional[str] = Depends(api_key_header)) -> Optional[str]:
    if settings.api_key is None:
        return None
    if api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    return api_key


def require_api_key() -> Optional[str]:
    return Depends(get_api_key)