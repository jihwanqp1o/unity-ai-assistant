"""
config.py
----------
프로젝트 전역 설정. 환경변수 기반으로 API 키를 읽어오며, 키가 없으면
core/claude_client.py가 자동으로 mock 모드로 동작한다.

사용법 (Windows, VSCode 터미널 기준):
    setx ANTHROPIC_API_KEY "sk-ant-..."   # 새 터미널부터 적용
    또는 프로젝트 루트에 .env 파일을 만들고 python-dotenv로 로드해도 됨(선택 사항).
"""
import os

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-5")

# Q4/Q5에서 정의한 범위: 온디맨드 캡처 단축키
CAPTURE_HOTKEY = os.environ.get("CAPTURE_HOTKEY", "ctrl+shift+c")

# 라이트 RAG 매칭 파라미터
RAG_TOP_K = 3
RAG_MIN_SCORE = 1.0
