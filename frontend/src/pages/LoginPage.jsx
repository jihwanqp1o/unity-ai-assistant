import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../api";

export default function LoginPage({ onAuthed }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const next = params.get("next") || "/app/history";

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    try {
      const user = await api.login(email, password);
      onAuthed(user);
      navigate(next);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <form className="form-card" onSubmit={handleSubmit}>
      <h2>로그인</h2>
      <input
        type="email"
        placeholder="이메일"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
      />
      <input
        type="password"
        placeholder="비밀번호"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />
      {error && <div className="error-text">{error}</div>}
      <button type="submit">로그인</button>
      <div>
        계정이 없으신가요? <Link to={`/signup?next=${encodeURIComponent(next)}`}>회원가입</Link>
      </div>
    </form>
  );
}
