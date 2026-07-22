import { useEffect, useState } from "react";
import { Link, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { api } from "./api";
import HelpPage from "./pages/HelpPage";
import HistoryPage from "./pages/HistoryPage";
import LoginPage from "./pages/LoginPage";
import PairPage from "./pages/PairPage";
import SessionPage from "./pages/SessionPage";
import SignupPage from "./pages/SignupPage";

export default function App() {
  const [user, setUser] = useState(undefined); // undefined = 로딩 중, null = 로그아웃 상태
  const navigate = useNavigate();

  useEffect(() => {
    api
      .me()
      .then(setUser)
      .catch(() => setUser(null));
  }, []);

  async function handleLogout() {
    await api.logout();
    setUser(null);
    navigate("/login");
  }

  if (user === undefined) {
    return <div className="app-shell">불러오는 중...</div>;
  }

  return (
    <>
      <nav className="top-row" style={{ padding: "10px 16px", borderBottom: "1px solid #3f4147" }}>
        <Link to="/app/history">Unity AI Assistant</Link>
        <Link to="/help">도움말</Link>
        <span style={{ marginLeft: "auto" }}>
          {user ? (
            <>
              {user.email} · <button onClick={handleLogout}>로그아웃</button>
            </>
          ) : (
            <Link to="/login">로그인</Link>
          )}
        </span>
      </nav>
      <Routes>
        <Route path="/login" element={<LoginPage onAuthed={setUser} />} />
        <Route path="/signup" element={<SignupPage onAuthed={setUser} />} />
        <Route path="/pair" element={<PairPage user={user} />} />
        <Route path="/help" element={<HelpPage />} />
        <Route path="/app/session/:id" element={user ? <SessionPage /> : <Navigate to="/login" />} />
        <Route path="/app/history" element={user ? <HistoryPage /> : <Navigate to="/login" />} />
        <Route path="*" element={<Navigate to={user ? "/app/history" : "/login"} />} />
      </Routes>
    </>
  );
}
