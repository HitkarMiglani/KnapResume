import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session as DbSession

from app.database import get_db
from app.dependencies import get_current_user, require_csrf
from app.models import Bullet, ResumeImport, ResumeWorkspace, SourceFact, User
from app.normalization import normalize_fact
from app.resume_parsing import extract_text, parse_resume
from app.schemas import ResumeImportDetailResponse, ResumeImportResponse

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.post(
    "/import",
    response_model=ResumeImportDetailResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_csrf)],
)
def import_profile(
    file: UploadFile = File(...),
    workspace_id: uuid.UUID | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    workspace = None
    if workspace_id is not None:
        workspace = (
            db.query(ResumeWorkspace)
            .filter(ResumeWorkspace.id == workspace_id, ResumeWorkspace.user_id == user.id)
            .first()
        )
        if workspace is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "workspace not found")
    # 1. Read content
    content = file.file.read()

    # 2. Check file size (max 5MB)
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds the 5MB limit.",
        )

    # 3. Check format (only PDF and DOCX matching extensions and media types)
    filename = file.filename or ""
    filename_lower = filename.lower()
    content_type = file.content_type

    is_pdf = filename_lower.endswith(".pdf") and content_type == "application/pdf"
    is_docx = (
        filename_lower.endswith(".docx")
        and content_type
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

    if not (is_pdf or is_docx):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only PDF and DOCX are allowed.",
        )

    # 4. Save ResumeImport in database with status='processing'
    file_type = "pdf" if is_pdf else "docx"
    import_obj = ResumeImport(
        user_id=user.id,
        workspace_id=workspace_id,
        filename=filename,
        file_type=file_type,
        status="processing",
    )
    db.add(import_obj)
    db.commit()
    db.refresh(import_obj)

    try:
        # Extract text and parse
        raw_text = extract_text(content, filename)
        parsed_facts = parse_resume(raw_text)

        # Process facts and bullets
        for item in parsed_facts:
            section = item.get("section")
            raw_text_item = item.get("raw_text")
            if not section or not raw_text_item:
                continue

            try:
                normalized_text = normalize_fact(raw_text_item)
            except Exception:
                # Log/safely ignore normalization failures for this entry and continue
                continue

            fact = SourceFact(
                user_id=user.id,
                section=section,
                raw_text=raw_text_item,
                import_id=import_obj.id,
            )
            db.add(fact)
            db.flush()

            bullet = Bullet(
                user_id=user.id,
                source_fact_id=fact.id,
                normalized_text=normalized_text,
            )
            db.add(bullet)

        import_obj.status = "completed"
        db.commit()
        db.refresh(import_obj)

    except Exception as exc:
        db.rollback()
        # Update import to failed
        import_obj.status = "failed"
        db.add(import_obj)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Resume processing failed: {str(exc)}",
        ) from exc

    return import_obj


@router.get("/imports", response_model=list[ResumeImportResponse])
def list_imports(
    workspace_id: uuid.UUID | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    query = db.query(ResumeImport).filter(ResumeImport.user_id == user.id)
    if workspace_id is not None:
        query = query.filter(ResumeImport.workspace_id == workspace_id)
    return (
        query
        .order_by(ResumeImport.created_at.desc())
        .all()
    )


@router.delete(
    "/imports/{import_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_csrf)],
)
def delete_import(
    import_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    import_obj = (
        db.query(ResumeImport)
        .filter(ResumeImport.id == import_id, ResumeImport.user_id == user.id)
        .first()
    )
    if import_obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume import not found or access denied.",
        )

    db.delete(import_obj)
    db.commit()
