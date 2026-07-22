"""
agent/local_agent.py
----------------------
로컬 캡처 에이전트 (PyQt 없음, 백그라운드 콘솔 프로세스).

전역 핫키(core/hotkey.py)로 화면을 캡처(core/capture.py)하고, 배포된 백엔드에 세션을
만들어 스크린샷을 올린 뒤, 기본 브라우저로 그 세션의 웹 페이지를 연다. 질문 입력/답변
표시/코드 패널은 모두 웹(React) 쪽에서 처리하며, 이 에이전트는 캡처+핫키 감지만 담당한다.

실행 전제 (Windows, VSCode 터미널):
    pip install -r requirements.txt
    python -m agent.local_agent

최초 실행 시 기기 페어링이 필요하며(브라우저가 자동으로 열려 로그인 후 기기 승인),
승인되면 로컬에 토큰이 저장되어 이후 실행부터는 다시 승인할 필요가 없다.
"""
from __future__ import annotations

import sys

import requests

from agent.agent_config import load_device_token, save_device_token
from agent.pairing import pair_device
from config import BACKEND_BASE_URL, CAPTURE_HOTKEY
from core.capture import ScreenCapture
from core.hotkey import HotkeyListener


class LocalCaptureAgent:
    def __init__(self):
        self.capture = ScreenCapture()
        self.hotkey = HotkeyListener(hotkey=CAPTURE_HOTKEY)
        self.device_token = load_device_token() or self._pair_and_save()

    @staticmethod
    def _pair_and_save() -> str:
        token = pair_device()
        save_device_token(token)
        print("기기 페어링 완료. 이후 실행부터는 다시 승인할 필요가 없습니다.")
        return token

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.device_token}"}

    def on_capture(self) -> None:
        try:
            result = self.capture.capture()
        except Exception as e:  # noqa: BLE001
            print(f"캡처 실패: {e}")
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
            print(f"백엔드 업로드 실패: {e}")
            return

        print(f"캡처 완료 ({result.width}x{result.height}) -> {session['session_url']}")
        import webbrowser

        webbrowser.open(session["session_url"])

    def run(self) -> None:
        try:
            self.hotkey.start(self.on_capture)
        except Exception as e:  # noqa: BLE001
            print(f"전역 단축키 등록 실패: {e}")
            sys.exit(1)

        print(f"'{CAPTURE_HOTKEY}' 단축키 대기 중... (Ctrl+C로 종료)")
        try:
            import keyboard

            keyboard.wait()
        except KeyboardInterrupt:
            pass
        finally:
            self.hotkey.stop()


if __name__ == "__main__":
    LocalCaptureAgent().run()
