import React from "react";
import { BrowserRouter } from "react-router-dom";
import { Auth0Provider, AppState } from "@auth0/auth0-react";
import App from "./App.tsx";

const domain = (import.meta as any).env?.VITE_AUTH0_DOMAIN;
const clientId = (import.meta as any).env?.VITE_AUTH0_CLIENT_ID;

const onRedirectCallback = (appState?: AppState) => {
  window.history.replaceState(
    {},
    document.title,
    appState?.returnTo || window.location.pathname
  );
};

export default function AuthRoot() {
  if (!domain || !clientId) {
    console.error(
      "[Auth0] VITE_AUTH0_DOMAIN / VITE_AUTH0_CLIENT_ID are not set. Auth is disabled."
    );
  }

  return (
    <Auth0Provider
      domain={domain}
      clientId={clientId}
      authorizationParams={{
        redirect_uri: window.location.origin + "/callback",
      }}
      onRedirectCallback={onRedirectCallback}
      cacheLocation="localstorage"
      useRefreshTokens={true}
    >
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </Auth0Provider>
  );
}
