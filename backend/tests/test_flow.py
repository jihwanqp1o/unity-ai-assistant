"""회원가입 -> 기기 페어링 -> 세션 생성/스크린샷 업로드 -> 질문 전체 흐름 테스트.

ANTHROPIC_API_KEY가 없는 테스트 환경에서는 core/claude_client.py가 자동으로 mock 모드로
동작하므로, RAG가 올바른 문서를 찾았는지는 mock 응답 문자열에 포함된 문서 제목으로 검증한다.
"""


def test_signup_login_pair_session_ask_flow(client):
    signup_resp = client.post(
        "/api/auth/signup", json={"email": "dev@example.com", "password": "hunter2222"}
    )
    assert signup_resp.status_code == 200, signup_resp.text

    me_resp = client.get("/api/auth/me")
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "dev@example.com"

    start_resp = client.post("/api/devices/pair/start")
    assert start_resp.status_code == 200, start_resp.text
    code = start_resp.json()["device_code"]

    pending_resp = client.get(f"/api/devices/pair/{code}")
    assert pending_resp.json()["status"] == "pending"

    claim_resp = client.post(f"/api/devices/pair/{code}/claim")
    assert claim_resp.status_code == 200, claim_resp.text

    poll_resp = client.get(f"/api/devices/pair/{code}")
    assert poll_resp.status_code == 200
    poll_body = poll_resp.json()
    assert poll_body["status"] == "claimed"
    device_token = poll_body["token"]
    assert device_token

    headers = {"Authorization": f"Bearer {device_token}"}
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


def test_unclaimed_device_token_rejected(client):
    resp = client.post("/api/sessions", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401


def test_session_requires_login(client):
    resp = client.get("/api/sessions")
    assert resp.status_code == 401
