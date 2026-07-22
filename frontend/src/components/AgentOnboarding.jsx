const AGENT_DOWNLOAD_URL =
  "https://github.com/jihwanqp1o/unity-ai-assistant/releases/latest/download/UnityAIAssistantAgent.exe";

export default function AgentOnboarding() {
  return (
    <div className="onboarding-card">
      <h3>시작하기 전에: 로컬 캡처 에이전트 설치</h3>
      <p style={{ color: "#9aa0a6" }}>
        Unity 에디터 화면을 캡처하려면 이 컴퓨터에 작은 캡처 프로그램을 설치해야 해요 —
        브라우저만으로는 화면 캡처나 전역 단축키가 동작하지 않습니다.
      </p>
      <a href={AGENT_DOWNLOAD_URL}>
        <button type="button">⬇ 에이전트 다운로드 (Windows)</button>
      </a>
      <ol className="onboarding-steps">
        <li>
          다운로드한 <code>UnityAIAssistantAgent.exe</code>를 실행하세요 (트레이 아이콘이 떠요)
        </li>
        <li>자동으로 열리는 브라우저에서 로그인 후 "이 기기 승인"을 눌러주세요</li>
        <li>
          승인되면 Unity 에디터에서 <b>Ctrl+Shift+C</b>를 눌러 화면을 캡처하세요 — 이 페이지가
          자동으로 뜹니다
        </li>
      </ol>
    </div>
  );
}
