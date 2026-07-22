"""
core/llm_client.py
--------------------
Gemini API 래퍼. 실제 API 키가 없어도(mock=True) 파이프라인 전체를 테스트할 수 있도록
real/mock 두 모드를 지원한다.

설계 이유 (Claude에서 Gemini로 교체, 무료 티어 활용):
- core/prompt_builder.py는 특정 벤더에 묶이지 않은 범용 메시지 포맷(role + text/image
  content blocks)만 만든다. 이 모듈이 그 포맷을 Gemini API의 `contents` 구조로 변환하는
  책임을 진다 — 나중에 벤더를 또 바꾸더라도 prompt_builder.py는 그대로 두면 된다.
- google-genai 패키지는 real 모드를 사용할 때만 import하므로, 패키지가 설치되지 않았거나
  키가 없는 환경에서도 mock 모드 테스트/실행은 항상 가능하다.
- 실제 키를 얻으면 GEMINI_API_KEY 환경변수만 설정하면 자동으로 real 모드로 전환된다
  (config.py 참조). Gemini API 키는 https://aistudio.google.com/apikey 에서 무료로 발급받을
  수 있고, gemini-2.5-flash는 무료 티어 한도 내에서 쓸 수 있다.
"""
from __future__ import annotations

import base64
import os
import re
from typing import List, Dict, Any, Optional


class LLMClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-2.5-flash",
        mock: Optional[bool] = None,
        max_tokens: int = 4096,  # 1024였을 때 답변이 문장 중간에 잘리는 문제가 있었음
    ):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
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
            from google import genai
            from google.genai import types
        except ImportError as e:
            raise RuntimeError(
                "google-genai 패키지가 설치되어 있지 않습니다. `pip install google-genai`로 설치하세요."
            ) from e

        if not self.api_key:
            raise RuntimeError(
                "GEMINI_API_KEY가 설정되어 있지 않습니다. 환경변수를 설정하거나 "
                "LLMClient(api_key=...)로 직접 전달하세요."
            )

        client = genai.Client(api_key=self.api_key)
        response = client.models.generate_content(
            model=self.model,
            contents=self._to_gemini_parts(messages),
            config=types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=self.max_tokens,
            ),
        )
        return response.text or ""

    @staticmethod
    def _to_gemini_parts(messages: List[Dict[str, Any]]) -> List[Any]:
        """core/prompt_builder.py의 범용 content blocks를 Gemini `contents` 리스트로 변환한다.

        지금은 build_messages()가 항상 user 메시지 1개만 만들기 때문에 role 구분 없이
        평평한 Part 리스트로 넘겨도 충분하다 (SDK가 단일 user 턴으로 취급한다).
        """
        from google.genai import types

        parts: List[Any] = []
        for message in messages:
            content = message.get("content", [])
            if isinstance(content, str):
                parts.append(content)
                continue
            for block in content:
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
                elif block.get("type") == "image":
                    source = block.get("source", {})
                    parts.append(
                        types.Part.from_bytes(
                            data=base64.b64decode(source.get("data", "")),
                            mime_type=source.get("media_type", "image/png"),
                        )
                    )
        return parts

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
            "[MOCK 응답 - GEMINI_API_KEY 미설정, 실제 LLM 호출 없음]",
            f"질문 요약: {question.strip() if question else '(질문을 추출하지 못함)'}",
        ]
        if has_image:
            lines.append("스크린샷 입력이 감지되었습니다. (mock 모드에서는 실제 이미지 분석을 수행하지 않습니다.)")
        if doc_title:
            lines.append(f"원인 진단(RAG 근거): '{doc_title}' 문서와 관련된 문제로 보입니다.")
            lines.append(f"주의사항: {doc_pitfall}")
        else:
            lines.append("관련 Unity 문서를 찾지 못해 일반적인 답변만 가능합니다. (실제 키 연결 후 재확인 필요)")
        lines.append("실제 코드 제안은 GEMINI_API_KEY 연결 후 real 모드에서 확인하세요.")
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
        user_question="점프가 두 번 눌려도 한 번만 되는지 화면 보고 알려줘",
        rag_context=context,
    )
    client = LLMClient()  # 키 없음 -> 자동 mock 모드
    print("mock 모드 여부:", client.mock)
    print(client.ask(messages, system=build_system_prompt()))
