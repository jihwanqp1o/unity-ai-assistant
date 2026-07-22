"""
backend/app.py
---------------
FastAPI 앱 진입점.

실행 (개발):
    uvicorn backend.app:app --reload --port 8000

프로덕션에서는 frontend/ 를 빌드(`npm run build`)해 나온 frontend/dist를 이 앱이
정적으로 서빙한다 (API 라우터가 먼저 매칭되므로 /api/* 와 충돌하지 않는다).

SPA 라우팅 주의: React Router의 클라이언트 사이드 경로(/login, /pair, /app/session/:id 등)는
실제 파일이 아니라서, 단순히 StaticFiles(html=True)만 두면 브라우저가 그 경로로 직접
진입할 때(에이전트가 여는 세션 링크, 새로고침 등) 정적 파일 서버가 404를 반환해버린다
(React가 뜨기도 전에 서버 단계에서 막힘). 그래서 실제 자산은 /assets 마운트로만 서빙하고,
그 외 매칭되지 않는 모든 GET 요청은 index.html로 폴백해 React Router가 라우팅을 넘겨받게 한다.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
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
    app.mount("/assets", StaticFiles(directory=_FRONTEND_DIST / "assets"), name="frontend-assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str) -> FileResponse:
        # /api/* 는 위 라우터들이 이미 먼저 매칭해 처리하므로 여기 도달하지 않는다.
        return FileResponse(_FRONTEND_DIST / "index.html")
