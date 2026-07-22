import { extractFirstCodeBlock, stripFirstCodeBlock } from "../lib/codeBlock";

export default function ChatLog({ messages }) {
  return (
    <div className="chat-log">
      <div className="chat-message" style={{ fontStyle: "italic", color: "#9aa0a6" }}>
        👋 <b>사용법</b>
        <br />
        위 스크린샷을 참고해 궁금한 점을 아래에 적고 전송을 누르세요. AI가 Unity 공식 문서를
        근거로 답변하고, 코드가 있으면 아래 코드창에 표시됩니다.
      </div>
      {messages.map((m, i) => {
        if (m.role === "user") {
          return (
            <div className="chat-message" key={i}>
              <div className="who">나</div>
              <div>{m.text}</div>
            </div>
          );
        }
        const code = extractFirstCodeBlock(m.text);
        const display = code ? stripFirstCodeBlock(m.text) : m.text;
        return (
          <div className="chat-message" key={i}>
            <div className="who ai">AI</div>
            <div>{display}</div>
          </div>
        );
      })}
    </div>
  );
}
