import "./shims.ts";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import AuthRoot from "./AuthRoot.tsx";
import "./index.css";

if (import.meta.env.PROD && "serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch((error) => {
      console.warn("Priv Core offline shell could not be registered:", error);
    });
  });
}

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
    // Pass a control-char-stripped copy so a tainted message can't forge
    // extra log lines (CR/LF log injection).
    originalConsoleWarn(message.replace(/[\r\n\u0000-\u001F\u007F]+/g, " "));
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
    <AuthRoot />
  </StrictMode>
);
