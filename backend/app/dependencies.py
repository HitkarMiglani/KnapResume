from collections.abc import Generator
from datetime import UTC, datetime

from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session as DbSession

from app.database import get_db
from app.models import Session as SessionModel
from app.models import User
from app.security import csrf_tokens_match, hash_session_token

SESSION_COOKIE_NAME = "session_id"
CSRF_HEADER_NAME = "x-csrf-token"


def get_current_session(
    session_id: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    db: DbSession = Depends(get_db),
) -> Generator[SessionModel]:
    if session_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "not authenticated")

    token_hash = hash_session_token(session_id)
    record = db.query(SessionModel).filter(SessionModel.token_hash == token_hash).first()

    if record is not None:
        expires_at = record.expires_at
        # Postgres returns naive datetimes for "timestamp without time zone"; the
        # column always stores UTC, so a naive value is interpreted as UTC as-is.
        expires_at = expires_at.replace(tzinfo=UTC) if expires_at.tzinfo is None else expires_at

    if record is None or expires_at < datetime.now(UTC):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "not authenticated")

    yield record


def get_current_user(
    session: SessionModel = Depends(get_current_session),
    db: DbSession = Depends(get_db),
) -> User:
    user = db.get(User, session.user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "not authenticated")
    return user


def require_csrf(
    session: SessionModel = Depends(get_current_session),
    x_csrf_token: str | None = Header(default=None, alias=CSRF_HEADER_NAME),
) -> None:
    if not csrf_tokens_match(session.csrf_token, x_csrf_token):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "csrf token missing or invalid")
