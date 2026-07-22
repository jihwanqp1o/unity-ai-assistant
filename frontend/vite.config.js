import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 개발 모드에서 /api 요청을 배포된(또는 로컬) FastAPI 백엔드로 프록시한다.
// 같은 오리진처럼 보이게 해서 쿠키 기반 로그인 세션이 CORS 문제 없이 동작한다.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: process.env.BACKEND_BASE_URL || "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
