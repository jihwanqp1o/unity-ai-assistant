"""
scripts/run_scenario_eval.py
------------------------------
개정 PRD Q6 성공지표를 자동으로 측정하는 스크립트:
  "사전 준비한 대표 Unity 에러·버그 시나리오 N건 중, 도구가 원인을 정확히
   진단하고 유효한 해결 코드를 제안한 비율" (목표 80% 이상)

측정 방식:
  1) data/test_scenarios.json의 각 시나리오 질문에 대해 라이트 RAG(core/rag.py)가
     정답 스니펫(expected_snippet_id)을 top-1으로 정확히 찾는지 확인한다.
  2) 찾았다면 ClaudeClient(mock 또는 real)로 실제 파이프라인을 끝까지 실행해
     응답을 생성한다.
  3) top-1 정답률을 Q6 성공지표의 1차 근사치로 리포트한다.

주의: API 키가 없는 상태(mock 모드)에서는 "RAG가 올바른 문서를 찾았는가"까지만
정량 검증되며, LLM이 실제로 올바른 코드를 생성하는지는 real 모드 연결 후
사람이 직접 확인해야 한다 (README 참고).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.rag import UnityDocRAG  # noqa: E402
from core.claude_client import ClaudeClient  # noqa: E402
from core.prompt_builder import build_messages, build_system_prompt  # noqa: E402


def load_scenarios() -> list[dict]:
    path = ROOT / "data" / "test_scenarios.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    scenarios = load_scenarios()
    rag = UnityDocRAG()
    client = ClaudeClient()

    print(f"총 {len(scenarios)}개 시나리오 평가 시작 (Claude 모드: {'MOCK' if client.mock else 'REAL'})\n")

    correct = 0
    results = []

    for scn in scenarios:
        matches = rag.search(scn["question"], top_k=1)
        top1_id = matches[0].snippet["id"] if matches else None
        is_correct = top1_id == scn["expected_snippet_id"]
        correct += int(is_correct)

        context = rag.format_context(matches)
        messages = build_messages(user_question=scn["question"], rag_context=context)
        answer = client.ask(messages, system=build_system_prompt())

        results.append(
            {
                "id": scn["id"],
                "question": scn["question"],
                "expected": scn["expected_snippet_id"],
                "retrieved_top1": top1_id,
                "correct": is_correct,
            }
        )

        status = "PASS" if is_correct else "FAIL"
        print(f"[{status}] {scn['id']}: {scn['question'][:40]}...")
        print(f"       기대: {scn['expected_snippet_id']} / 검색됨: {top1_id}")
        if not is_correct:
            print(f"       (mock/real 응답 일부) {answer.splitlines()[0] if answer else ''}")
        print()

    accuracy = correct / len(scenarios) * 100
    print("=" * 60)
    print(f"RAG top-1 정확도: {correct}/{len(scenarios)} = {accuracy:.1f}%")
    print("목표(Q6 성공지표): 80% 이상")
    print("PASS" if accuracy >= 80 else "FAIL", "- 목표 대비", "달성" if accuracy >= 80 else "미달")

    if client.mock:
        print(
            "\n※ 현재 MOCK 모드입니다. 이 수치는 '라이트 RAG 검색 정확도'만 측정한 것이며,\n"
            "   실제 LLM 코드 생성 품질은 ANTHROPIC_API_KEY 연결 후 real 모드로 재평가해야 합니다."
        )


if __name__ == "__main__":
    main()
