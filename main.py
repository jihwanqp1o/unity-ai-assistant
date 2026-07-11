"""
main.py
--------
Unity AI Assistant 엔트리포인트. 개정 PRD(Q4/Q5) 핵심 기능 3개를 배선한다:
  1) Unity 문서 라이트 RAG (core/rag.py)
  2) 스크린샷 기반 상황 인식 (core/capture.py, core/hotkey.py)
  3) 원클릭 코드 적용 (ui/overlay_window.py)

실행 전제 (Windows, VSCode 터미널):
    pip install -r requirements.txt
    python main.py

이 세션(리눅스 헤드리스 샌드박스)에서는 PyQt 창 렌더링·전역 단축키·실제 화면 캡처를
실행 확인할 수 없다. core/rag.py, core/prompt_builder.py, core/claude_client.py(mock)는
이 환경에서 이미 개별 실행 검증을 마쳤다 (tests/ 참고).
"""
from __future__ import annotations

import sys

from config import CAPTURE_HOTKEY, RAG_TOP_K, RAG_MIN_SCORE
from core.rag import UnityDocRAG
from core.claude_client import ClaudeClient
from core.prompt_builder import build_messages, build_system_prompt
from core.capture import ScreenCapture
from core.hotkey import HotkeyListener


class UnityAssistantApp:
    def __init__(self):
        self.rag = UnityDocRAG()
        self.client = ClaudeClient()  # 키 없으면 자동 mock 모드
        self.capture = ScreenCapture()
        self.hotkey = HotkeyListener(hotkey=CAPTURE_HOTKEY)
        self.pending_screenshot_b64: str | None = None
        self.overlay = None  # UI는 build_overlay()에서 지연 생성

    # ------------------------------------------------------------------
    def build_overlay(self):
        from ui.overlay_window import OverlayWindow

        self.overlay = OverlayWindow(
            on_capture_clicked=self.on_capture,
            on_send_clicked=self.on_send,
            hotkey_label=CAPTURE_HOTKEY,
        )
        return self.overlay

    # ------------------------------------------------------------------
    def on_capture(self) -> None:
        if self.overlay:
            self.overlay.set_status("● 캡처 중...")
        try:
            result = self.capture.capture()
            self.pending_screenshot_b64 = result.to_base64()
            if self.overlay:
                self.overlay.set_status(f"● 캡처 완료 ({result.width}x{result.height})")
        except Exception as e:  # noqa: BLE001
            if self.overlay:
                self.overlay.set_status(f"● 캡처 실패: {e}")

    def on_send(self, question: str) -> None:
        if self.overlay:
            self.overlay.append_user_message(question)
            self.overlay.set_status("● 분석 중...")

        matches = self.rag.search(question, top_k=RAG_TOP_K, min_score=RAG_MIN_SCORE)
        context = self.rag.format_context(matches)

        messages = build_messages(
            user_question=question,
            rag_context=context,
            screenshot_b64=self.pending_screenshot_b64,
        )
        answer = self.client.ask(messages, system=build_system_prompt())

        if self.overlay:
            self.overlay.append_ai_message(answer)
            self.overlay.set_status("● 분석 완료" if not self.client.mock else "● 분석 완료 (MOCK 모드)")

    # ------------------------------------------------------------------
    def run(self) -> None:
        try:
            from PyQt5 import QtWidgets
        except ImportError:
            print(
                "PyQt5가 설치되어 있지 않아 GUI를 시작할 수 없습니다.\n"
                "  pip install PyQt5\n"
                "설치 후 다시 실행하세요. (RAG/Claude 파이프라인만 테스트하려면 "
                "scripts/run_scenario_eval.py를 사용하세요.)"
            )
            sys.exit(1)

        app = QtWidgets.QApplication(sys.argv)
        overlay = self.build_overlay()

        try:
            self.hotkey.start(self.on_capture)
        except Exception as e:  # noqa: BLE001
            print(f"전역 단축키 등록 실패(계속 진행, 캡처 버튼은 정상 동작): {e}")

        overlay.show()
        exit_code = app.exec_()
        self.hotkey.stop()
        sys.exit(exit_code)


if __name__ == "__main__":
    UnityAssistantApp().run()
