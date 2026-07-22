import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../api";

export default function PairPage({ user }) {
  const [params] = useSearchParams();
  const code = params.get("code") || "";
  const [claimed, setClaimed] = useState(false);
  const [error, setError] = useState(null);

  async function handleApprove() {
    setError(null);
    try {
      await api.claimDevice(code);
      setClaimed(true);
    } catch (err) {
      setError(err.message);
    }
  }

  if (!user) {
    return (
      <div className="form-card">
        <p>기기를 승인하려면 먼저 로그인해야 합니다.</p>
        <Link to={`/login?next=${encodeURIComponent(`/pair?code=${code}`)}`}>로그인 하러 가기</Link>
      </div>
    );
  }

  return (
    <div className="form-card">
      <h2>새 캡처 에이전트 승인</h2>
      <p>
        페어링 코드: <b>{code}</b>
      </p>
      {claimed ? (
        <p style={{ color: "#3fb950" }}>승인 완료! 에이전트로 돌아가세요.</p>
      ) : (
        <button onClick={handleApprove}>이 기기 승인</button>
      )}
      {error && <div className="error-text">{error}</div>}
    </div>
  );
}
