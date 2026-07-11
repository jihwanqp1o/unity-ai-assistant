"""
core/prompt_builder.py
-----------------------
스크린샷(선택) + 사용자 질문/코드 + 라이트 RAG 검색 결과를 하나의 Claude Messages API
요청 형태로 결합한다. 이 모듈은 순수 함수로만 구성되어 있어 외부 의존성 없이
단위 테스트가 가능하다 (anthropic 패키지 자체는 core/claude_client.py에서만 사용).
"""
from __future__ import annotations

from typing import Optional, List, Dict, Any


SYSTEM_PROMPT = (
    "당신은 Unity 게임 엔진에 특화된 1인 인디 개발자용 코딩 어시스턴트입니다. "
    "사용자가 제공하는 Unity 에디터 스크린샷과 코드, 그리고 아래 제공되는 Unity 공식 "
    "문서 스니펫을 근거로 정확하고 실행 가능한 답변을 제공하세요.\n\n"
    "규칙:\n"
    "1. 제공된 문서 스니펫과 모순되는 답을 하지 마세요. 근거가 부족하면 '불확실'이라고 명시하세요.\n"
    "2. 코드 제안 시 Unity 버전(예: Unity 6에서 velocity -> linearVelocity)을 고려하세요.\n"
    "3. 답변은 (1) 원인 진단 (2) 즉시 적용 가능한 수정 코드 (3) 한 줄 요약 순서로 구성하세요.\n"
    "4. 화면을 근거로 진단할 때는 어떤 요소(Inspector 값, 콘솔 로그 등)를 보고 판단했는지 밝히세요."
)


def build_system_prompt() -> str:
    return SYSTEM_PROMPT


def build_user_content(
    user_question: str,
    rag_context: str,
    code_paste: Optional[str] = None,
    screenshot_b64: Optional[str] = None,
    screenshot_media_type: str = "image/png",
) -> List[Dict[str, Any]]:
    """Anthropic Messages API의 단일 user 메시지 content 블록 리스트를 생성한다.

    - 이미지가 있으면 image 블록을 맨 앞에 둔다 (Vision 분석 우선순위).
    - RAG 컨텍스트와 사용자 질문/코드는 텍스트 블록으로 결합한다.
    """
    content: List[Dict[str, Any]] = []

    if screenshot_b64:
        content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": screenshot_media_type,
                    "data": screenshot_b64,
                },
            }
        )

    text_parts = [f"[사용자 질문]\n{user_question.strip()}"]

    if code_paste:
        text_parts.append(f"[붙여넣은 코드]\n```\n{code_paste.strip()}\n```")

    text_parts.append(f"[Unity 공식 문서 검색 결과 (라이트 RAG)]\n{rag_context.strip()}")

    content.append({"type": "text", "text": "\n\n".join(text_parts)})
    return content


def build_messages(
    user_question: str,
    rag_context: str,
    code_paste: Optional[str] = None,
    screenshot_b64: Optional[str] = None,
    screenshot_media_type: str = "image/png",
) -> List[Dict[str, Any]]:
    """anthropic.messages.create(messages=...)에 바로 넣을 수 있는 형태로 반환한다."""
    return [
        {
            "role": "user",
            "content": build_user_content(
                user_question=user_question,
                rag_context=rag_context,
                code_paste=code_paste,
                screenshot_b64=screenshot_b64,
                screenshot_media_type=screenshot_media_type,
            ),
        }
    ]


if __name__ == "__main__":
    msgs = build_messages(
        user_question="점프가 두 번 눌려도 한 번만 되는 것 같아요",
        rag_context="[문서 1] 점프 & 접지 판정 ...",
        code_paste="if (Input.GetButtonDown(\"Jump\")) rb.velocity = ...",
    )
    import json
    print(json.dumps(msgs, ensure_ascii=False, indent=2))
