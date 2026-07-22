import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../api";

export default function SignupPage({ onAuthed }) {
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
      const user = await api.signup(email, password);
      onAuthed(user);
      navigate(next);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <form className="form-card" onSubmit={handleSubmit}>
      <h2>회원가입</h2>
      <input
        type="email"
        placeholder="이메일"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
      />
      <input
        type="password"
        placeholder="비밀번호 (8자 이상)"
        minLength={8}
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />
      {error && <div className="error-text">{error}</div>}
      <button type="submit">가입하기</button>
      <div>
        이미 계정이 있으신가요? <Link to={`/login?next=${encodeURIComponent(next)}`}>로그인</Link>
      </div>
    </form>
  );
}
