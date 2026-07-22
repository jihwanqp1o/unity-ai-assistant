# Unity AI Assistant (1주 MVP) — VSCode 이어작업 가이드

개정 PRD(아산AX_개인PRD_4조_지환_개정판) 기준 구현. Unity 단일 엔진 · 온디맨드 스크린샷 ·
라이트 RAG 기반 코드 어시스턴트.

## 웹 전환 (2026-07-22)

PyQt5 always-on-top 오버레이 단일 프로세스였던 앱을 **로컬 캡처 에이전트 + 배포형
FastAPI 백엔드 + React 프론트엔드** 구조로 전환했다. 자세한 배경/아키텍처는 아래
"폴더 구조"와 `CLAUDE.md`를 참고. 이전 `ui/overlay_window.py`, `main.py`,
`UnityAIAssistant.spec`(PyQt5 exe 패키징)은 웹 UI로 대체되어 제거되었다.
`core/rag.py`, `core/prompt_builder.py`, `core/claude_client.py`는 변경 없이 그대로
백엔드에서 재사용되므로, 아래 "이 세션에서 한 일" / "RAG 정확도 이슈" 기록은 여전히 유효하다.

## 이 세션에서 한 일 / 못 한 일 (투명성을 위해 명시)

이 프로젝트는 Cowork의 리눅스 헤드리스 샌드박스(디스플레이 없음)에서 작성되었다.
아래 항목은 **Cowork 세션에서 실제로 실행·검증까지 완료**했다:

- `core/rag.py` (라이트 RAG 키워드 매칭) — 단위 테스트 15개 전부 통과 (`pytest tests/`)
- `core/prompt_builder.py` (프롬프트 조립) — 단위 테스트 통과
- `core/claude_client.py` mock 모드 — API 키 없이도 파이프라인 동작 확인
- `scripts/run_scenario_eval.py` — 대표 시나리오 8건 중 8건 RAG top-1 정확도 100%
  (최초 버전은 25%였고, 키워드/스코어링 로직을 수정해 100%까지 끌어올림 — 아래 "알아야 할 것" 참조)

### VSCode(Windows)에서 추가로 검증 완료 (2026-07-11)

Cowork 세션에서는 디스플레이/키보드 후킹이 없어 확인 못 했던 아래 항목들을, 실제
Windows 환경(Python 3.14, venv)에서 재검증 완료했다:

- `pytest tests/ -v` — 15개 전부 통과 (Windows/Python 3.14 환경에서도 재현됨)
- `scripts/run_scenario_eval.py` — mock 모드 8/8 (100%) 재현됨
- `ui/overlay_window.py` 단독 실행 — PyQt5 창이 정상 렌더링됨. 확장 윈도우 스타일
  검사(`GetWindowLong` ExStyle)로 `WS_EX_TOPMOST` 비트가 실제로 설정된 것을 확인 —
  always-on-top 정상 동작.
- `core/hotkey.py` 단독 실행 — **관리자 권한 없이도** 전역 단축키 등록이 성공했다
  (일반 사용자 권한으로 충분했음, README에 적힌 "관리자 권한 필요할 수 있음"은 이 환경
  기준으로는 해당 없음). 실제 하드웨어 스캔코드로 Ctrl+Shift+C를 시뮬레이션해 콜백이
  정확히 트리거되는 것도 확인.
- `core/capture.py` 단독 실행 — 실제 화면을 1920x1080 PNG로 정상 캡처(mss는
  `mss.mss()`가 deprecated라는 경고만 발생, 기능엔 문제 없음).
- `main.py` 통합 배선 — 캡처(base64 인코딩 성공) → RAG 검색("점프 & 착지 판정" 문서
  정확히 매칭) → prompt 조립 → mock client 응답 → 오버레이 채팅 로그 표시까지
  end-to-end로 정상 동작 확인.

### 아직 확인 못 한 것

- **Claude API 실제 호출(real 모드, Vision 분석 포함)** — `ANTHROPIC_API_KEY`가 아직
  없어(비용 문제로 보류) mock 모드로만 검증된 상태. 크레딧 확보 후
  `setx ANTHROPIC_API_KEY "sk-ant-..."`로 등록하고 `scripts/run_scenario_eval.py`를
  real 모드로 재실행해 실제 LLM 코드 제안 품질을 확인해야 한다 (Day 6, 아래 표 참조).

## 알아야 할 것 (RAG 정확도 이슈와 해결 과정)

처음 작성한 키워드 매칭 로직으로 대표 시나리오 8건을 돌렸을 때 정확도가 **25%**로
Q6 목표(80%)에 크게 못 미쳤다. 원인은 두 가지였다:

1. `collision-2d-vs-3d`처럼 "충돌" 같은 짧고 범용적인 키워드가 더 구체적인 문서
   (`collider-offset-mismatch`)를 이겨버리는 스코어링 문제
