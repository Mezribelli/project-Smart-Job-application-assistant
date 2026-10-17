"""SQL persistence for agent runs (SGBD / SQL requirement).

Stores every analysis+generation+execution run so the dashboard can show a
history of unit-test campaigns. Uses SQLite by default (zero-config) and any
SQLAlchemy URL -- including PostgreSQL -- via ``AI_DATABASE_URL``.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from sqlalchemy import DateTime, Float, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

_DEFAULT_DB_DIR = Path(__file__).resolve().parents[1] / "data"
_DEFAULT_DB_PATH = _DEFAULT_DB_DIR / "ai_service.db"


def _default_url() -> str:
    explicit = os.environ.get("AI_DATABASE_URL")
    if explicit:
        return explicit
    _DEFAULT_DB_DIR.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{_DEFAULT_DB_PATH.as_posix()}"


class Base(DeclarativeBase):
    pass


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    language: Mapped[str] = mapped_column(String(32))
    provider: Mapped[str] = mapped_column(String(32))
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    functions_count: Mapped[int] = mapped_column(Integer, default=0)
    classes_count: Mapped[int] = mapped_column(Integer, default=0)
    complexity: Mapped[int] = mapped_column(Integer, default=0)
    test_status: Mapped[str | None] = mapped_column(String(8), nullable=True)
    coverage: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_preview: Mapped[str] = mapped_column(Text, default="")
    test_preview: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "language": self.language,
            "provider": self.provider,
            "model": self.model,
            "functionsCount": self.functions_count,
            "classesCount": self.classes_count,
            "complexity": self.complexity,
            "testStatus": self.test_status,
            "coverage": self.coverage,
            "sourcePreview": self.source_preview,
            "testPreview": self.test_preview,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }


_engine = None
_SessionFactory: sessionmaker[Session] | None = None


def configure(url: str | None = None) -> None:
    """(Re)configure the engine. Mainly used by tests."""

    global _engine, _SessionFactory
    _engine = create_engine(url or _default_url(), future=True)
    _SessionFactory = sessionmaker(bind=_engine, expire_on_commit=False, future=True)
    Base.metadata.create_all(_engine)


def _ensure_configured() -> None:
    if _SessionFactory is None:
        configure()


@contextmanager
def get_session() -> Iterator[Session]:
    _ensure_configured()
    assert _SessionFactory is not None
    session = _SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def save_run(
    *,
    language: str,
    provider: str,
    model: str | None,
    analysis: dict[str, Any],
    test_source: str,
    source: str,
    test_status: str | None = None,
    coverage: float | None = None,
) -> dict[str, Any]:
    run = AnalysisRun(
        language=language,
        provider=provider,
        model=model,
        functions_count=len(analysis.get("functions", [])),
        classes_count=len(analysis.get("classes", [])),
        complexity=int(analysis.get("complexity", 0)),
        test_status=test_status,
        coverage=coverage,
        source_preview=source[:2000],
        test_preview=test_source[:2000],
    )
    with get_session() as session:
        session.add(run)
        session.flush()
        run_id = run.id
        snapshot = run.to_dict()
    snapshot["id"] = run_id
    return snapshot


def list_runs(limit: int = 20) -> list[dict[str, Any]]:
    with get_session() as session:
        rows = session.execute(
            select(AnalysisRun).order_by(AnalysisRun.id.desc()).limit(limit)
        ).scalars().all()
        return [row.to_dict() for row in rows]


def get_run(run_id: int) -> dict[str, Any] | None:
    with get_session() as session:
        row = session.get(AnalysisRun, run_id)
        return row.to_dict() if row else None
