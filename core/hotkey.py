"""
core/hotkey.py
----------------
전역 단축키(기본 Ctrl+Shift+C)로 콜백을 트리거하는 모듈 (keyboard 라이브러리 사용).

주의 (샌드박스 vs 실제 환경):
- 전역 키보드 후킹은 실제 OS 입력 장치/권한이 필요해 헤드리스 리눅스 샌드박스에서는
  등록/트리거 동작을 실행 확인할 수 없다 (import 및 API 시그니처만 검증됨).
- Windows에서는 관리자 권한이 필요할 수 있다 (keyboard 라이브러리 특성).
- VSCode(Windows)에서 `pip install keyboard` 후 직접 실행해 단축키 반응을 확인할 것.
"""
from __future__ import annotations

from typing import Callable, Optional


DEFAULT_HOTKEY = "ctrl+shift+c"


class HotkeyListener:
    def __init__(self, hotkey: str = DEFAULT_HOTKEY):
        self.hotkey = hotkey
        self._registered = False

    def start(self, on_trigger: Callable[[], None]) -> None:
        """전역 단축키를 등록하고, 눌릴 때마다 on_trigger()를 호출한다.

        블로킹 호출이 아니며, keyboard.wait()를 별도로 호출하지 않는 한 즉시 반환된다.
        앱 종료 시 stop()으로 해제해야 한다.
        """
        try:
            import keyboard
        except ImportError as e:
            raise RuntimeError(
                "keyboard 패키지가 필요합니다. `pip install keyboard`로 설치하세요. "
                "Windows에서는 관리자 권한 실행이 필요할 수 있습니다."
            ) from e

        # trigger_on_release=True: 키를 누르고 있는 도중 OS가 auto-repeat로 key-down
        # 이벤트를 여러 번 보내면(길게 눌렀을 때 흔함) on_trigger가 중복 호출되는 문제가
        # 있었다. release는 물리적으로 키를 뗄 때 한 번만 발생하므로 이 문제가 없다.
        keyboard.add_hotkey(self.hotkey, on_trigger, trigger_on_release=True)
        self._registered = True

    def stop(self) -> None:
        if not self._registered:
            return
        try:
            import keyboard

            keyboard.remove_hotkey(self.hotkey)
        except Exception:
            # 앱 종료 시점의 정리 실패는 치명적이지 않으므로 조용히 무시한다.
            pass
        self._registered = False


if __name__ == "__main__":
    def _on_trigger():
        print("단축키가 눌렸습니다! (실제 캡처 트리거는 main.py에서 연결됨)")

    listener = HotkeyListener()
    try:
        listener.start(_on_trigger)
        print(f"'{DEFAULT_HOTKEY}' 단축키 대기 중... (Ctrl+C로 종료)")
        import keyboard

        keyboard.wait()
    except Exception as e:  # noqa: BLE001
        print(f"이 환경에서는 전역 단축키 등록을 확인할 수 없습니다 (정상): {e}")
