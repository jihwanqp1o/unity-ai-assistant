import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import AgentOnboarding from "../components/AgentOnboarding";
import { formatDateTime } from "../lib/format";

const STATUS_LABELS = {
  capturing: { text: "캡처 중", color: "#58a6ff" },
  ready: { text: "답변 대기", color: "#d29922" },
  answered: { text: "답변 완료", color: "#3fb950" },
};

export default function HistoryPage() {
  const [sessions, setSessions] = useState(null); // null = 아직 안 불러옴 (빈 목록과 구분)

  useEffect(() => {
    api
      .listSessions()
      .then(setSessions)
      .catch(() => setSessions([]));
  }, []);

  async function handleDelete(id) {
    if (!window.confirm("이 캡처 기록을 삭제할까요? 되돌릴 수 없어요.")) return;
    try {
      await api.deleteSession(id);
      setSessions((prev) => prev.filter((s) => s.id !== id));
    } catch (err) {
      alert(err.message);
    }
  }

  if (sessions === null) {
    return (
      <div className="app-shell">
        <h2>캡처 히스토리</h2>
        <p style={{ color: "#9aa0a6" }}>불러오는 중...</p>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <h2>캡처 히스토리</h2>
      {sessions.length === 0 && <AgentOnboarding />}
      <ul className="session-list">
        {sessions.map((s) => {
          const status = STATUS_LABELS[s.status] || { text: s.status, color: "#9aa0a6" };
          return (
            <li key={s.id}>
              <Link to={`/app/session/${s.id}`} className="session-item">
                {s.screenshot_b64 ? (
                  <img
                    className="session-thumb"
                    src={`data:image/png;base64,${s.screenshot_b64}`}
                    alt="캡처된 화면 미리보기"
                  />
                ) : (
                  <div className="session-thumb session-thumb-empty" />
                )}
                <div className="session-item-body">
                  <div className="session-item-top">
                    <span className="session-time">{formatDateTime(s.created_at)}</span>
                    <span className="session-status" style={{ color: status.color }}>
                      ● {status.text}
                    </span>
                  </div>
                  <div className="session-question">
                    {s.question || <span style={{ color: "#9aa0a6" }}>아직 질문을 남기지 않았어요</span>}
                  </div>
                </div>
              </Link>
              <button
                className="session-delete-btn"
                onClick={() => handleDelete(s.id)}
                title="삭제"
                aria-label="삭제"
              >
                🗑
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
