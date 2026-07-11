"""
core/claude_client.py
----------------------
Claude API 래퍼. 실제 API 키가 없어도(mock=True) 파이프라인 전체를 테스트할 수 있도록
real/mock 두 모드를 지원한다.

설계 이유 (1주 MVP 결정):
- 이번 세션 시점에는 API 키가 없는 상태(mock 모드)로 개발을 시작한다.
- anthropic 패키지는 real 모드를 사용할 때만 import하므로, 패키지가 설치되지 않았거나
  키가 없는 환경에서도 mock 모드 테스트/실행은 항상 가능하다.
- 실제 키를 얻으면 ANTHROPIC_API_KEY 환경변수만 설정하면 자동으로 real 모드로 전환된다
  (config.py 참조).
"""
from __future__ import annotations

import os
import re
from typing import List, Dict, Any, Optional


class ClaudeClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-5",
        mock: Optional[bool] = None,
        max_tokens: int = 1024,
    ):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model
        self.max_tokens = max_tokens
        # mock 인자를 명시하지 않으면 API 키 존재 여부로 자동 판단한다.
        self.mock = mock if mock is not None else (not bool(self.api_key))

    def ask(self, messages: List[Dict[str, Any]], system: str) -> str:
        if self.mock:
            return self._mock_ask(messages, system)
        return self._real_ask(messages, system)

    # ------------------------------------------------------------------
    # Real mode
    # ------------------------------------------------------------------
    def _real_ask(self, messages: List[Dict[str, Any]], system: str) -> str:
        try:
            import anthropic  # 지연 import: mock 모드에서는 설치 여부와 무관하게 동작
        except ImportError as e:
            raise RuntimeError(
                "anthropic 패키지가 설치되어 있지 않습니다. `pip install anthropic`으로 설치하세요."
            ) from e

        if not self.api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY가 설정되어 있지 않습니다. 환경변수를 설정하거나 "
                "ClaudeClient(api_key=...)로 직접 전달하세요."
            )

        client = anthropic.Anthropic(api_key=self.api_key)
        response = client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system,
            messages=messages,
        )
        # content는 블록 리스트이며 text 타입 블록만 이어붙인다.
        parts = [block.text for block in response.content if getattr(block, "type", None) == "text"]
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Mock mode - API 키 없이 파이프라인(검색→프롬프트→응답) 자체를 검증하기 위한 모드.
    # 실제 LLM 추론 품질은 검증하지 않으며, 라이트 RAG가 올바른 문서를 찾았는지와
    # 파이프라인 배선이 올바른지를 확인하는 용도이다.
    # ------------------------------------------------------------------
    def _mock_ask(self, messages: List[Dict[str, Any]], system: str) -> str:
        text = self._extract_text(messages)
        question = self._extract_between(text, "[사용자 질문]", "[")
        doc_title, doc_pitfall = self._extract_first_doc(text)
        has_image = self._has_image(messages)

        lines = [
            "[MOCK 응답 - ANTHROPIC_API_KEY 미설정, 실제 LLM 호출 없음]",
            f"질문 요약: {question.strip() if question else '(질문을 추출하지 못함)'}",
        ]
        if has_image:
            lines.append("스크린샷 입력이 감지되었습니다. (mock 모드에서는 실제 이미지 분석을 수행하지 않습니다.)")
        if doc_title:
            lines.append(f"원인 진단(RAG 근거): '{doc_title}' 문서와 관련된 문제로 보입니다.")
            lines.append(f"주의사항: {doc_pitfall}")
        else:
            lines.append("관련 Unity 문서를 찾지 못해 일반적인 답변만 가능합니다. (실제 키 연결 후 재확인 필요)")
        lines.append("실제 코드 제안은 ANTHROPIC_API_KEY 연결 후 real 모드에서 확인하세요.")
        return "\n".join(lines)

    @staticmethod
    def _extract_text(messages: List[Dict[str, Any]]) -> str:
        parts = []
        for m in messages:
            content = m.get("content", [])
            if isinstance(content, str):
                parts.append(content)
                continue
            for block in content:
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
        return "\n".join(parts)

    @staticmethod
    def _has_image(messages: List[Dict[str, Any]]) -> bool:
        for m in messages:
            content = m.get("content", [])
            if isinstance(content, list):
                for block in content:
                    if block.get("type") == "image":
                        return True
        return False

    @staticmethod
    def _extract_between(text: str, start: str, end_prefix: str) -> str:
        try:
            after = text.split(start, 1)[1]
            # end_prefix로 시작하는 다음 섹션 헤더 전까지만 취함
            idx = after.find("\n" + end_prefix)
            return after[:idx] if idx != -1 else after
        except IndexError:
            return ""

    @staticmethod
    def _extract_first_doc(text: str) -> tuple[str, str]:
        title_match = re.search(r"\[문서 1\]\s*(.+?)\s*\(출처", text)
        pitfall_match = re.search(r"주의사항:\s*(.+)", text)
        title = title_match.group(1).strip() if title_match else ""
        pitfall = pitfall_match.group(1).strip() if pitfall_match else ""
        return title, pitfall


if __name__ == "__main__":
    from prompt_builder import build_messages, build_system_prompt
    from rag import UnityDocRAG

    rag = UnityDocRAG()
    matches = rag.search("점프가 두 번 눌려도 한 번만 되는데 isGrounded 관련인 것 같아요")
    context = rag.format_context(matches)
    messages = build_messages(
        user_question="점프가 두 번 눌려도 한 번만 되는데 왜 그런지 화면 보고 알려줘",
        rag_context=context,
    )
    client = ClaudeClient()  # 키 없음 -> 자동 mock 모드
    print("mock 모드 여부:", client.mock)
    print(client.ask(messages, system=build_system_prompt()))
