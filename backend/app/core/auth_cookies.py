"""Cookie helpers for browser sessions and their CSRF protection."""

import secrets
from hmac import compare_digest

from fastapi import HTTPException, Request, Response, status

from app.core.config import settings

SESSION_COOKIE_NAME = "freshsense_session"
CSRF_COOKIE_NAME = "freshsense_csrf"
CSRF_HEADER_NAME = "X-CSRF-Token"
_UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _secure_cookie() -> bool:
    return settings.ENVIRONMENT == "production"


def set_session_cookies(response: Response, token: str) -> str:
    """Set an HttpOnly session cookie and return the matching CSRF token."""
    csrf_token = secrets.token_urlsafe(32)
    max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    secure = _secure_cookie()
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=max_age,
        httponly=True,
        secure=secure,
        samesite="strict",
        path="/api/v1",
    )
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        max_age=max_age,
        httponly=False,
        secure=secure,
        samesite="strict",
        path="/",
    )
    return csrf_token


def clear_session_cookies(response: Response) -> None:
    secure = _secure_cookie()
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        httponly=True,
        secure=secure,
        samesite="strict",
        path="/api/v1",
    )
    response.delete_cookie(
        key=CSRF_COOKIE_NAME,
        httponly=False,
        secure=secure,
        samesite="strict",
        path="/",
    )


def enforce_csrf(request: Request) -> None:
    """Require a same-site double-submit token for cookie-authenticated writes."""
    if request.method.upper() not in _UNSAFE_METHODS:
        return
    if not request.cookies.get(SESSION_COOKIE_NAME):
        return
    cookie_token = request.cookies.get(CSRF_COOKIE_NAME, "")
    header_token = request.headers.get(CSRF_HEADER_NAME, "")
    if not cookie_token or not header_token or not compare_digest(cookie_token, header_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token missing or invalid",
        )
