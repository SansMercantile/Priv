import "./shims.ts";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App.tsx";
import "./index.css";

// Intercept and absorb unpreventable cross-origin iframe and script error events
if (typeof window !== "undefined") {
  // Override console.error to filter out third-party iframe errors and noisy script warnings
  const originalConsoleError = console.error;
  console.error = function (...args: any[]) {
    const message = args
      .map((arg) => {
        try {
          return typeof arg === "object" ? (arg?.message || JSON.stringify(arg)) : String(arg);
        } catch (e) {
          return String(arg);
        }
      })
      .join(" ");

    const msgLower = message.toLowerCase();
    if (
      msgLower.includes("script error") ||
      msgLower.includes("contentwindow") ||
      msgLower.includes("iframe") ||
      msgLower.includes("cross-origin") ||
      msgLower.includes("cannot listen to the event") ||
      msgLower.includes("targetorigin") ||
      msgLower.includes("permission denied")
    ) {
      // Quietly absorb
      return;
    }
    originalConsoleError.apply(console, args);
  };

  // Override console.warn to filter out third-party iframe and scripts warnings
  const originalConsoleWarn = console.warn;
  console.warn = function (...args: any[]) {
    const message = args
      .map((arg) => {
        try {
          return typeof arg === "object" ? (arg?.message || JSON.stringify(arg)) : String(arg);
        } catch (e) {
          return String(arg);
        }
      })
      .join(" ");

    const msgLower = message.toLowerCase();
    if (
      msgLower.includes("script error") ||
      msgLower.includes("contentwindow") ||
      msgLower.includes("iframe") ||
      msgLower.includes("cross-origin") ||
      msgLower.includes("cannot listen to the event") ||
      msgLower.includes("targetorigin") ||
      msgLower.includes("permission denied")
    ) {
      // Quietly absorb
      return;
    }
    originalConsoleWarn.apply(console, args);
  };

  // Error event listener with preventDefault and stopPropagation
  window.addEventListener("error", (event) => {
    const message = event.message || "";
    const msgLower = message.toLowerCase();
    if (
      msgLower.includes("script error") ||
      msgLower.includes("contentwindow") ||
      msgLower.includes("iframe") ||
      msgLower.includes("cross-origin") ||
      msgLower.includes("cannot listen to the event") ||
      msgLower.includes("targetorigin") ||
      msgLower.includes("permission denied") ||
      !event.filename
    ) {
      event.preventDefault();
      event.stopPropagation();
    }
  }, true);

  // Directly assign window.onerror as fallback interface for total suppression
  window.onerror = function (message, source, lineno, colno, error) {
    const msgStr = String(message || "");
    const msgLower = msgStr.toLowerCase();
    if (
      msgLower.includes("script error") ||
      msgLower.includes("contentwindow") ||
      msgLower.includes("iframe") ||
      msgLower.includes("cross-origin") ||
      msgLower.includes("cannot listen to the event") ||
      msgLower.includes("targetorigin") ||
      msgLower.includes("permission denied") ||
      !source
    ) {
      return true; // Suppress standard browser handler
    }
    return false;
  };

  // Unhandled promise rejection listener
  window.addEventListener("unhandledrejection", (event) => {
    const reason = event.reason;
    const message = reason && reason.message ? reason.message : String(reason);
    const msgLower = message.toLowerCase();
    if (
      msgLower.includes("script error") ||
      msgLower.includes("contentwindow") ||
      msgLower.includes("iframe") ||
      msgLower.includes("cross-origin") ||
      msgLower.includes("cannot listen to the event") ||
      msgLower.includes("targetorigin") ||
      msgLower.includes("permission denied")
    ) {
      event.preventDefault();
      event.stopPropagation();
    }
  }, true);
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>
);
