"""
backend/db.py
--------------
SQLAlchemy 엔진/세션 팩토리. 기본은 로컬 SQLite 파일(backend/data/app.db)이며,
DATABASE_URL 환경변수로 다른 DB(예: 배포 환경의 Postgres)로 교체할 수 있다.
"""
from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

_DEFAULT_SQLITE_PATH = Path(__file__).resolve().parent / "data" / "app.db"
_DEFAULT_SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{_DEFAULT_SQLITE_PATH}")

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """모든 모델의 테이블을 생성한다 (앱 시작 시 1회 호출)."""
    from backend import models  # noqa: F401  (모델 등록을 위해 import)

    Base.metadata.create_all(bind=engine)
