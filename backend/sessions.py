"""
backend/sessions.py
---------------------
캡처 세션 CRUD + 질문 응답. 로컬 에이전트가 세션을 만들고 스크린샷을 올리면(Device 인증),
React 프론트엔드가 그 세션을 읽고 질문을 보낸다(User 쿠키 인증). `/quick`은 에이전트가
캡처 직후 네이티브 입력창에서 받은 질문을 스크린샷과 함께 한 번에 보내 즉시 답변까지
받는 용도(Device 인증) — Unity↔브라우저 전환을 한 번으로 줄이기 위해 추가됨.

질문 응답 로직은 기존 core/rag.py, core/prompt_builder.py를 변경 없이 그대로 재사용하고,
LLM 호출은 core/llm_client.py(Gemini)를 통한다 — 옛 main.py의 UnityAssistantApp.on_send()와
동일한 순서 (RAG 검색 → 컨텍스트 포맷 → 메시지 빌드 → LLM 호출). `/ask`(User 인증)와
`/quick`(Device 인증) 둘 다 이 순서를 그대로 타므로 `_answer_question()`으로 공유한다.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DbSession

from backend.auth import get_current_user
from backend.db import get_db
from backend.devices import get_current_device
from backend.models import CaptureSession, Device, User
from backend.schemas import (
    AskRequest,
    AskResponse,
    QuickCaptureIn,
    QuickCaptureOut,
    ScreenshotIn,
    SessionCreateOut,
    SessionOut,
)
from config import FRONTEND_BASE_URL, GEMINI_MAX_OUTPUT_TOKENS, GEMINI_MODEL, RAG_MIN_SCORE, RAG_TOP_K
from core.llm_client import LLMClient
from core.prompt_builder import build_messages, build_system_prompt
from core.rag import UnityDocRAG

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

_rag = UnityDocRAG()
_client = LLMClient(model=GEMINI_MODEL, max_tokens=GEMINI_MAX_OUTPUT_TOKENS)


def _get_owned_session(session_id: str, user_id: int, db: DbSession) -> CaptureSession:
    session = db.get(CaptureSession, session_id)
    if session is None or session.user_id != user_id:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    return session


def _answer_question(
    session: CaptureSession, question: str, code_paste: Optional[str], db: DbSession
) -> AskResponse:
    matches = _rag.search(question, top_k=RAG_TOP_K, min_score=RAG_MIN_SCORE)
    context = _rag.format_context(matches)
    messages = build_messages(
        user_question=question,
        rag_context=context,
        code_paste=code_paste,
        screenshot_b64=session.screenshot_b64,
    )
    answer = _client.ask(messages, system=build_system_prompt())

    session.question = question
    session.code_paste = code_paste
    session.answer = answer
    session.status = "answered"
    db.commit()

    return AskResponse(answer=answer, mock=_client.mock)


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
    return _answer_question(session, body.question, body.code_paste, db)


@router.post("/quick", response_model=QuickCaptureOut)
def quick_capture(
    body: QuickCaptureIn,
    device: Device = Depends(get_current_device),
    db: DbSession = Depends(get_db),
) -> QuickCaptureOut:
    """캡처 직후 에이전트의 네이티브 입력창에서 받은 질문을 스크린샷과 함께 한 번에 받아
    세션 생성 → 스크린샷 저장 → 답변까지 한 요청으로 끝낸다 (agent/quick_dialog.py 참고)."""
    session = CaptureSession(user_id=device.user_id, screenshot_b64=body.screenshot_b64, status="ready")
    db.add(session)
    db.commit()
    db.refresh(session)

    result = _answer_question(session, body.question, body.code_paste, db)

    return QuickCaptureOut(
        id=session.id,
        session_url=f"{FRONTEND_BASE_URL}/app/session/{session.id}",
        answer=result.answer,
        mock=result.mock,
    )


@router.delete("/{session_id}")
def delete_session(
    session_id: str, user: User = Depends(get_current_user), db: DbSession = Depends(get_db)
) -> dict:
    session = _get_owned_session(session_id, user.id, db)
    db.delete(session)
    db.commit()
    return {"ok": True}