2. 스니펫의 키워드가 실제 사용자가 쓸 법한 구어체 표현("버튼을 눌러도 반응이 없어요" 등)을
   충분히 커버하지 못한 문제

`core/rag.py`의 스코어링을 키워드 길이(구체성) 기반 가중치로 바꾸고, `data/unity_snippets.json`의
`keywords`에 구어체 표현을 보강해 100%까지 개선했다. **다만 스니펫이 20~40개뿐인 라이트 RAG의
근본적 한계**로, 실제 사용 중 다루지 않은 새로운 유형의 질문에는 정확도가 떨어질 수 있다.
스니펫을 늘리거나(Day 2 참고) 실제 API 연결 후 real 모드로 종합 재평가가 필요하다.

## 폴더 구조

```
unity-ai-assistant/
├── config.py                  # 환경변수 기반 설정 (API 키, 단축키, FRONTEND/BACKEND_BASE_URL 등)
├── requirements.txt
├── Dockerfile                  # React 빌드 + FastAPI 서빙 멀티스테이지
├── core/                        # 웹 전환 이후에도 변경 없이 그대로 재사용
│   ├── rag.py                  # 라이트 RAG (키워드 매칭, 외부 의존성 없음)
│   ├── prompt_builder.py        # 프롬프트 조립 (외부 의존성 없음)
│   ├── claude_client.py         # Claude API 래퍼 (real/mock)
│   ├── capture.py               # 화면 캡처 (mss) — agent/에서 사용
│   └── hotkey.py                 # 전역 단축키 (keyboard) — agent/에서 사용
├── agent/                       # 로컬 캡처 에이전트 (PyQt 없음, 백그라운드 콘솔 프로세스)
│   ├── local_agent.py            # 핫키+캡처+세션 업로드+브라우저 오픈
│   ├── pairing.py                 # device-code 페어링
│   └── agent_config.py            # 페어링 토큰 로컬 저장
├── backend/                     # 배포형 FastAPI 백엔드
│   ├── app.py                    # 앱 진입점, 프론트 빌드 정적 서빙
│   ├── auth.py                    # 회원가입/로그인 (JWT 쿠키)
│   ├── devices.py                  # 기기 페어링 엔드포인트
│   ├── sessions.py                  # 세션/스크린샷/질문 엔드포인트 (core/* 재사용)
│   ├── models.py / db.py / security.py / schemas.py
│   └── tests/test_flow.py          # signup→pair→session→ask e2e 테스트
├── frontend/                    # React(Vite) 웹 UI
│   └── src/{pages,components,lib}
├── data/
│   ├── unity_snippets.json      # Unity 공식 문서 스니펫 33개
│   └── test_scenarios.json      # 대표 에러 시나리오 8건 (Q6 성공지표 측정용)
├── scripts/
│   └── run_scenario_eval.py     # Q6 성공지표 자동 측정 스크립트
└── tests/                        # core/* 단위 테스트 (웹 전환 영향 없음)
```

## VSCode에서 시작하기 (Windows)

```powershell
cd unity-ai-assistant
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 1) 먼저 mock 모드로 RAG 파이프라인 자체가 도는지 확인 (API 키 불필요)
python scripts\run_scenario_eval.py

# 2) 단위 테스트 (core/* + backend/*)
pytest tests\ backend\tests\ -v

# 3) 백엔드 실행 (FastAPI, 기본 포트 8000)
# FRONTEND_BASE_URL/BACKEND_BASE_URL 기본값은 실제 배포된 Render 주소다 — 로컬 개발 중에는
# 아래처럼 localhost로 덮어써야 pair_url/session_url이 로컬 프론트엔드를 가리킨다.
$env:FRONTEND_BASE_URL = "http://localhost:5173"
$env:BACKEND_BASE_URL = "http://localhost:8000"
uvicorn backend.app:app --reload --port 8000

# 4) 프론트엔드 실행 (별도 터미널, 기본 포트 5173 — /api는 자동으로 백엔드로 프록시됨)
cd frontend
npm install
npm run dev

# 5) 로컬 캡처 에이전트 실행 (별도 터미널, 위와 동일하게 localhost로 덮어써서 로컬 백엔드에 붙임)
$env:BACKEND_BASE_URL = "http://localhost:8000"
python -m agent.local_agent
# 최초 실행 시 브라우저가 열려 로그인+기기 승인을 요청한다. 이후 CAPTURE_HOTKEY(기본
# Ctrl+Shift+C)를 누르면 화면을 캡처해 세션을 만들고 브라우저 탭을 연다.

# 6) API 키 연결 후 real 모드로 전환 (백엔드 프로세스 기준)
setx ANTHROPIC_API_KEY "sk-ant-..."
# (새 터미널에서 uvicorn을 다시 시작하면 자동으로 real 모드로 전환됨)
```

