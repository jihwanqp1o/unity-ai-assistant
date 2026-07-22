import AgentOnboarding from "../components/AgentOnboarding";

export default function HelpPage() {
  return (
    <div className="app-shell">
      <h2>사용법</h2>

      <AgentOnboarding />

      <div className="onboarding-card">
        <h3>매번 캡처할 때 (에이전트 설치 후)</h3>
        <ol className="onboarding-steps">
          <li>
            Unity 에디터에서 화면을 캡처하고 싶을 때 <b>Ctrl+Shift+C</b>를 누르거나, 트레이
            아이콘 메뉴에서 "지금 캡처"를 클릭하세요
          </li>
          <li>기본 브라우저에 새 탭이 자동으로 열리고, 방금 캡처한 화면이 보여요</li>
          <li>화면 아래 입력창에 궁금한 점(에러 내용, 코드 등)을 적고 전송하세요</li>
          <li>
            AI가 Unity 공식 문서를 근거로 답변합니다 — 코드가 포함되어 있으면 아래 코드창의
            "원클릭 적용" 버튼으로 클립보드에 복사할 수 있어요
          </li>
          <li>지난 캡처 내역은 언제든 상단의 "Unity AI Assistant" 링크(히스토리)에서 다시 볼 수 있어요</li>
        </ol>
      </div>

      <div className="onboarding-card">
        <h3>답변이 이상하게 짧거나 "[MOCK 응답 ...]"으로 시작해요</h3>
        <p style={{ color: "#9aa0a6" }}>
          아직 서버에 Gemini API 키가 연결되지 않은 상태입니다 — 이 경우 실제 AI 분석 대신
          파이프라인 연결만 확인하는 가짜(mock) 응답이 나옵니다. 관리자가 Render 대시보드의
          Environment 탭에서 <code>GEMINI_API_KEY</code>를 등록하면 해결됩니다.
        </p>
      </div>
    </div>
  );
}
