import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

SECTIONS = ("experience", "project", "education", "skill")


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(unique=True, nullable=False)
    csrf_token: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    expires_at: Mapped[datetime] = mapped_column(nullable=False)


class SourceFact(Base):
    __tablename__ = "source_facts"
    __table_args__ = (CheckConstraint(f"section IN {SECTIONS}", name="ck_source_facts_section"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    section: Mapped[str] = mapped_column(nullable=False)
    raw_text: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))

    bullet: Mapped["Bullet"] = relationship(back_populates="source_fact", uselist=False)


class Bullet(Base):
    __tablename__ = "bullets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    source_fact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("source_facts.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    normalized_text: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))

    source_fact: Mapped[SourceFact] = relationship(back_populates="bullet")
