import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DbSession

from app.completeness import compute_completeness
from app.database import get_db
from app.dependencies import get_current_user, require_csrf
from app.jd_parsing import AIParsingError, parse_job_description
from app.models import JobDescription, User
from app.schemas import CompletenessResponse, JobDescriptionCreateRequest, JobDescriptionResponse

router = APIRouter(prefix="/api", tags=["job-descriptions"])


@router.post(
    "/job-descriptions",
    response_model=JobDescriptionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_csrf)],
)
def create_job_description(
    body: JobDescriptionCreateRequest,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    try:
        skills, keywords, seniority = parse_job_description(body.raw_text)
    except AIParsingError as exc:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            "job description AI parsing failed"
        ) from exc

    jd = JobDescription(
        user_id=user.id,
        raw_text=body.raw_text,
        skills=skills,
        keywords=keywords,
        seniority=seniority,
    )
    db.add(jd)
    db.commit()
    db.refresh(jd)

    return jd


@router.get("/job-descriptions", response_model=list[JobDescriptionResponse])
def list_job_descriptions(user: User = Depends(get_current_user), db: DbSession = Depends(get_db)):
    return (
        db.query(JobDescription)
        .filter(JobDescription.user_id == user.id)
        .order_by(JobDescription.created_at.desc())
        .all()
    )


@router.get("/job-descriptions/{job_description_id}", response_model=JobDescriptionResponse)
def get_job_description(
    job_description_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    jd = (
        db.query(JobDescription)
        .filter(JobDescription.id == job_description_id, JobDescription.user_id == user.id)
        .first()
    )
    if jd is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "job description not found")
    return jd


@router.delete(
    "/job-descriptions/{job_description_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_csrf)],
)
def delete_job_description(
    job_description_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    jd = (
        db.query(JobDescription)
        .filter(JobDescription.id == job_description_id, JobDescription.user_id == user.id)
        .first()
    )
    if jd is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "job description not found")

    db.delete(jd)
    db.commit()


@router.get("/profile/completeness", response_model=CompletenessResponse)
def get_completeness(user: User = Depends(get_current_user), db: DbSession = Depends(get_db)):
    scores, overall = compute_completeness(db, user.id)
    return CompletenessResponse(**scores, overall=overall)
