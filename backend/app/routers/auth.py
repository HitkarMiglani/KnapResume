from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DbSession

from app.config import settings
from app.database import get_db
from app.dependencies import (
    SESSION_COOKIE_NAME,
    get_current_session,
    get_current_user,
    require_csrf,
)
from app.models import Session as SessionModel
from app.models import User
from app.schemas import LoginRequest, RegisterRequest, SessionResponse
from app.security import (
    hash_password,
    hash_session_token,
    new_csrf_token,
    new_session_token,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _start_session(response: Response, db: DbSession, user: User) -> SessionResponse:
    token = new_session_token()
    csrf_token = new_csrf_token()
    expires_at = datetime.now(UTC) + timedelta(hours=settings.session_ttl_hours)

    db.add(
        SessionModel(
            user_id=user.id,
            token_hash=hash_session_token(token),
            csrf_token=csrf_token,
            expires_at=expires_at,
        )
    )
    db.commit()

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,  # loopback HTTP dev only, per ADR 0002/0003
        path="/",
        max_age=settings.session_ttl_hours * 3600,
    )
    return SessionResponse(user_id=user.id, email=user.email, csrf_token=csrf_token)


@router.post("/register", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, response: Response, db: DbSession = Depends(get_db)):
    user = User(email=body.email, password_hash=hash_password(body.password))
    db.add(user)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "email already registered") from exc

    return _start_session(response, db, user)


@router.post("/login", response_model=SessionResponse)
def login(body: LoginRequest, response: Response, db: DbSession = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if user is None or not verify_password(user.password_hash, body.password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid email or password")

    return _start_session(response, db, user)


@router.get("/session", response_model=SessionResponse)
def read_session(
    user: User = Depends(get_current_user),
    session: SessionModel = Depends(get_current_session),
):
    return SessionResponse(user_id=user.id, email=user.email, csrf_token=session.csrf_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_csrf)],
)
def logout(
    response: Response,
    session: SessionModel = Depends(get_current_session),
    db: DbSession = Depends(get_db),
):
    db.delete(session)
    db.commit()
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")


@router.delete(
    "/account",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_csrf)],
)
def delete_account(
    response: Response,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    db.delete(user)  # cascades to sessions, source_facts, bullets, job_descriptions
    db.commit()
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
