"""
config.py
----------
프로젝트 전역 설정. 환경변수 기반으로 API 키를 읽어오며, 키가 없으면
core/llm_client.py가 자동으로 mock 모드로 동작한다.

사용법 (Windows, VSCode 터미널 기준):
    setx GEMINI_API_KEY "..."   # https://aistudio.google.com/apikey 에서 무료 발급, 새 터미널부터 적용
    또는 프로젝트 루트에 .env 파일을 만들고 python-dotenv로 로드해도 됨(선택 사항).
"""
import os

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
# gemini-2.5-flash: 무료 티어에서 쓸 수 있는 안정 버전. Google이 모델을 새로 내놓으면
# 이 환경변수만 바꿔서 업그레이드하면 된다("-latest" 별칭은 예고 없이 바뀌어 깨질 수 있어
# 일부러 안 씀 — core/llm_client.py 참고).
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
# 답변이 문장 중간에 잘리던 문제(기본 1024 토큰)를 고치기 위해 늘려둔 값.
GEMINI_MAX_OUTPUT_TOKENS = int(os.environ.get("GEMINI_MAX_OUTPUT_TOKENS", "4096"))

# Q4/Q5에서 정의한 범위: 온디맨드 캡처 단축키
CAPTURE_HOTKEY = os.environ.get("CAPTURE_HOTKEY", "ctrl+shift+c")

# 라이트 RAG 매칭 파라미터
RAG_TOP_K = 3
RAG_MIN_SCORE = 1.0

# 웹 전환: 배포된 프론트엔드/백엔드 기준 URL.
# 기본값은 실제 배포된 Render 서비스(단일 오리진이라 프론트/백엔드 주소가 동일)이다 —
# 로컬 캡처 에이전트를 배포용으로 패키징(installer/agent.iss)할 때 이 기본값이 그대로
# 쓰이므로, 일반 사용자는 환경변수를 따로 설정하지 않아도 배포된 백엔드에 연결된다.
# 로컬 개발 시에는 FRONTEND_BASE_URL/BACKEND_BASE_URL 환경변수로 각각
# Vite(5173)/uvicorn(8000)을 가리키도록 덮어쓴다.
FRONTEND_BASE_URL = os.environ.get("FRONTEND_BASE_URL", "https://unity-ai-assistant.onrender.com")
BACKEND_BASE_URL = os.environ.get("BACKEND_BASE_URL", "https://unity-ai-assistant.onrender.com")
