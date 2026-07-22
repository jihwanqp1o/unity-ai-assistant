const BASE = "/api";

async function request(path, options = {}) {
  const resp = await fetch(`${BASE}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    throw new Error(body.detail || `요청 실패 (${resp.status})`);
  }
  if (resp.status === 204) return null;
  return resp.json();
}

export const api = {
  signup: (email, password) =>
    request("/auth/signup", { method: "POST", body: JSON.stringify({ email, password }) }),
  login: (email, password) =>
    request("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  logout: () => request("/auth/logout", { method: "POST" }),
  me: () => request("/auth/me"),
  claimDevice: (code) => request(`/devices/pair/${code}/claim`, { method: "POST" }),
  getSession: (id) => request(`/sessions/${id}`),
  listSessions: () => request("/sessions"),
  ask: (id, question, codePaste) =>
    request(`/sessions/${id}/ask`, {
      method: "POST",
      body: JSON.stringify({ question, code_paste: codePaste || null }),
    }),
};
