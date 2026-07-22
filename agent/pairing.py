"""
agent/pairing.py
------------------
device-code 페어링 흐름 (CLI 도구의 `gh auth login`과 동일한 패턴):
  1) 백엔드에 새 device_code 발급 요청
  2) 승인 페이지를 기본 브라우저로 오픈
  3) 사용자가 웹에서 로그인 후 승인할 때까지 짧은 간격으로 폴링
  4) 승인되면 이후 API 호출에 쓸 기기 토큰을 반환
"""
from __future__ import annotations

import sys
import time
import webbrowser
from typing import Callable, Optional

import requests

from config import BACKEND_BASE_URL

POLL_INTERVAL_SECONDS = 2.0
POLL_TIMEOUT_SECONDS = 300.0


def _log(message: str) -> None:
    # --windowed로 패키징된 exe는 sys.stdout이 None이라 print()가 그대로 터진다.
    if sys.stdout is not None:
        print(message)


def pair_device(on_pair_url: Optional[Callable[[str], None]] = None) -> str:
    """새 device_code를 발급받아 브라우저 승인을 기다리고, 승인되면 기기 토큰을 반환한다.

    on_pair_url이 주어지면 콘솔 print 대신(또는 추가로) 그 콜백에도 승인 URL을 전달한다 —
    트레이 아이콘 알림 등 콘솔이 없는 실행 환경에서 사용자에게 알리기 위함.
    """
    start = requests.post(f"{BACKEND_BASE_URL}/api/devices/pair/start", timeout=10)
    start.raise_for_status()
    body = start.json()
    device_code, pair_url = body["device_code"], body["pair_url"]

    _log(f"브라우저에서 이 기기를 승인해주세요: {pair_url}")
    if on_pair_url:
        on_pair_url(pair_url)
    webbrowser.open(pair_url)

    deadline = time.monotonic() + POLL_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        resp = requests.get(f"{BACKEND_BASE_URL}/api/devices/pair/{device_code}", timeout=10)
        resp.raise_for_status()
        poll_body = resp.json()
        if poll_body["status"] == "claimed" and poll_body.get("token"):
            return poll_body["token"]
        time.sleep(POLL_INTERVAL_SECONDS)

    raise TimeoutError("기기 승인 대기 시간이 초과되었습니다. 에이전트를 다시 실행해주세요.")
