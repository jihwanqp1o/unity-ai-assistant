"""
agent/quick_dialog.py
------------------------
캡처 직후 Unity 위에 곧바로 띄우는 작은 질문 입력창.

표준 라이브러리 tkinter만 쓴다(추가 의존성 없음, PyInstaller 번들에도 항상 포함됨).
목적: 캡처 → 브라우저 전환 → 질문 입력 → 다시 브라우저 확인으로 이어지던 흐름에서
"브라우저로 전환해 질문 입력"을 없애기 위함 — 여기서 질문을 받아 백엔드에 스크린샷과
함께 바로 보내고, 브라우저는 이미 완성된 답변을 보여주는 용도로만 연다
(agent/local_agent.py의 on_capture 참고).
"""
from __future__ import annotations

from typing import Optional


def ask_question() -> Optional[str]:
    """작은 입력창을 띄우고, 사용자가 입력해 전송한 텍스트를 반환한다.
    취소하거나 빈 채로 닫으면 None을 반환한다 (호출부는 이 경우 기존 방식대로
    스크린샷만 올리고 브라우저에서 질문을 입력받는 흐름으로 넘어간다)."""
    import tkinter as tk

    result: dict = {"value": None}

    root = tk.Tk()
    root.title("Unity AI Assistant")
    root.attributes("-topmost", True)
    root.resizable(False, False)
    root.configure(bg="#1e1f22")

    tk.Label(
        root,
        text="무엇이 궁금하세요? (Ctrl+Enter로 전송, Esc로 취소)",
        bg="#1e1f22",
        fg="#e6e6e6",
        padx=12,
        pady=8,
    ).pack(anchor="w")

    text = tk.Text(
        root,
        width=64,
        height=6,
        bg="#26282c",
        fg="#e6e6e6",
        insertbackground="#e6e6e6",
        relief="flat",
        highlightthickness=1,
        highlightbackground="#3f4147",
        highlightcolor="#3fb950",
    )
    text.pack(padx=12, pady=(0, 8))
    text.focus_set()

    def submit(event=None):
        result["value"] = text.get("1.0", "end").strip()
        root.destroy()

    def cancel(event=None):
        result["value"] = None
        root.destroy()

    button_row = tk.Frame(root, bg="#1e1f22")
    button_row.pack(fill="x", padx=12, pady=(0, 12))
    tk.Button(button_row, text="취소", command=cancel).pack(side="right", padx=(6, 0))
    tk.Button(button_row, text="전송", command=submit).pack(side="right")

    text.bind("<Control-Return>", submit)
    root.bind("<Escape>", cancel)
    root.protocol("WM_DELETE_WINDOW", cancel)

    # 화면 중앙보다 살짝 위쪽에 띄운다 (Unity 창을 너무 많이 가리지 않도록)
    root.update_idletasks()
    w, h = root.winfo_width(), root.winfo_height()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"+{(sw - w) // 2}+{(sh - h) // 3}")

    root.mainloop()
    return result["value"] or None
