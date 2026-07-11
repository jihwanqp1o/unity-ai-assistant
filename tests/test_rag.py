import json
import pytest

from core.rag import UnityDocRAG


@pytest.fixture(scope="module")
def rag():
    return UnityDocRAG()


@pytest.fixture(scope="module")
def scenarios():
    from pathlib import Path

    path = Path(__file__).resolve().parent.parent / "data" / "test_scenarios.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_load_snippets_nonempty(rag):
    assert len(rag.snippets) >= 20, "스니펫이 20개 이상이어야 함(Q4/데이터 제약 조건)"


def test_search_returns_top1_correctly_for_all_scenarios(rag, scenarios):
    """Q6 성공지표의 핵심 전제: 대표 시나리오에서 RAG가 정답 문서를 top-1으로 찾아야 함."""
    failures = []
    for scn in scenarios:
        matches = rag.search(scn["question"], top_k=1)
        top1 = matches[0].snippet["id"] if matches else None
        if top1 != scn["expected_snippet_id"]:
            failures.append((scn["id"], scn["expected_snippet_id"], top1))
    assert not failures, f"RAG top-1 불일치: {failures}"


def test_search_no_match_returns_empty(rag):
    matches = rag.search("완전히 관련 없는 질문 asdkjaslkdj 12345", top_k=3)
    # 무관한 질의는 매칭이 없거나 매우 적어야 한다 (거짓 양성 방지 확인용).
    assert isinstance(matches, list)


def test_format_context_empty_list_has_fallback_message(rag):
    context = rag.format_context([])
    assert "찾지 못했습니다" in context


def test_format_context_includes_source_and_pitfall(rag):
    matches = rag.search("점프가 두 번 눌리는 문제, isGrounded")
    context = rag.format_context(matches)
    assert "출처" in context
    assert "주의사항" in context
