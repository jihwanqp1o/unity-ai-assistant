// core/../ui/overlay_window.py의 _CODE_BLOCK_RE / _STATUS_COLORS를 그대로 이식한 것.
// 코드 블록 추출 로직과 상태 문구→색상 매핑 규칙은 파이썬판과 1:1로 유지한다.

export const CODE_BLOCK_RE = /```(?:\w+)?\n([\s\S]*?)```/;

export function extractFirstCodeBlock(text) {
  const match = CODE_BLOCK_RE.exec(text || "");
  return match ? match[1].trim() : null;
}

export function stripFirstCodeBlock(text) {
  return (text || "").replace(CODE_BLOCK_RE, "📋 [코드 블록 — 아래 코드창 참고]");
}

const STATUS_COLORS = [
  ["대기", "#9aa0a6"],
  ["캡처 중", "#58a6ff"],
  ["캡처 완료", "#58a6ff"],
  ["캡처 실패", "#f85149"],
  ["분석 중", "#d29922"],
  ["분석 완료", "#3fb950"],
  ["복사되었습니다", "#3fb950"],
  ["실패", "#f85149"],
];

export function statusColor(text) {
  for (const [key, color] of STATUS_COLORS) {
    if ((text || "").includes(key)) return color;
  }
  return "#9aa0a6";
}
