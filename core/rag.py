"""
core/rag.py
-----------
"라이트 RAG": 벡터DB/임베딩 없이, 사전에 큐레이션된 Unity 공식 문서 스니펫(JSON)을
키워드 매칭만으로 검색하는 경량 검색 모듈.

1주 MVP 범위 결정 사항(A2 개정 PRD 참조):
- 임베딩 기반 벡터 검색 대신 키워드 오버랩 스코어링을 사용한다.
- 스니펫 수는 20~40개로 제한해 사람이 직접 큐레이션한 품질을 유지한다.
- 순수 표준 라이브러리만 사용해 외부 의존성 없이 단위 테스트가 가능하다.

이 모듈은 외부 라이브러리에 의존하지 않으므로, PyQt/anthropic 등이 설치되지
않은 환경에서도 독립적으로 테스트할 수 있다.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any


DEFAULT_SNIPPETS_PATH = Path(__file__).resolve().parent.parent / "data" / "unity_snippets.json"


@dataclass
class SnippetMatch:
    snippet: Dict[str, Any]
    score: float
    matched_keywords: List[str] = field(default_factory=list)


def _tokenize(text: str) -> List[str]:
    """소문자화 후 영숫자/한글 토큰만 추출한다."""
    text = text.lower()
    tokens = re.findall(r"[a-z0-9가-힣_]+", text)
    return tokens


class UnityDocRAG:
    """Unity 공식 문서 스니펫에 대한 키워드 기반 라이트 RAG 검색기."""

    def __init__(self, snippets_path: str | Path = DEFAULT_SNIPPETS_PATH):
        self.snippets_path = Path(snippets_path)
        self.snippets: List[Dict[str, Any]] = []
        self.load()

    def load(self) -> None:
        if not self.snippets_path.exists():
            raise FileNotFoundError(
                f"Unity 스니펫 데이터 파일을 찾을 수 없습니다: {self.snippets_path}"
            )
        with open(self.snippets_path, "r", encoding="utf-8") as f:
            self.snippets = json.load(f)

    def search(self, query: str, top_k: int = 3, min_score: float = 1.0) -> List[SnippetMatch]:
        """질의 문자열과 가장 관련 있는 스니펫 top_k개를 점수 내림차순으로 반환한다.

        스코어링 규칙(단순 키워드 오버랩, 임베딩 없음):
          - 스니펫의 keyword가 질의에 부분 문자열로 포함되면 키워드 길이에 비례해 가점
            (길고 구체적인 키워드일수록 높은 점수, 짧고 일반적인 키워드는 낮은 점수)
          - 스니펫 title의 토큰이 질의 토큰과 겹치면 +1점
          - 질의 토큰이 키워드 토큰과 부분적으로 겹치는 경우(부분 일치)도 소폭 가점
            (한국어 조사 변형: "위치가" vs "위치" 등)
        """
        query_lower = query.lower()
        query_tokens = set(_tokenize(query))

        matches: List[SnippetMatch] = []
        for snippet in self.snippets:
            score = 0.0
            matched_keywords: List[str] = []

            for kw in snippet.get("keywords", []):
                kw_lower = kw.lower()
                if kw_lower in query_lower:
                    specificity_bonus = min(len(kw_lower) * 0.4, 4.0)
                    score += 1.0 + specificity_bonus
                    matched_keywords.append(kw)
                else:
                    kw_tokens = _tokenize(kw)
                    matched_partial = False
                    for kt in kw_tokens:
                        if len(kt) < 2:
                            continue
                        for qt in query_tokens:
                            if len(qt) >= 2 and (qt.startswith(kt) or kt.startswith(qt)):
                                score += 0.8
                                matched_partial = True
                                break
                        if matched_partial:
                            break

            title_tokens = set(_tokenize(snippet.get("title", "")))
            for tt in title_tokens:
                if len(tt) < 2:
                    continue
                for qt in query_tokens:
                    if qt.startswith(tt) or tt.startswith(qt):
                        score += 1.0
                        break

            if score > 0:
                matches.append(
                    SnippetMatch(snippet=snippet, score=round(score, 2), matched_keywords=matched_keywords)
                )

        matches.sort(key=lambda m: m.score, reverse=True)
        filtered = [m for m in matches if m.score >= min_score]
        return filtered[:top_k]

    def format_context(self, matches: List[SnippetMatch]) -> str:
        """검색된 스니펫들을 LLM 프롬프트에 바로 삽입 가능한 텍스트 블록으로 포맷팅한다."""
        if not matches:
            return "(관련 Unity 공식 문서 스니펫을 찾지 못했습니다. 일반 지식으로 답변하되 불확실함을 명시하세요.)"

        blocks = []
        for i, m in enumerate(matches, start=1):
            s = m.snippet
            blocks.append(
                f"[문서 {i}] {s.get('title')} (출처: {s.get('source')})\n"
                f"내용: {s.get('snippet')}\n"
                f"주의사항: {s.get('pitfall', '-')}"
            )
        return "\n\n".join(blocks)


if __name__ == "__main__":
    rag = UnityDocRAG()
    demo_query = "점프가 두 번 눌려도 한 번만 되는데 isGrounded 관련인 것 같아요"
    results = rag.search(demo_query)
    print(f"질의: {demo_query}\n")
    print(rag.format_context(results))
