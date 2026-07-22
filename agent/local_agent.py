"""
agent/local_agent.py
----------------------
로컬 캡처 에이전트 (PyQt 없음, 시스템 트레이 아이콘 기반 백그라운드 프로세스).

전역 핫키(core/hotkey.py)로 화면을 캡처(core/capture.py)하고, 배포된 백엔드에 세션을
만들어 스크린샷을 올린 뒤, 기본 브라우저로 그 세션의 웹 페이지를 연다. 질문 입력/답변
표시/코드 패널은 모두 웹(React) 쪽에서 처리하며, 이 에이전트는 캡처+핫키 감지+상태
표시(트레이 아이콘)만 담당한다.

트레이 아이콘을 쓰는 이유: 이 프로세스는 창이 없는 백그라운드 프로그램이라 실행 중인지
아닌지 한눈에 알기 어렵다. 트레이 메뉴가 상태 텍스트(대기/캡처 중/실패 등)를 보여주고,
"지금 캡처"(핫키 대체 수단)와 "종료"를 제공한다. pystray의 메뉴 콜백은 자체 스레드에서
실행되고 icon.run()은 메인 스레드를 블로킹하므로, 페어링/핫키 등록은 별도 스레드
(_bootstrap)에서 수행한다.

실행 전제 (Windows, VSCode 터미널):
    pip install -r requirements.txt
    python -m agent.local_agent

배포용 설치 프로그램 빌드는 agent_entry.py + installer/agent.iss 참고 (README 참고).

최초 실행 시 기기 페어링이 필요하며(브라우저가 자동으로 열려 로그인 후 기기 승인),
승인되면 로컬에 토큰이 저장되어 이후 실행부터는 다시 승인할 필요가 없다.
"""
from __future__ import annotations

import threading
import webbrowser
from typing import Optional

import pystray
import requests

from agent.agent_config import load_device_token, save_device_token
from agent.pairing import pair_device
from config import BACKEND_BASE_URL, CAPTURE_HOTKEY, FRONTEND_BASE_URL
from core.capture import ScreenCapture
from core.hotkey import HotkeyListener


def _build_tray_image():
    from PIL import Image, ImageDraw

    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((2, 2, size - 2, size - 2), fill=(63, 185, 80, 255))  # 기존 다크테마 강조색 #3fb950
    draw.text((size / 2 - 4, size / 2 - 7), "U", fill=(30, 31, 34, 255))
    return img


class LocalCaptureAgent:
    def __init__(self):
        self.capture = ScreenCapture()
        self.hotkey = HotkeyListener(hotkey=CAPTURE_HOTKEY)
        self.device_token: Optional[str] = None
        self.status_text = "시작하는 중..."

        self._icon = pystray.Icon(
            "unity_ai_assistant",
            _build_tray_image(),
            "Unity AI Assistant",
            menu=pystray.Menu(
                pystray.MenuItem(lambda item: self.status_text, None, enabled=False),
                pystray.MenuItem("지금 캡처", self._handle_capture_clicked),
                pystray.MenuItem("히스토리 열기", self._handle_open_history),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("종료", self._handle_quit),
            ),
        )

    def _set_status(self, text: str) -> None:
        self.status_text = text
        self._icon.update_menu()

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.device_token}"}

    # ------------------------------------------------------------------
    def _bootstrap(self) -> None:
        """트레이 아이콘이 뜬 뒤 백그라운드 스레드에서 페어링+핫키 등록을 수행한다."""
        token = load_device_token()
        if not token:
            self._set_status("브라우저에서 기기 승인을 기다리는 중...")
            try:
                token = pair_device(on_pair_url=self._notify_pair_url)
            except Exception as e:  # noqa: BLE001
                self._set_status(f"기기 페어링 실패: {e}")
                return
            save_device_token(token)
        self.device_token = token

        try:
            self.hotkey.start(self.on_capture)
        except Exception as e:  # noqa: BLE001
            self._set_status(f"전역 단축키 등록 실패: {e}")
            return

        self._set_status(f"대기 중 ({CAPTURE_HOTKEY})")
        # 창이 없는 백그라운드 프로그램이라 실행됐는지 알기 어려우므로, 준비가 끝나면
        # 눈에 보이는 알림을 한 번 띄운다 — 핫키가 어렵다는 피드백이 있어 트레이 메뉴로도
        # 캡처할 수 있다는 것을 여기서 같이 알린다.
        self._icon.notify(
            f"Unity AI Assistant가 실행 중입니다.\n"
            f"캡처하려면 {CAPTURE_HOTKEY}를 누르거나, 트레이 아이콘을 우클릭해 "
            f"'지금 캡처'를 선택하세요.",
            "Unity AI Assistant 준비 완료",
        )

    def _notify_pair_url(self, pair_url: str) -> None:
        self._icon.notify(
            f"브라우저에서 이 기기를 승인해주세요:\n{pair_url}", "Unity AI Assistant - 기기 승인 필요"
        )

    # ------------------------------------------------------------------
    def on_capture(self) -> None:
        if not self.device_token:
            self._set_status("아직 기기 페어링이 끝나지 않았습니다")
            return

        self._set_status("캡처 중...")
        try:
            result = self.capture.capture()
        except Exception as e:  # noqa: BLE001
            self._set_status(f"캡처 실패: {e}")
            return

        try:
            create_resp = requests.post(
                f"{BACKEND_BASE_URL}/api/sessions", headers=self._headers(), timeout=10
            )
            create_resp.raise_for_status()
            session = create_resp.json()

            requests.post(
                f"{BACKEND_BASE_URL}/api/sessions/{session['id']}/screenshot",
                json={"screenshot_b64": result.to_base64()},
                headers=self._headers(),
                timeout=10,
            ).raise_for_status()
        except requests.RequestException as e:
            self._set_status(f"백엔드 업로드 실패: {e}")
            return

        self._set_status(f"캡처 완료 ({result.width}x{result.height})")
        self._icon.notify("캡처 완료. 브라우저에서 질문을 입력하세요.", "Unity AI Assistant")
        webbrowser.open(session["session_url"])

    # ------------------------------------------------------------------
    def _handle_capture_clicked(self, icon, item) -> None:
        self.on_capture()

    def _handle_open_history(self, icon, item) -> None:
        webbrowser.open(f"{FRONTEND_BASE_URL}/app/history")

    def _handle_quit(self, icon, item) -> None:
        self.hotkey.stop()
        icon.stop()

    def run(self) -> None:
        threading.Thread(target=self._bootstrap, daemon=True).start()
        self._icon.run()  # 메인 스레드를 블로킹 (Windows 트레이 이벤트 루프 요건)


if __name__ == "__main__":
    LocalCaptureAgent().run()
