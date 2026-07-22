"""
agent_entry.py
----------------
PyInstaller 빌드 진입점. `agent/local_agent.py`를 패키지 안쪽에서 직접 빌드 대상으로
잡으면 `from agent.agent_config import ...` 같은 절대 임포트가 프로즌 실행파일 안에서
깨지기 쉬워서, 저장소 루트에 있는 이 얇은 래퍼를 대신 빌드 진입점으로 쓴다
(옛 main.py와 같은 위치/역할).

빌드:
    pyinstaller --onefile --windowed --name UnityAIAssistantAgent agent_entry.py
    # 결과물: dist/UnityAIAssistantAgent.exe (설치 프로그램은 installer/agent.iss 참고)
"""
from __future__ import annotations

from agent.local_agent import LocalCaptureAgent

if __name__ == "__main__":
    LocalCaptureAgent().run()
