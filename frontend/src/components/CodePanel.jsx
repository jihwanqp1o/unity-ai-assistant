export default function CodePanel({ code, onCopy }) {
  return (
    <>
      <div className="code-row">
        <span className="section-label">마지막 제안 코드</span>
        <div style={{ marginLeft: "auto" }}>
          <button disabled={!code} onClick={onCopy}>
            📋 원클릭 적용 (클립보드 복사)
          </button>
        </div>
      </div>
      <div className="code-panel">{code || ""}</div>
    </>
  );
}
