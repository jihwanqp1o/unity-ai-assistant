"""
backend/db.py
--------------
SQLAlchemy 엔진/세션 팩토리. 로컬 개발 기본값은 SQLite 파일(backend/data/app.db)이며,
DATABASE_URL 환경변수로 다른 DB(배포 환경의 Postgres 등)로 교체한다.

배포 환경(Render)은 반드시 Postgres를 써야 한다 — SQLite 파일은 컨테이너 디스크에 쓰는데,
Render 무료 웹 서비스는 영속 디스크를 지원하지 않아 재배포/재시작(슬립 후 깨어남 포함)마다
파일이 통째로 초기화된다. 실제로 이 때문에 "회원가입은 되는데 기존 계정으로 로그인은 안
되는" 버그가 있었다 — 재배포 사이에 계정이 사라진 것이었다. render.yaml이 무료 Postgres를
프로비저닝해 DATABASE_URL을 자동으로 채워준다.
"""
from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

_DEFAULT_SQLITE_PATH = Path(__file__).resolve().parent / "data" / "app.db"
_DEFAULT_SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{_DEFAULT_SQLITE_PATH}")
# Render(과거 Heroku 스타일 포함)의 Postgres 연결 문자열은 "postgres://"로 오는 경우가 있는데,
# SQLAlchemy 2.0의 기본 postgres 드라이버는 "postgresql://" 스킴만 인식한다.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

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
