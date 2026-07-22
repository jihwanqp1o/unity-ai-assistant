"""
agent/agent_config.py
-----------------------
로컬 캡처 에이전트가 페어링으로 발급받은 기기 토큰을 저장/로드한다.

저장 위치:
  Windows: %APPDATA%/UnityAIAssistant/agent_config.json
  그 외 OS: ~/.unity-ai-assistant/agent_config.json
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional


def _config_path() -> Path:
    appdata = os.environ.get("APPDATA")
    base = Path(appdata) / "UnityAIAssistant" if appdata else Path.home() / ".unity-ai-assistant"
    base.mkdir(parents=True, exist_ok=True)
    return base / "agent_config.json"


def load_device_token() -> Optional[str]:
    path = _config_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return data.get("device_token")


def save_device_token(token: str) -> None:
    _config_path().write_text(
        json.dumps({"device_token": token}, ensure_ascii=False, indent=2), encoding="utf-8"
    )
