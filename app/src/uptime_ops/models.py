from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Target(Base):
    __tablename__ = "targets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False, unique=True)
    last_status: Mapped[str] = mapped_column(String(16), default="unknown", nullable=False)
    last_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    alerted: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    checks: Mapped[list["Check"]] = relationship(
        back_populates="target",
        cascade="all, delete-orphan",
    )


class Check(Base):
    __tablename__ = "checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    target_id: Mapped[int] = mapped_column(
        ForeignKey("targets.id", ondelete="CASCADE"),
        nullable=False,
    )
    up: Mapped[bool] = mapped_column(nullable=False)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    target: Mapped[Target] = relationship(back_populates="checks")
