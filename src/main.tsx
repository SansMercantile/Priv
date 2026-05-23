import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App.tsx";
import { EnvironmentProvider } from "./context/EnvironmentContext";
import "./index.css";

declare global {
  interface Window {
    ENV?: { DEMO_MODE?: boolean };
  }
}
if (typeof window !== "undefined" && !window.ENV) {
  window.ENV = {};
}

// Intercept and absorb unpreventable cross-origin iframe and script error events
if (typeof window !== "undefined") {
  window.addEventListener("error", (event) => {
    const message = event.message || "";
    if (
      message.includes("Script error") ||
      message.includes("contentWindow") ||
      message.includes("iframe") ||
      message.includes("cross-origin") ||
      !event.filename
    ) {
      event.preventDefault();
      event.stopPropagation();
      console.warn("Absorbed and suppressed third-party sandbox iframe/script warning:", message);
    }
  }, true);

  window.addEventListener("unhandledrejection", (event) => {
    const reason = event.reason;
    const message = reason && reason.message ? reason.message : String(reason);
    if (
      message.includes("contentWindow") ||
      message.includes("iframe") ||
      message.includes("cross-origin")
    ) {
      event.preventDefault();
      event.stopPropagation();
      console.warn("Absorbed third-party unhandled rejection:", message);
    }
  }, true);
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <EnvironmentProvider>
        <App />
      </EnvironmentProvider>
    </BrowserRouter>
  </StrictMode>
);
