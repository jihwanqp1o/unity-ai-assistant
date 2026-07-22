import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import AgentOnboarding from "../components/AgentOnboarding";

export default function HistoryPage() {
  const [sessions, setSessions] = useState([]);

  useEffect(() => {
    api.listSessions().then(setSessions).catch(() => {});
  }, []);

  return (
    <div className="app-shell">
      <h2>캡처 히스토리</h2>
      {sessions.length === 0 && <AgentOnboarding />}
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
