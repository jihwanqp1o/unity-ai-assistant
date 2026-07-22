"""
backend/app.py
---------------
FastAPI 앱 진입점.

실행 (개발):
    uvicorn backend.app:app --reload --port 8000

프로덕션에서는 frontend/ 를 빌드(`npm run build`)해 나온 frontend/dist를 이 앱이
정적으로 서빙한다 (API 라우터가 먼저 매칭되므로 /api/* 와 충돌하지 않는다).
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend import auth, devices, sessions
from backend.db import init_db
from config import FRONTEND_BASE_URL


@asynccontextmanager
async def _lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Unity AI Assistant", lifespan=_lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_BASE_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(devices.router)
app.include_router(sessions.router)


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


_FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if _FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=_FRONTEND_DIST, html=True), name="frontend")
