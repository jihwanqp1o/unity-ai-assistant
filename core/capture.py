"""
core/capture.py
-----------------
단축키로 트리거되는 온디맨드 화면 캡처 모듈 (mss 사용).

주의 (샌드박스 vs 실제 환경):
- 이 모듈은 실제 디스플레이가 있는 Windows 환경에서 동작을 확인해야 한다.
- 개발에 사용한 리눅스 샌드박스는 헤드리스(디스플레이 없음)라 mss.grab() 실제 캡처는
  이 환경에서 실행 확인이 불가능하다. import/구조/인코딩 로직만 이 환경에서 검증했다.
- VSCode(Windows)에서 `pip install mss`후 `python core/capture.py`로 실제 캡처를
  1차 확인할 것을 권장한다.
"""
from __future__ import annotations

import base64
import io
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class CaptureResult:
    png_bytes: bytes
    width: int
    height: int

    def to_base64(self) -> str:
        return base64.b64encode(self.png_bytes).decode("ascii")


class ScreenCapture:
    """mss를 이용한 화면 캡처. monitor_index=0은 전체 가상 화면, 1부터는 개별 모니터."""

    def __init__(self, monitor_index: int = 1):
        self.monitor_index = monitor_index

    def capture(self, region: Optional[Tuple[int, int, int, int]] = None) -> CaptureResult:
        """스크린샷을 PNG bytes로 캡처한다.

        region: (left, top, width, height) 지정 시 해당 영역만 캡처(예: Unity 에디터 창 영역).
                None이면 monitor_index 전체를 캡처한다.
        """
        try:
            import mss
            from PIL import Image
        except ImportError as e:
            raise RuntimeError(
                "mss / Pillow 패키지가 필요합니다. `pip install mss pillow`로 설치하세요."
            ) from e

        with mss.mss() as sct:
            if region is not None:
                left, top, width, height = region
                monitor = {"left": left, "top": top, "width": width, "height": height}
            else:
                monitor = sct.monitors[self.monitor_index]

            raw = sct.grab(monitor)
            img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")

            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return CaptureResult(png_bytes=buf.getvalue(), width=img.width, height=img.height)


if __name__ == "__main__":
    # 실제 디스플레이가 있는 환경(Windows)에서만 정상 동작 확인 가능.
    try:
        cap = ScreenCapture()
        result = cap.capture()
        print(f"캡처 성공: {result.width}x{result.height}, {len(result.png_bytes)} bytes")
    except Exception as e:  # noqa: BLE001 - 데모 스크립트이므로 광범위 예외 허용
        print(f"이 환경에서는 실제 캡처를 확인할 수 없습니다 (정상): {e}")
