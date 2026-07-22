import os
import pytest

from core.llm_client import LLMClient
from core.prompt_builder import build_messages, build_system_prompt
from core.rag import UnityDocRAG


def test_auto_mock_when_no_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    client = LLMClient()
    assert client.mock is True


def test_explicit_mock_true_even_with_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-test-key")
    client = LLMClient(mock=True)
    assert client.mock is True


def test_mock_ask_reports_no_api_key():
    client = LLMClient(mock=True)
    messages = build_messages(user_question="테스트", rag_context="컨텍스트 없음")
    answer = client.ask(messages, system=build_system_prompt())
    assert "MOCK" in answer
    assert "GEMINI_API_KEY" in answer


def test_mock_ask_surfaces_rag_doc_title():
    rag = UnityDocRAG()
    matches = rag.search("점프가 두 번 눌려도 한 번만 되는데 isGrounded 관련인 것 같아요")
    context = rag.format_context(matches)
    messages = build_messages(user_question="점프 문제", rag_context=context)

    client = LLMClient(mock=True)
    answer = client.ask(messages, system=build_system_prompt())
    assert "점프 & 접지 판정" in answer


def test_real_mode_without_key_raises():
    client = LLMClient(mock=False, api_key=None)
    messages = build_messages(user_question="q", rag_context="ctx")
    with pytest.raises(RuntimeError):
        client.ask(messages, system=build_system_prompt())
