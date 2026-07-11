from core.prompt_builder import build_messages, build_user_content, build_system_prompt


def test_system_prompt_mentions_unity_and_rules():
    sp = build_system_prompt()
    assert "Unity" in sp
    assert len(sp) > 50


def test_build_messages_basic_structure():
    msgs = build_messages(user_question="테스트 질문", rag_context="테스트 컨텍스트")
    assert isinstance(msgs, list)
    assert len(msgs) == 1
    assert msgs[0]["role"] == "user"
    assert isinstance(msgs[0]["content"], list)


def test_image_block_appears_before_text_block():
    content = build_user_content(
        user_question="q",
        rag_context="ctx",
        screenshot_b64="ZmFrZWJhc2U2NA==",
    )
    types = [b["type"] for b in content]
    assert types[0] == "image"
    assert "text" in types


def test_no_image_means_only_text_block():
    content = build_user_content(user_question="q", rag_context="ctx")
    types = [b["type"] for b in content]
    assert types == ["text"]


def test_code_paste_included_in_text():
    content = build_user_content(
        user_question="q",
        rag_context="ctx",
        code_paste="void Update() {}",
    )
    text_block = next(b for b in content if b["type"] == "text")
    assert "void Update" in text_block["text"]
    assert "붙여넣은 코드" in text_block["text"]
