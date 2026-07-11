"""
ui/overlay_window.py
----------------------
Unity 에디터 옆에 always-on-top으로 떠 있는 오버레이 대화창 (Q5 화면 2, mockup_q4_3 참고).

주의 (샌드박스 vs 실제 환경):
- 이 샌드박스는 헤드리스(디스플레이 서버 없음)라 PyQt5 창을 실제로 렌더링해
  스크린샷으로 확인할 수 없다. 이 파일은 문법 검증(py_compile)까지만 이 환경에서 확인했다.
- VSCode(Windows)에서 `pip install PyQt5` 후 `python ui/overlay_window.py`로
  실제 창이 뜨는지 1차로 직접 확인할 것.

UI 구성 (Q5 화면 설명과 1:1 대응):
- 상단: 캡처 버튼("📷 화면 캡처") + 상태 라벨("대기 중" / "분석 중" / "분석 완료")
- 중앙: 대화 로그 (사용자 질문 / AI 응답 텍스트)
- 코드 블록: 마지막 응답에서 추출된 코드 + "원클릭 적용"(클립보드 복사) 버튼
- 하단: 질문 입력창 + 전송 버튼
"""
from __future__ import annotations

import re
from typing import Callable, Optional


_CODE_BLOCK_RE = re.compile(r"```(?:\w+)?\n(.*?)```", re.DOTALL)


def _extract_first_code_block(text: str) -> Optional[str]:
    """AI 응답 텍스트에서 ```...``` 코드 블록을 하나 추출한다 (원클릭 복사용)."""
    match = _CODE_BLOCK_RE.search(text)
    return match.group(1).strip() if match else None


def _strip_first_code_block(text: str) -> str:
    """채팅 로그에는 코드 블록 대신 안내 문구만 남긴다 (아래 코드창과 중복 방지)."""
    return _CODE_BLOCK_RE.sub("📋 [코드 블록 — 아래 코드창 참고]", text, count=1)


STYLESHEET = """
QWidget {
    background-color: #1e1f22;
    color: #e6e6e6;
    font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
    font-size: 10.5pt;
}
QPushButton {
    background-color: #2b2d31;
    border: 1px solid #3f4147;
    border-radius: 6px;
    padding: 7px 14px;
}
QPushButton:hover {
    background-color: #35373c;
    border-color: #3fb950;
}
QPushButton:pressed {
    background-color: #26282c;
}
QPushButton:disabled {
    color: #6b6e73;
    border-color: #2c2d30;
}
QTextEdit, QPlainTextEdit, QLineEdit {
    background-color: #26282c;
    border: 1px solid #3f4147;
    border-radius: 6px;
    padding: 8px;
    selection-background-color: #3fb95055;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #3fb950;
}
QLabel#sectionLabel {
    color: #9aa0a6;
    font-weight: 600;
}
"""

_STATUS_COLORS = {
    "대기": "#9aa0a6",
    "캡처 중": "#58a6ff",
    "캡처 완료": "#58a6ff",
    "캡처 실패": "#f85149",
    "분석 중": "#d29922",
    "분석 완료": "#3fb950",
    "복사되었습니다": "#3fb950",
}

ONBOARDING_HTML = (
    "<div style='color:#9aa0a6; font-style:italic;'>"
    "👋 <b>사용법</b><br>"
    "① 상단 <b>📷 화면 캡처</b> 버튼 또는 <b>Ctrl+Shift+C</b>로 Unity 에디터 화면을 캡처하세요<br>"
    "② 아래 입력창에 궁금한 점을 적고 <b>전송</b>을 누르세요<br>"
    "③ AI가 Unity 공식 문서를 근거로 답변하고, 코드가 있으면 아래 코드창과 "
    "<b>원클릭 적용</b> 버튼으로 클립보드에 복사할 수 있어요"
    "</div><hr style='border-color:#3f4147;'>"
)


