from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core import database
from app.core.auth_cookies import SESSION_COOKIE_NAME, enforce_csrf
from app.core.security import decode_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    request: Request,
    bearer_token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    cookie_token = request.cookies.get(SESSION_COOKIE_NAME)
    if bearer_token:
        # Explicit bearer clients keep working without browser-only CSRF rules.
        token = bearer_token
    elif cookie_token:
        enforce_csrf(request)
        token = cookie_token
    else:
        token = None
    subject = decode_token(token) if token else None
    if subject is None:
        raise credentials_exception
    user = db.query(User).filter(User.id == subject).first()
    if user is None:
        # Fallback: token subject may be email (backwards compat)
        user = db.query(User).filter(User.email == subject).first()
    if user is None:
        raise credentials_exception
    return user
