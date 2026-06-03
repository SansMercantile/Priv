// content.js
// SANS PRIV XM Connector - Content Script

(function() {
  console.log("[PRIV-Connector] Content script injected on XM Global member area.");

  function getAccountId() {
    // Try different selectors/patterns to find Account ID on XM Global member area page
    const bodyText = document.body.innerText;
    const accountIdMatch = bodyText.match(/Account ID:\s*(\d+)/i) || 
                           bodyText.match(/ID:\s*(\d+)/i) ||
                           bodyText.match(/MT[45]\s*ID:\s*(\d+)/i);
    
    if (accountIdMatch) {
      return accountIdMatch[1];
    }
    
    // Fallback: look for typical XM DOM elements
    const memberLoginElement = document.querySelector(".member-login-id, .account-id, [data-account-id]");
    if (memberLoginElement) {
      return memberLoginElement.textContent.trim().replace(/\D/g, "");
    }
    
    return null;
  }

  function triggerSync() {
    const accountId = getAccountId();
    if (!accountId) {
      console.log("[PRIV-Connector] Could not determine Account ID yet. User might not be logged in or page still loading.");
      return;
    }

    console.log(`[PRIV-Connector] Found Account ID: ${accountId}. Sending sync request to background worker...`);
    chrome.storage.local.set({ lastKnownAccount: accountId });
    chrome.runtime.sendMessage({
      action: "sync_session",
      accountId: accountId
    }, (response) => {
      if (chrome.runtime.lastError) {
        console.error("[PRIV-Connector] Error communicating with background service worker:", chrome.runtime.lastError.message);
        return;
      }
      if (response && response.success) {
        console.log(`[PRIV-Connector] Session sync successful! Time: ${response.timestamp}`);
      } else {
        console.warn(`[PRIV-Connector] Session sync failed or pending: ${response ? response.error : 'No response'}`);
      }
    });
  }

  // Run on page load
  if (document.readyState === "complete" || document.readyState === "interactive") {
    // Small delay to allow dynamic JS to load the account ID
    setTimeout(triggerSync, 2000);
  } else {
    window.addEventListener("DOMContentLoaded", () => {
      setTimeout(triggerSync, 2000);
    });
  }

  // Periodically check/sync every 5 minutes in case the session gets renewed or page states change
  setInterval(triggerSync, 300000);
})();