import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

export default function HistoryPage() {
  const [sessions, setSessions] = useState([]);

  useEffect(() => {
    api.listSessions().then(setSessions).catch(() => {});
  }, []);

  return (
    <div className="app-shell">
      <h2>캡처 히스토리</h2>
      {sessions.length === 0 && (
        <p style={{ color: "#9aa0a6" }}>
          아직 캡처된 세션이 없습니다. 로컬 캡처 에이전트에서 핫키로 캡처해보세요.
        </p>
      )}
      <ul className="session-list">
        {sessions.map((s) => (
          <li key={s.id}>
            <Link to={`/app/session/${s.id}`}>
              {s.id.slice(0, 8)} — {s.question ? s.question.slice(0, 40) : "(질문 없음)"} [{s.status}]
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
