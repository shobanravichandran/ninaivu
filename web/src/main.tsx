import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import Landing from "./landing/Landing";
import "./styles.css";

// Two pages, no router: the story at /, the working console at /app (Vercel rewrites both to index.html).
const isApp = window.location.pathname.startsWith("/app");

createRoot(document.getElementById("root")!).render(<StrictMode>{isApp ? <App /> : <Landing />}</StrictMode>);
