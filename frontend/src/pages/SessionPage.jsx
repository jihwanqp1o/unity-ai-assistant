import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import ChatLog from "../components/ChatLog";
import CodePanel from "../components/CodePanel";
import StatusBadge from "../components/StatusBadge";
import { extractFirstCodeBlock } from "../lib/codeBlock";
import { formatDateTime } from "../lib/format";

export default function SessionPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [session, setSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [status, setStatus] = useState("대기 중");
  const [code, setCode] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api
      .getSession(id)
      .then((s) => {
        setSession(s);
        if (s.question) {
          const msgs = [{ role: "user", text: s.question }];
          if (s.answer) msgs.push({ role: "ai", text: s.answer });
          setMessages(msgs);
          if (s.answer) {
            const c = extractFirstCodeBlock(s.answer);
            if (c) setCode(c);
          }
        }
        setStatus(s.screenshot_b64 ? "캡처 완료" : "대기 중");
      })
      .catch((err) => setError(err.message));
  }, [id]);

  async function handleSend(e) {
    e.preventDefault();
    const q = question.trim();
    if (!q) return;
    setQuestion("");
    setMessages((prev) => [...prev, { role: "user", text: q }]);
    setStatus("분석 중");
    try {
      const res = await api.ask(id, q);
      setMessages((prev) => [...prev, { role: "ai", text: res.answer }]);
      const c = extractFirstCodeBlock(res.answer);
      if (c) setCode(c);
      setStatus(res.mock ? "분석 완료 (MOCK 모드)" : "분석 완료");
    } catch (err) {
      setStatus(`실패: ${err.message}`);
    }
  }

  function handleCopy() {
    if (!code) return;
    navigator.clipboard.writeText(code);
    setStatus("코드가 클립보드에 복사되었습니다");
  }

  async function handleDelete() {
    if (!window.confirm("이 캡처 기록을 삭제할까요? 되돌릴 수 없어요.")) return;
    try {
      await api.deleteSession(id);
      navigate("/app/history");
    } catch (err) {
      alert(err.message);
    }
  }

  if (error) return <div className="app-shell error-text">{error}</div>;
  if (!session) return <div className="app-shell">불러오는 중...</div>;

  return (
    <div className="app-shell">
      <div className="top-row">
        <span className="section-label">{formatDateTime(session.created_at)} 캡처</span>
        <StatusBadge text={status} />
        <button onClick={handleDelete}>🗑 삭제</button>
      </div>
      {session.screenshot_b64 && (
        <img
          className="screenshot-preview"
          src={`data:image/png;base64,${session.screenshot_b64}`}
          alt="캡처된 Unity 에디터 화면"
        />
      )}
      <ChatLog messages={messages} />
      <CodePanel code={code} onCopy={handleCopy} />
      <form className="bottom-row" onSubmit={handleSend}>
        <input
          placeholder="질문하거나 코드를 붙여넣으세요..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <button type="submit">전송 ▶</button>
      </form>
    </div>
  );
}
