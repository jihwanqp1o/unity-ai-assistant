"""
agent/updater.py
------------------
자동 업데이트: GitHub Releases에서 최신 에이전트 버전을 확인하고, 있으면 새 exe를 받아
현재 실행 파일을 교체한 뒤 재시작한다.

패키징된 exe(PyInstaller --onefile)에서만 의미가 있다 — `python -m agent.local_agent`로
소스에서 직접 실행 중이면(`sys.frozen`이 없음) 교체할 실행 파일 자체가 없으므로
`check_for_update()`가 항상 None을 반환한다.

Windows에서 실행 중인 자기 자신의 exe 파일은 바로 덮어쓸 수 없어서, 다운로드한 새 exe로
교체하는 작업은 별도의 배치 스크립트에 맡긴다: 현재 프로세스가 완전히 종료되기를 기다렸다가
새 exe로 옮기고 재실행한다. 페어링 토큰(%APPDATA%/UnityAIAssistant/agent_config.json)은
실행 파일과 별개 위치에 있어 업데이트해도 그대로 남는다 — 재승인 불필요.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from typing import Optional

import requests

from agent import __version__ as CURRENT_VERSION

_RELEASES_LATEST_API = "https://api.github.com/repos/jihwanqp1o/unity-ai-assistant/releases/latest"
_TAG_PREFIX = "agent-v"
_ASSET_NAME = "UnityAIAssistantAgent.exe"


def _parse_version(tag: str) -> Optional[tuple]:
    if not tag.startswith(_TAG_PREFIX):
        return None
    try:
        return tuple(int(part) for part in tag[len(_TAG_PREFIX):].split("."))
    except ValueError:
        return None


def check_for_update() -> Optional[dict]:
    """최신 릴리즈가 현재 실행 중인 버전보다 새로우면
    {"version": "1.2.0", "download_url": "..."}를 반환하고, 아니면(에러 포함) None을 반환한다."""
    if not getattr(sys, "frozen", False):
        return None  # 소스 실행 중이면 업데이트 대상 exe가 없음

    try:
        resp = requests.get(_RELEASES_LATEST_API, timeout=10)
        resp.raise_for_status()
        body = resp.json()
    except requests.RequestException:
        return None

    latest = _parse_version(body.get("tag_name", ""))
    current = _parse_version(_TAG_PREFIX + CURRENT_VERSION)
    if latest is None or current is None or latest <= current:
        return None

    asset = next((a for a in body.get("assets", []) if a.get("name") == _ASSET_NAME), None)
    if not asset:
        return None

    return {"version": ".".join(map(str, latest)), "download_url": asset["browser_download_url"]}


def apply_update(download_url: str) -> bool:
    """새 exe를 내려받아 현재 실행 파일을 교체하고 재시작하는 스크립트를 띄운다.

    True를 반환하면 교체 절차가 시작된 것이므로, 호출부는 바로 프로세스를 종료해야 한다
    (트레이 아이콘 stop 등). 다운로드 실패 등으로 False를 반환하면 아무 것도 바뀌지 않았으니
    평소처럼 계속 실행하면 된다.
    """
    if not getattr(sys, "frozen", False):
        return False

    current_exe = sys.executable
    tmp_dir = tempfile.mkdtemp(prefix="unity_ai_assistant_update_")
    new_exe_path = os.path.join(tmp_dir, _ASSET_NAME)

    try:
        with requests.get(download_url, stream=True, timeout=60) as resp:
            resp.raise_for_status()
            with open(new_exe_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1 << 16):
                    f.write(chunk)
    except (requests.RequestException, OSError):
        return False

    pid = os.getpid()
    script_path = os.path.join(tmp_dir, "update.bat")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(
            "@echo off\r\n"
            f"taskkill /PID {pid} /F >nul 2>&1\r\n"
            ":wait\r\n"
            f'tasklist /FI "PID eq {pid}" 2>nul | find "{pid}" >nul\r\n'
            "if not errorlevel 1 (\r\n"
            "  timeout /t 1 /nobreak >nul\r\n"
            "  goto wait\r\n"
            ")\r\n"
            f'move /Y "{new_exe_path}" "{current_exe}" >nul\r\n'
            f'start "" "{current_exe}"\r\n'
            f'rmdir /S /Q "{tmp_dir}" >nul 2>&1\r\n'
        )

    subprocess.Popen(
        ["cmd", "/c", script_path],
        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
        close_fds=True,
    )
    return True