일반 사용자에게 배포하는 `agent/local_agent.py`(또는 아래 설치 프로그램)는 환경변수를 따로
설정하지 않으면 `config.py`의 기본값 그대로 **실제 배포된 백엔드**(`https://unity-ai-assistant.onrender.com`)에
연결된다 — 이 경우가 기본 시나리오이고, 위 로컬 오버라이드는 개발 중에만 쓴다.

## 배포 (Docker)

`Dockerfile`은 React 빌드 산출물을 FastAPI가 정적으로 서빙하는 단일 이미지를 만든다
(프론트/백엔드가 같은 오리진이 되므로 운영 환경에서는 CORS 설정이 사실상 불필요하다).

```powershell
docker build -t unity-ai-assistant .
docker run -p 8000:8000 `
  -e ANTHROPIC_API_KEY=sk-ant-... `
  -e JWT_SECRET=<32바이트 이상의 랜덤 문자열> `
  -e FRONTEND_BASE_URL=https://<배포 도메인> `
  -e BACKEND_BASE_URL=https://<배포 도메인> `
  unity-ai-assistant
```

- 특정 PaaS(Render/Fly.io/Railway 등)는 지정하지 않았다 — 이 Dockerfile을 그대로 올리면 된다.
- 기본 DB는 컨테이너 내 SQLite 파일(`backend/data/app.db`)이다. 컨테이너 재생성 시 데이터가
  사라지므로, 영속 볼륨을 마운트하거나 `DATABASE_URL`로 외부 DB(Postgres 등)를 지정해야 한다.
- 로컬 캡처 에이전트(`agent/local_agent.py`)는 배포 대상이 아니라 각 개발자의 Windows
  머신에서 직접 실행하는 프로그램이다 — `BACKEND_BASE_URL` 환경변수로 배포된 백엔드를
  가리키도록 설정한다.

## Render에 실제 배포하기 (무료 티어 기준)

`render.yaml`(Blueprint)이 준비되어 있어 계정만 만들면 대부분 자동으로 설정된다. 계정 생성·
결제정보 등록·리포 연동 승인은 본인 확인이 필요한 단계라 직접 진행해야 한다.

1. **Render 가입**: https://render.com → "Get Started" → GitHub 계정으로 가입(추천, 리포 연동이
   자동으로 됨).
2. **New + → Blueprint** 선택 → 이 리포(`jihwanqp1o/unity-ai-assistant`)를 GitHub 연동 목록에서
   선택 (처음이면 Render GitHub App 설치/리포 접근 권한 승인 화면이 뜬다).
3. Render가 `render.yaml`을 읽어 서비스 구성을 자동으로 보여준다 — 이름/플랜 확인 후 "Apply".
4. 배포 중 `ANTHROPIC_API_KEY`를 입력하라는 칸이 뜬다 (`sync: false`라 리포에는 안 들어가고
   Render 대시보드에만 저장됨). 아직 키가 없으면 비워두고 mock 모드로 우선 배포해도 된다 —
   나중에 Render 대시보드 → Environment 탭에서 언제든 추가/변경 가능.
5. 첫 배포가 끝나면 `https://unity-ai-assistant.onrender.com` (이름이 이미 쓰였다면 Render가
   임의 접미사를 붙인 다른 주소)로 접속 가능해진다. **실제로 배정된 주소가 `render.yaml`의
   `FRONTEND_BASE_URL`/`BACKEND_BASE_URL`과 다르면** Environment 탭에서 두 값을 실제 주소로
   맞춰주고 "Manual Deploy" 재실행.
6. 로컬 캡처 에이전트를 쓰는 각 개발자 PC에서는 `python -m agent.local_agent`를 실행하거나(개발용),
   아래 "로컬 캡처 에이전트 설치 프로그램 만들기"로 만든 설치 파일을 나눠주면 된다(배포용) —
   `config.py`의 기본값이 이미 이 Render 주소를 가리키므로 환경변수 설정이 따로 필요 없다.

**무료 티어 특유의 제약** (알아두고 배포할 것):
- 무료 웹 서비스는 일정 시간 요청이 없으면 슬립되고, 다음 요청 때 첫 응답이 수십 초 걸릴 수 있음.
- 무료 티어는 영속 디스크를 지원하지 않아 **SQLite 파일이 재배포/재시작 시 초기화된다** — 계정과
  캡처 히스토리가 사라진다는 뜻. 데이터를 유지하려면 유료 플랜의 Persistent Disk를 추가하거나,
  `DATABASE_URL`을 Render의 무료 Postgres 애드온으로 바꾸는 것을 고려할 것.

## 로컬 캡처 에이전트 설치 프로그램 만들기

