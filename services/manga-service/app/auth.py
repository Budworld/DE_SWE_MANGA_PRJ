from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Literal

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings


Role = Literal["admin", "user"]


@dataclass(frozen=True)
class AuthenticatedUser:
    username: str
    role: Role
    expires_at: int


bearer_scheme = HTTPBearer(auto_error=False)


def authenticate_demo_user(username: str, password: str) -> AuthenticatedUser | None:
    settings = get_settings()
    if (
        username == settings.auth_demo_admin_username
        and password == settings.auth_demo_admin_password
    ):
        return AuthenticatedUser(username=username, role="admin", expires_at=0)
    if username == settings.auth_demo_user_username and password == settings.auth_demo_user_password:
        return AuthenticatedUser(username=username, role="user", expires_at=0)
    return None


def create_access_token(user: AuthenticatedUser) -> tuple[str, int]:
    settings = get_settings()
    expires_at = int(time.time()) + settings.auth_token_ttl_seconds
    payload = {"sub": user.username, "role": user.role, "exp": expires_at}
    payload_segment = _encode_json(payload)
    signature = _sign(payload_segment)
    return f"{payload_segment}.{signature}", expires_at


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthenticatedUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return verify_access_token(credentials.credentials)


def require_admin(current_user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return current_user


def verify_access_token(token: str) -> AuthenticatedUser:
    try:
        payload_segment, signature = token.split(".", 1)
    except ValueError as error:
        raise _invalid_token() from error

    expected_signature = _sign(payload_segment)
    if not hmac.compare_digest(signature, expected_signature):
        raise _invalid_token()

    try:
        payload = json.loads(_decode_segment(payload_segment))
    except (ValueError, json.JSONDecodeError) as error:
        raise _invalid_token() from error

    username = payload.get("sub")
    role = payload.get("role")
    expires_at = payload.get("exp")
    if not isinstance(username, str) or role not in {"admin", "user"} or not isinstance(expires_at, int):
        raise _invalid_token()
    if expires_at <= int(time.time()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return AuthenticatedUser(username=username, role=role, expires_at=expires_at)


def _encode_json(payload: dict[str, object]) -> str:
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _decode_segment(segment: str) -> str:
    padding = "=" * (-len(segment) % 4)
    return base64.urlsafe_b64decode(f"{segment}{padding}").decode("utf-8")


def _sign(payload_segment: str) -> str:
    secret = get_settings().auth_token_secret.encode("utf-8")
    digest = hmac.new(secret, payload_segment.encode("ascii"), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def _invalid_token() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid bearer token",
        headers={"WWW-Authenticate": "Bearer"},
    )
