# Unity AI Assistant (1주 MVP) — VSCode 이어작업 가이드

개정 PRD(아산AX_개인PRD_4조_지환_개정판) 기준 구현. Unity 단일 엔진 · 온디맨드 스크린샷 ·
라이트 RAG 기반 코드 어시스턴트.

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
├── main.py                  # 엔트리포인트 (RAG+캡처+단축키+오버레이 배선)
├── config.py                 # 환경변수 기반 설정 (API 키, 단축키 등)
├── requirements.txt
├── core/
│   ├── rag.py                # 라이트 RAG (키워드 매칭, 외부 의존성 없음)
│   ├── prompt_builder.py      # 프롬프트 조립 (외부 의존성 없음)
│   ├── claude_client.py       # Claude API 래퍼 (real/mock)
│   ├── capture.py             # 화면 캡처 (mss)
│   └── hotkey.py               # 전역 단축키 (keyboard)
├── ui/
│   └── overlay_window.py      # PyQt5 오버레이 창
├── data/
│   ├── unity_snippets.json    # Unity 공식 문서 스니펫 33개
│   └── test_scenarios.json    # 대표 에러 시나리오 8건 (Q6 성공지표 측정용)
├── scripts/
│   └── run_scenario_eval.py   # Q6 성공지표 자동 측정 스크립트
└── tests/
    ├── test_rag.py
    ├── test_prompt_builder.py
    └── test_claude_client_mock.py
```

## VSCode에서 시작하기 (Windows)

```powershell
cd unity-ai-assistant
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 1) 먼저 mock 모드로 파이프라인 자체가 도는지 확인 (API 키 불필요)
python scripts\run_scenario_eval.py

# 2) 단위 테스트
pytest tests\ -v

# 3) API 키 연결 후 real 모드로 전환
setx ANTHROPIC_API_KEY "sk-ant-..."
# (새 터미널에서) 다시 실행하면 자동으로 real 모드로 전환됨
python scripts\run_scenario_eval.py

# 4) 전체 앱 실행 (PyQt 창 + 전역 단축키 + 실제 캡처)
python main.py
```

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
- PyQt always-on-top·투명도는 OS별 동작 차이 존재 (Windows 기준 검증 필요)
- 원클릭 코드 적용은 클립보드 복사로 한정 (파일 자동 쓰기·Unity 프로젝트 직접 수정은 범위 밖)
- 라이트 RAG는 스니펫 20~40개 범위 내에서만 정확 — 데모 시나리오 밖 질문은 정확도가 떨어질 수 있음
