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

import time
import webbrowser

import requests

from config import BACKEND_BASE_URL

POLL_INTERVAL_SECONDS = 2.0
POLL_TIMEOUT_SECONDS = 300.0


def pair_device() -> str:
    start = requests.post(f"{BACKEND_BASE_URL}/api/devices/pair/start", timeout=10)
    start.raise_for_status()
    body = start.json()
    device_code, pair_url = body["device_code"], body["pair_url"]

    print(f"브라우저에서 이 기기를 승인해주세요: {pair_url}")
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
