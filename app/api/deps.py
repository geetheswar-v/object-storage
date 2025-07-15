from fastapi import HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.service.db import get_session
from typing import Optional, AsyncGenerator


security = HTTPBearer(auto_error=False)


async def verify_api_key(
    x_api_key: Optional[str] = Header(None, alias="x-api-key"),
    authorization: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> bool:
    """Verify API key from header or authorization"""
    api_key = None
    
    # Check x-api-key header first
    if x_api_key:
        api_key = x_api_key
    # Check authorization header
    elif authorization:
        api_key = authorization.credentials
    
    if not api_key or api_key != settings.api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key"
        )
    
    return True


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency"""
    async for session in get_session():
        yield session