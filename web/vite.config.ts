import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In dev, /api goes to the local FastAPI server. On Vercel, web/vercel.json rewrites /api to the API project.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { "/api": "http://localhost:8000" },
  },
});
