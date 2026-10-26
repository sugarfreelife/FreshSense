from datetime import datetime, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth_cookies import SESSION_COOKIE_NAME, clear_session_cookies, enforce_csrf, set_session_cookies
from app.core.config import settings
from app.core.deps import get_current_user, get_db, oauth2_scheme
from app.core.rate_limit import limit_auth_requests
from app.core.security import access_token_id, create_access_token, decode_token, get_password_hash, verify_password
from app.models.user import RevokedToken, User
from app.utils.time import utcnow_naive
from app.schemas.auth import AuthResponse, Token, UserCreate, UserLogin, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


def _token_expiry(token: str) -> datetime:
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    return datetime.fromtimestamp(payload["exp"], tz=timezone.utc).replace(tzinfo=None)


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(limit_auth_requests)],
)
def register(payload: UserCreate, response: Response, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=payload.email,
        name=payload.name.strip() if payload.name and payload.name.strip() else None,
        hashed_password=get_password_hash(payload.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered") from exc
    db.refresh(user)
    token = create_access_token(subject=user.id)
    set_session_cookies(response, token)
    return AuthResponse(
        access_token=None if settings.ENVIRONMENT == "production" else token,
        user=UserOut.model_validate(user),
    )


@router.post("/login", response_model=AuthResponse, dependencies=[Depends(limit_auth_requests)])
def login(payload: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(subject=user.id)
    set_session_cookies(response, token)
    return AuthResponse(
        access_token=None if settings.ENVIRONMENT == "production" else token,
        user=UserOut.model_validate(user),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    response: Response,
    bearer_token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    cookie_token = request.cookies.get(SESSION_COOKIE_NAME)
    if cookie_token:
        enforce_csrf(request)

    tokens = {token for token in (bearer_token, cookie_token) if token and decode_token(token)}
    now = utcnow_naive()
    pruned = db.query(RevokedToken).filter(RevokedToken.expires_at <= now).delete(synchronize_session=False)
    for token in tokens:
        db.merge(RevokedToken(token_id=access_token_id(token), expires_at=_token_expiry(token)))
    if tokens or pruned:
        db.commit()
    clear_session_cookies(response)


@router.post("/token", response_model=Token, include_in_schema=False, dependencies=[Depends(limit_auth_requests)])
def login_oauth(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return {"access_token": create_access_token(subject=user.id), "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
def me(current: User = Depends(get_current_user)):
    return current
