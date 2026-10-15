import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In the Base44 sandbox preview the frontend is served on one public origin and proxies
// its API calls to the backend service, so the browser never makes a cross-origin request.
// That setup sets VITE_API_BASE_URL to an empty string, which makes the app call /api on
// its own origin. Outside the sandbox this proxy is not registered and the app keeps using
// the absolute VITE_API_BASE_URL from the environment (default http://localhost:8080).
const sandboxApiProxy =
  process.env.BASE44_PREVIEW_MODE === "1"
    ? {
        "/api": {
          target: process.env.VITE_API_PROXY_TARGET ?? "http://localhost:8080",
          changeOrigin: true,
        },
      }
    : undefined;

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: sandboxApiProxy,
  },
});
