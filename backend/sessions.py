"""
backend/sessions.py
---------------------
캡처 세션 CRUD + 질문 응답. 로컬 에이전트가 세션을 만들고 스크린샷을 올리면(Device 인증),
React 프론트엔드가 그 세션을 읽고 질문을 보낸다(User 쿠키 인증).

질문 응답 로직은 기존 core/rag.py, core/prompt_builder.py를 변경 없이 그대로 재사용하고,
LLM 호출은 core/llm_client.py(Gemini)를 통한다 — 옛 main.py의 UnityAssistantApp.on_send()와
동일한 순서 (RAG 검색 → 컨텍스트 포맷 → 메시지 빌드 → LLM 호출).
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DbSession

from backend.auth import get_current_user
from backend.db import get_db
from backend.devices import get_current_device
from backend.models import CaptureSession, Device, User
from backend.schemas import AskRequest, AskResponse, ScreenshotIn, SessionCreateOut, SessionOut
from config import FRONTEND_BASE_URL, GEMINI_MODEL, RAG_MIN_SCORE, RAG_TOP_K
from core.llm_client import LLMClient
from core.prompt_builder import build_messages, build_system_prompt
from core.rag import UnityDocRAG

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

_rag = UnityDocRAG()
_client = LLMClient(model=GEMINI_MODEL)


def _get_owned_session(session_id: str, user_id: int, db: DbSession) -> CaptureSession:
    session = db.get(CaptureSession, session_id)
    if session is None or session.user_id != user_id:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    return session


@router.post("", response_model=SessionCreateOut)
def create_session(device: Device = Depends(get_current_device), db: DbSession = Depends(get_db)) -> SessionCreateOut:
    session = CaptureSession(user_id=device.user_id, status="capturing")
    db.add(session)
    db.commit()
    db.refresh(session)
    return SessionCreateOut(id=session.id, session_url=f"{FRONTEND_BASE_URL}/app/session/{session.id}")


@router.post("/{session_id}/screenshot")
def upload_screenshot(
    session_id: str,
    body: ScreenshotIn,
    device: Device = Depends(get_current_device),
    db: DbSession = Depends(get_db),
) -> dict:
    session = _get_owned_session(session_id, device.user_id, db)
    session.screenshot_b64 = body.screenshot_b64
    session.status = "ready"
    db.commit()
    return {"ok": True}


@router.get("", response_model=List[SessionOut])
def list_sessions(user: User = Depends(get_current_user), db: DbSession = Depends(get_db)) -> List[CaptureSession]:
    return (
        db.query(CaptureSession)
        .filter(CaptureSession.user_id == user.id)
        .order_by(CaptureSession.created_at.desc())
        .all()
    )


@router.get("/{session_id}", response_model=SessionOut)
def get_session(session_id: str, user: User = Depends(get_current_user), db: DbSession = Depends(get_db)) -> CaptureSession:
    return _get_owned_session(session_id, user.id, db)


@router.post("/{session_id}/ask", response_model=AskResponse)
def ask(
    session_id: str,
    body: AskRequest,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
) -> AskResponse:
    session = _get_owned_session(session_id, user.id, db)

    matches = _rag.search(body.question, top_k=RAG_TOP_K, min_score=RAG_MIN_SCORE)
    context = _rag.format_context(matches)
    messages = build_messages(
        user_question=body.question,
        rag_context=context,
        code_paste=body.code_paste,
        screenshot_b64=session.screenshot_b64,
    )
    answer = _client.ask(messages, system=build_system_prompt())

    session.question = body.question
    session.code_paste = body.code_paste
    session.answer = answer
    session.status = "answered"
    db.commit()

    return AskResponse(answer=answer, mock=_client.mock)
