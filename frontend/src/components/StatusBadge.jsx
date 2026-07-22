import { statusColor } from "../lib/codeBlock";

export default function StatusBadge({ text }) {
  return (
    <span className="status-label" style={{ color: statusColor(text) }}>
      ● {text}
    </span>
  );
}
