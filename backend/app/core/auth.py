import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.core.config import Settings


def owner_access(settings: Settings):
    if settings.app_env == "production" and not (settings.owner_username and settings.owner_password):
        raise ValueError("Production requires OWNER_USERNAME and OWNER_PASSWORD")
    if bool(settings.owner_username) != bool(settings.owner_password):
        raise ValueError("Set both OWNER_USERNAME and OWNER_PASSWORD")
    security = HTTPBasic(auto_error=False)

    def require_owner(request: Request, credentials: Annotated[HTTPBasicCredentials | None, Depends(security)]):
        if request.url.path == "/api/v1/health" or not settings.owner_password:
            return
        username = credentials.username if credentials else ""
        password = credentials.password if credentials else ""
        valid_user = secrets.compare_digest(username.encode(), settings.owner_username.encode())
        valid_password = secrets.compare_digest(password.encode(), settings.owner_password.encode())
        if not (valid_user and valid_password):
            raise HTTPException(401, "Sign in required", headers={"WWW-Authenticate": 'Basic realm="AI Mind Clone"'})

    return require_owner
