import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DbSession

from app.database import get_db
from app.dependencies import get_current_user, require_csrf
from app.models import Bullet, SourceFact, User
from app.normalization import NormalizationError, normalize_fact
from app.schemas import BulletResponse, FactCreateRequest

router = APIRouter(prefix="/api/bullets", tags=["profile"])


@router.post(
    "",
    response_model=BulletResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_csrf)],
)
def create_bullet(
    body: FactCreateRequest,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    try:
        normalized_text = normalize_fact(body.raw_text)
    except NormalizationError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    fact = SourceFact(user_id=user.id, section=body.section, raw_text=body.raw_text)
    db.add(fact)
    db.flush()

    bullet = Bullet(user_id=user.id, source_fact_id=fact.id, normalized_text=normalized_text)
    db.add(bullet)
    db.commit()
    db.refresh(bullet)
    db.refresh(fact)

    return BulletResponse(
        id=bullet.id,
        section=fact.section,
        raw_text=fact.raw_text,
        normalized_text=bullet.normalized_text,
        created_at=bullet.created_at,
    )


@router.get("", response_model=list[BulletResponse])
def list_bullets(user: User = Depends(get_current_user), db: DbSession = Depends(get_db)):
    bullets = (
        db.query(Bullet)
        .filter(Bullet.user_id == user.id)
        .join(SourceFact)
        .order_by(Bullet.created_at.desc())
        .all()
    )
    return [
        BulletResponse(
            id=b.id,
            section=b.source_fact.section,
            raw_text=b.source_fact.raw_text,
            normalized_text=b.normalized_text,
            created_at=b.created_at,
        )
        for b in bullets
    ]


@router.delete(
    "/{bullet_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_csrf)]
)
def delete_bullet(
    bullet_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    bullet = (
        db.query(Bullet).filter(Bullet.id == bullet_id, Bullet.user_id == user.id).first()
    )
    if bullet is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "bullet not found")

    fact = db.get(SourceFact, bullet.source_fact_id)
    db.delete(bullet)
    if fact is not None:
        db.delete(fact)
    db.commit()
