import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models import SECTIONS


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SessionResponse(BaseModel):
    user_id: uuid.UUID
    email: EmailStr
    csrf_token: str


class FactCreateRequest(BaseModel):
    section: str = Field(pattern=f"^({'|'.join(SECTIONS)})$")
    raw_text: str = Field(min_length=1, max_length=2000)


class BulletResponse(BaseModel):
    id: uuid.UUID
    section: str
    raw_text: str
    normalized_text: str
    created_at: datetime

    model_config = {"from_attributes": True}


class JobDescriptionCreateRequest(BaseModel):
    raw_text: str = Field(min_length=1, max_length=20000)


class JobDescriptionResponse(BaseModel):
    id: uuid.UUID
    raw_text: str
    skills: list[str]
    keywords: list[str]
    seniority: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CompletenessResponse(BaseModel):
    experience: float
    project: float
    education: float
    skill: float
    overall: float


class ResumeImportResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    filename: str
    file_type: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ResumeImportDetailResponse(BaseModel):
    id: uuid.UUID
    filename: str
    file_type: str
    status: str
    created_at: datetime
    bullets: list[BulletResponse]

    model_config = {"from_attributes": True}
