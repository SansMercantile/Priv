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

  // Auth0's SDK auto-detects ?code&state on ANY route within this provider
  // and tries to process it as ITS OWN callback -- which collides with the
  // separate Deriv OAuth flow (also client-side, also lands with ?code&state
  // on the app's root/success path). Only let Auth0 actually process a
  // callback on its own dedicated /callback route (matching redirect_uri
  // below); skip it everywhere else so Deriv's callback isn't misread as an
  // Auth0 one and rejected with a false "Invalid state" error.
  const skipRedirectCallback = window.location.pathname !== "/callback";

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
      skipRedirectCallback={skipRedirectCallback}
    >
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </Auth0Provider>
  );
}
