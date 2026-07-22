"""
core/hotkey.py
----------------
전역 단축키(기본 Ctrl+Shift+C)로 콜백을 트리거하는 모듈.

Windows 표준 RegisterHotKey API(ctypes)를 사용한다. 원래는 `keyboard` 라이브러리의
저수준 키보드 후킹으로 구현했으나, 실사용 중 한 PC에서 단일 키(F9 등)는 정상 감지되면서도
Ctrl 계열 조합키(Ctrl+Shift+C, Ctrl+Alt+C 등 어떤 조합이든)만 원인 불명의 이유로 전혀
감지되지 않는 문제가 확인됐다 — 같은 환경에서 RegisterHotKey는 즉시 정상 동작했다.
조합키 자체를 OS가 책임지고 WM_HOTKEY 메시지로 통지해주므로, 후킹 방식보다 더 신뢰할 수 있다.

주의 (샌드박스 vs 실제 환경):
- Windows 전용 API이므로 Windows가 아닌 환경(헤드리스 리눅스 샌드박스 등)에서는
  start() 호출 시 RuntimeError가 발생한다 (import 및 클래스 시그니처만 검증 가능).
- 관리자 권한은 필요하지 않다. 다만 이미 다른 프로그램이 선점한 조합은 등록이
  실패한다 (RegisterHotKey가 False를 반환, 에러 코드가 예외 메시지에 포함된다).
"""
from __future__ import annotations

import ctypes
import threading
from typing import Callable, Dict, Optional, Tuple


DEFAULT_HOTKEY = "ctrl+shift+c"

_MOD_ALT = 0x0001
_MOD_CONTROL = 0x0002
_MOD_SHIFT = 0x0004
_MOD_WIN = 0x0008
_MOD_NOREPEAT = 0x4000  # 키를 누르고 있어도 OS auto-repeat로 재트리거되지 않도록 함

_WM_HOTKEY = 0x0312
_WM_QUIT = 0x0012
_HOTKEY_ID = 1

_MODIFIER_FLAGS = {
    "ctrl": _MOD_CONTROL,
    "control": _MOD_CONTROL,
    "alt": _MOD_ALT,
    "shift": _MOD_SHIFT,
    "win": _MOD_WIN,
    "windows": _MOD_WIN,
}

_VK_MAP: Dict[str, int] = {}
_VK_MAP.update({chr(c): c for c in range(0x30, 0x3A)})  # '0'-'9'
_VK_MAP.update({chr(c).lower(): c for c in range(0x41, 0x5B)})  # 'a'-'z'
_VK_MAP.update({f"f{i}": 0x70 + i - 1 for i in range(1, 25)})  # f1-f24


def _parse_hotkey(hotkey: str) -> Tuple[int, int]:
    parts = [p.strip().lower() for p in hotkey.split("+") if p.strip()]
    if not parts:
        raise ValueError(f"빈 단축키 문자열입니다: {hotkey!r}")
    *modifier_names, key_name = parts
    modifiers = 0
    for name in modifier_names:
        if name not in _MODIFIER_FLAGS:
            raise ValueError(f"알 수 없는 보조키입니다: {name!r} (in {hotkey!r})")
        modifiers |= _MODIFIER_FLAGS[name]
    if key_name not in _VK_MAP:
        raise ValueError(f"알 수 없는 키입니다: {key_name!r} (in {hotkey!r})")
    return modifiers, _VK_MAP[key_name]


class HotkeyListener:
    def __init__(self, hotkey: str = DEFAULT_HOTKEY):
        self.hotkey = hotkey
        self._modifiers, self._vk = _parse_hotkey(hotkey)
        self._thread: Optional[threading.Thread] = None
        self._thread_id: Optional[int] = None
        self._registered = threading.Event()
        self._register_error: Optional[Exception] = None

    def start(self, on_trigger: Callable[[], None]) -> None:
        """전역 단축키를 등록하고, 눌릴 때마다 on_trigger()를 호출한다.

        RegisterHotKey는 등록한 스레드의 메시지 큐로만 WM_HOTKEY를 보내므로, 등록과
        GetMessage 루프를 전담하는 백그라운드 스레드를 하나 띄운다. 등록 실패 시(다른
        프로그램이 이미 선점 등) 이 메서드를 호출한 스레드에서 즉시 RuntimeError가 난다.
        """
        if self._thread is not None:
            return
        self._register_error = None
        self._registered.clear()
        self._thread = threading.Thread(
            target=self._run, args=(on_trigger,), daemon=True, name="HotkeyListener"
        )
        self._thread.start()
        self._registered.wait(timeout=2.0)
        if self._register_error is not None:
            self._thread = None
            raise self._register_error

    def _run(self, on_trigger: Callable[[], None]) -> None:
        try:
            import ctypes.wintypes as wintypes

            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
        except (ImportError, AttributeError, OSError):
            self._register_error = RuntimeError(
                "이 환경은 Windows RegisterHotKey API를 지원하지 않습니다 (Windows 전용 기능)."
            )
            self._registered.set()
            return

        self._thread_id = kernel32.GetCurrentThreadId()

        if not user32.RegisterHotKey(None, _HOTKEY_ID, self._modifiers | _MOD_NOREPEAT, self._vk):
            err = kernel32.GetLastError()
            self._register_error = RuntimeError(
                f"전역 단축키 등록 실패 (Windows 에러 코드 {err}). "
                f"'{self.hotkey}' 조합을 다른 프로그램이 이미 선점하고 있을 수 있습니다."
            )
            self._registered.set()
            return

        self._registered.set()
        msg = wintypes.MSG()
        try:
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                if msg.message == _WM_HOTKEY and msg.wParam == _HOTKEY_ID:
                    on_trigger()
        finally:
            user32.UnregisterHotKey(None, _HOTKEY_ID)

    def stop(self) -> None:
        if self._thread is None:
            return
        if self._thread_id is not None:
            try:
                ctypes.windll.user32.PostThreadMessageW(self._thread_id, _WM_QUIT, 0, 0)
            except (AttributeError, OSError):
                pass
        self._thread.join(timeout=2.0)
        self._thread = None
        self._thread_id = None


if __name__ == "__main__":
    import time

    def _on_trigger():
        print("단축키가 눌렸습니다! (실제 캡처 트리거는 agent/local_agent.py에서 연결됨)")

    listener = HotkeyListener()
    try:
        listener.start(_on_trigger)
        print(f"'{DEFAULT_HOTKEY}' 단축키 대기 중... (Ctrl+C로 종료)")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    except Exception as e:  # noqa: BLE001
        print(f"이 환경에서는 전역 단축키 등록을 확인할 수 없습니다: {e}")
    finally:
        listener.stop()