`agent/local_agent.py`는 이제 콘솔 창 대신 **시스템 트레이 아이콘**으로 동작한다(상태 텍스트,
"지금 캡처", "히스토리 열기", "종료" 메뉴 제공) — Python/venv 설치 없이 실행되는 배포용 설치
파일(`.exe`)을 만들 수 있다. 이전 PyQt5 시절의 PyInstaller 패키징과 같은 패턴이다.

**현재 배포된 다운로드**: 정식 Inno Setup 설치 프로그램은 아직 없고(로컬에 ISCC 컴파일러가
없어 만들지 못함), 대신 1단계 산출물(PyInstaller 단일 exe, 설치 과정 없이 바로 실행)을
GitHub Releases에 올려뒀다 — 웹앱의 "에이전트 다운로드" 버튼이 가리키는 주소:
`https://github.com/jihwanqp1o/unity-ai-assistant/releases/latest/download/UnityAIAssistantAgent.exe`.
새 버전을 릴리즈할 때는 같은 파일명으로 `gh release create <tag> dist/UnityAIAssistantAgent.exe`를
실행하면 `/latest/download/...` 링크가 자동으로 최신 릴리즈를 가리킨다.

```powershell
# 1) PyInstaller로 단일 실행파일 빌드 (agent_entry.py가 진입점 — repo 루트에 있어야
#    agent.*, core.*, config 절대 임포트가 프로즌 상태에서도 정상 동작한다)
pip install -r requirements.txt   # pyinstaller, pystray 포함
pyinstaller --onefile --windowed --name UnityAIAssistantAgent agent_entry.py
# 결과물: dist\UnityAIAssistantAgent.exe (Python 없이도 더블클릭으로 실행됨)

# 2) 정식 설치 프로그램으로 감싸기 (Inno Setup, 무료: https://jrsoftware.org/isinfo.php)
# Inno Setup 설치 후:
& "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe" installer\agent.iss
# 결과물: dist_installer\UnityAIAssistantAgentSetup.exe
```

- `installer/agent.iss`는 Program Files에 설치, 시작 메뉴 바로가기, "Windows 시작 시 자동 실행"
  선택 체크박스(기본 해제), 설치 후 바로 실행 옵션을 포함한다.
- 이 설치 파일을 받는 사용자는 환경변수를 하나도 몰라도 된다 — `config.py`의 기본 URL이
  이미 배포된 Render 주소를 가리키기 때문에, 실행 → 브라우저에서 로그인+기기 승인 → 핫키로
  바로 쓸 수 있다.
- 페어링 토큰은 `%APPDATA%\UnityAIAssistant\agent_config.json`에 저장된다 — 설치 프로그램
  제거 시에도 이 파일은 남겨둔다(재설치해도 다시 승인할 필요 없도록).

## 남은 작업 (원래 1주 일정 기준, Day 1~3은 이 세션에서 완료)

| 일자 | 상태 | 남은 작업 |
|---|---|---|
| Day 1 | 완료 | 프로젝트 구조, mock 파이프라인 구성 |
| Day 2 | 완료 | Unity 문서 스니펫 33개, 라이트 RAG 매칭 (100% 재현) |
| Day 3 | 완료 | 텍스트 질의 + RAG 결합 파이프라인 (mock 모드 검증) |
| Day 4 | 완료 (2026-07-11, Windows에서 검증) | overlay_window.py 창 렌더링·always-on-top 확인, hotkey.py 단축키 감지 확인 |
| Day 5 | 완료 (2026-07-11, Windows에서 검증) | capture.py 실제 화면 캡처 확인, main.py 통합 end-to-end 확인 |
| Day 6 | **보류 (API 크레딧 필요)** | ANTHROPIC_API_KEY 연결 후 `scripts\run_scenario_eval.py`를 real 모드로 재실행해 실제 LLM 코드 생성 품질 확인, 부족하면 시나리오/스니펫 보강 |
| Day 7 | 대기 | 데모 리허설, 필요 시 스니펫 추가 큐레이션 |

## 알려진 제약 (A2 개정 PRD 부록 E 참조)

- Vision API 비용·키 사전 확보 필요
- 원클릭 코드 적용은 클립보드 복사로 한정 (파일 자동 쓰기·Unity 프로젝트 직접 수정은 범위 밖)
- 라이트 RAG는 스니펫 20~40개 범위 내에서만 정확 — 데모 시나리오 밖 질문은 정확도가 떨어질 수 있음
- 기기 페어링 코드(`device_code`)에 만료 시간이 없음 — MVP 범위 결정, 운영 전환 시 TTL/재사용
  방지 추가 필요 (`backend/devices.py` 참고)
- 세션 스크린샷은 SQLite에 base64 텍스트로 저장 — 사용자·세션 수가 늘면 객체 스토리지(S3 등)로
  옮기는 것을 고려해야 함
