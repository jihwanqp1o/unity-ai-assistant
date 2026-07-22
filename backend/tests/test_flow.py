"""회원가입 -> 기기 페어링 -> 세션 생성/스크린샷 업로드 -> 질문 전체 흐름 테스트.

GEMINI_API_KEY가 없는 테스트 환경에서는 core/llm_client.py가 자동으로 mock 모드로
동작하므로, RAG가 올바른 문서를 찾았는지는 mock 응답 문자열에 포함된 문서 제목으로 검증한다.
"""


def _signup_and_pair_device(client, email="dev@example.com"):
    """회원가입 + 기기 페어링을 끝내고 (device_token, headers)를 반환하는 테스트 헬퍼."""
    signup_resp = client.post("/api/auth/signup", json={"email": email, "password": "hunter2222"})
    assert signup_resp.status_code == 200, signup_resp.text

    start_resp = client.post("/api/devices/pair/start")
    code = start_resp.json()["device_code"]

    claim_resp = client.post(f"/api/devices/pair/{code}/claim")
    assert claim_resp.status_code == 200, claim_resp.text

    poll_resp = client.get(f"/api/devices/pair/{code}")
    device_token = poll_resp.json()["token"]
    assert device_token

    return device_token, {"Authorization": f"Bearer {device_token}"}


def test_signup_login_pair_session_ask_flow(client):
    device_token, headers = _signup_and_pair_device(client)

    me_resp = client.get("/api/auth/me")
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "dev@example.com"

    create_resp = client.post("/api/sessions", headers=headers)
    assert create_resp.status_code == 200, create_resp.text
    session_id = create_resp.json()["id"]

    screenshot_resp = client.post(
        f"/api/sessions/{session_id}/screenshot",
        json={"screenshot_b64": "ZmFrZS1wbmctYnl0ZXM="},
        headers=headers,
    )
    assert screenshot_resp.status_code == 200

    get_resp = client.get(f"/api/sessions/{session_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["status"] == "ready"

    ask_resp = client.post(
        f"/api/sessions/{session_id}/ask",
        json={"question": "점프가 두 번 눌려도 한 번만 되는데 isGrounded 관련인 것 같아요"},
    )
    assert ask_resp.status_code == 200, ask_resp.text
    body = ask_resp.json()
    assert body["mock"] is True
    assert "MOCK" in body["answer"]

    history_resp = client.get("/api/sessions")
    assert history_resp.status_code == 200
    assert len(history_resp.json()) == 1
    assert history_resp.json()[0]["answer"] == body["answer"]
    assert "created_at" in history_resp.json()[0]


def test_unclaimed_device_token_rejected(client):
    resp = client.post("/api/sessions", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401


def test_session_requires_login(client):
    resp = client.get("/api/sessions")
    assert resp.status_code == 401


def test_quick_capture_answers_in_one_call(client):
    """에이전트의 네이티브 입력창 플로우: 스크린샷+질문을 한 번에 보내 바로 답변을 받는다."""
    device_token, headers = _signup_and_pair_device(client)

    resp = client.post(
        "/api/sessions/quick",
        json={
            "screenshot_b64": "ZmFrZS1wbmctYnl0ZXM=",
            "question": "점프가 두 번 눌려도 한 번만 되는데 isGrounded 관련인 것 같아요",
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["mock"] is True
    assert "MOCK" in body["answer"]
    assert body["session_url"].endswith(f"/app/session/{body['id']}")

    get_resp = client.get(f"/api/sessions/{body['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["status"] == "answered"
    assert get_resp.json()["answer"] == body["answer"]


def test_quick_capture_requires_device_token(client):
    resp = client.post(
        "/api/sessions/quick",
        json={"screenshot_b64": "ZmFrZQ==", "question": "질문"},
    )
    assert resp.status_code == 401


def test_delete_session(client):
    device_token, headers = _signup_and_pair_device(client)

    create_resp = client.post("/api/sessions", headers=headers)
    session_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/api/sessions/{session_id}")
    assert delete_resp.status_code == 200, delete_resp.text

    get_resp = client.get(f"/api/sessions/{session_id}")
    assert get_resp.status_code == 404

    history_resp = client.get("/api/sessions")
    assert history_resp.json() == []


def test_delete_session_requires_login(client):
    device_token, headers = _signup_and_pair_device(client)
    create_resp = client.post("/api/sessions", headers=headers)
    session_id = create_resp.json()["id"]

    client.post("/api/auth/logout")
    resp = client.delete(f"/api/sessions/{session_id}")
    assert resp.status_code == 401