class OverlayWindow:
    """PyQt5 오버레이 창. 지연 import로 PyQt5 미설치 환경에서도 모듈 자체는 import 가능하다."""

    def __init__(
        self,
        on_capture_clicked: Callable[[], None],
        on_send_clicked: Callable[[str], None],
        hotkey_label: str = "Ctrl+Shift+C",
    ):
        try:
            from PyQt5 import QtWidgets, QtCore, QtGui
        except ImportError as e:
            raise RuntimeError(
                "PyQt5가 설치되어 있지 않습니다. `pip install PyQt5`로 설치하세요."
            ) from e

        self._QtWidgets = QtWidgets
        self._QtCore = QtCore
        self._QtGui = QtGui
        self.on_capture_clicked = on_capture_clicked
        self.on_send_clicked = on_send_clicked
        self._last_code_block: Optional[str] = None

        self.window = QtWidgets.QWidget()
        self.window.setWindowTitle("Unity Assistant Overlay")
        self.window.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Window
        )
        self.window.resize(600, 680)
        self.window.setStyleSheet(STYLESHEET)

        layout = QtWidgets.QVBoxLayout(self.window)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        # --- 상단: 캡처 버튼 + 도움말 + 상태 ---
        top_row = QtWidgets.QHBoxLayout()
        top_row.setSpacing(8)
        self.capture_btn = QtWidgets.QPushButton(f"📷 화면 캡처  ({hotkey_label})")
        self.capture_btn.clicked.connect(self._handle_capture_clicked)
        self.help_btn = QtWidgets.QPushButton("❓")
        self.help_btn.setFixedWidth(36)
        self.help_btn.setToolTip("사용법 다시 보기")
        self.help_btn.clicked.connect(self._handle_help_clicked)
        self.status_label = QtWidgets.QLabel()
        self._set_status_style("대기 중")
        top_row.addWidget(self.capture_btn)
        top_row.addWidget(self.help_btn)
        top_row.addStretch()
        top_row.addWidget(self.status_label)
        layout.addLayout(top_row)

        # --- 중앙: 대화 로그 ---
        log_label = QtWidgets.QLabel("대화")
        log_label.setObjectName("sectionLabel")
        layout.addWidget(log_label)
        self.chat_log = QtWidgets.QTextEdit()
        self.chat_log.setReadOnly(True)
        self.chat_log.setHtml(ONBOARDING_HTML)
        layout.addWidget(self.chat_log, stretch=3)

        # --- 코드 블록 + 원클릭 적용 ---
        code_row = QtWidgets.QHBoxLayout()
        code_label = QtWidgets.QLabel("마지막 제안 코드")
        code_label.setObjectName("sectionLabel")
        self.copy_btn = QtWidgets.QPushButton("📋 원클릭 적용 (클립보드 복사)")
        self.copy_btn.clicked.connect(self._handle_copy_clicked)
        self.copy_btn.setEnabled(False)
        code_row.addWidget(code_label)
        code_row.addStretch()
        code_row.addWidget(self.copy_btn)
        layout.addLayout(code_row)

        self.code_view = QtWidgets.QPlainTextEdit()
        self.code_view.setReadOnly(True)
        self.code_view.setMaximumHeight(160)
        layout.addWidget(self.code_view)

        # --- 하단: 입력창 + 전송 ---
        bottom_row = QtWidgets.QHBoxLayout()
        bottom_row.setSpacing(8)
        self.input_line = QtWidgets.QLineEdit()
        self.input_line.setPlaceholderText("질문하거나 코드를 붙여넣으세요...")
        self.input_line.returnPressed.connect(self._handle_send_clicked)
        self.send_btn = QtWidgets.QPushButton("전송 ▶")
        self.send_btn.clicked.connect(self._handle_send_clicked)
        bottom_row.addWidget(self.input_line, stretch=1)
        bottom_row.addWidget(self.send_btn)
        layout.addLayout(bottom_row)

    # ------------------------------------------------------------------
    def show(self) -> None:
        self.window.show()

    def _set_status_style(self, text: str) -> None:
        color = "#9aa0a6"
        for key, c in _STATUS_COLORS.items():
            if key in text:
                color = c
                break
        self.status_label.setText(f"● {text}")
        self.status_label.setStyleSheet(f"color: {color}; font-weight: 600;")

    def set_status(self, text: str) -> None:
        # 기존 호출부가 "● 접두사"를 직접 붙여서 넘기므로 호환을 위해 제거 후 재적용한다.
        self._set_status_style(text.lstrip("● ").strip())

    def _handle_help_clicked(self) -> None:
        self.chat_log.append(ONBOARDING_HTML)
        self._scroll_chat_to_bottom()

    def _scroll_chat_to_bottom(self) -> None:
        cursor = self.chat_log.textCursor()
        cursor.movePosition(self._QtGui.QTextCursor.End)
        self.chat_log.setTextCursor(cursor)
        self.chat_log.ensureCursorVisible()

    def append_user_message(self, text: str) -> None:
        self.chat_log.append(f"<b>나</b><br>{text}<br>")
        self._scroll_chat_to_bottom()

    def append_ai_message(self, text: str) -> None:
        code = _extract_first_code_block(text)
        display_text = _strip_first_code_block(text) if code else text
        self.chat_log.append(f"<b style='color:#3fb950'>AI</b><br>{display_text.replace(chr(10), '<br>')}<br>")
        self._scroll_chat_to_bottom()
        if code:
            self._last_code_block = code
            self.code_view.setPlainText(code)
            self.copy_btn.setEnabled(True)

    # ------------------------------------------------------------------
    def _handle_capture_clicked(self) -> None:
        self.on_capture_clicked()

    def _handle_send_clicked(self) -> None:
        text = self.input_line.text().strip()
        if not text:
            return
        self.input_line.clear()
        self.on_send_clicked(text)

    def _handle_copy_clicked(self) -> None:
        if not self._last_code_block:
            return
        clipboard = self._QtWidgets.QApplication.clipboard()
        clipboard.setText(self._last_code_block)
        self.set_status("● 코드가 클립보드에 복사되었습니다")


if __name__ == "__main__":
    # 실제 디스플레이가 있는 환경(Windows)에서만 창이 뜨는지 확인 가능.
    try:
        from PyQt5 import QtWidgets

        app = QtWidgets.QApplication([])

        def _demo_capture():
            print("캡처 버튼 클릭됨 (데모)")

        def _demo_send(text: str):
            print(f"전송된 질문: {text}")

        win = OverlayWindow(on_capture_clicked=_demo_capture, on_send_clicked=_demo_send)
        win.append_user_message("점프가 두 번 눌려도 한 번만 되는데 화면 보고 알려줘")
        win.append_ai_message(
            "isGrounded 갱신 시점 문제로 보입니다.\n```csharp\nisGrounded = Physics.CheckSphere(groundCheck.position, 0.2f, groundMask);\n```"
        )
        win.show()
        app.exec_()
    except Exception as e:  # noqa: BLE001
        print(f"이 환경에서는 실제 창 렌더링을 확인할 수 없습니다 (정상): {e}")
