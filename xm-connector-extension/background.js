// background.js
// SANS PRIV XM Connector - Background Service Worker

const DEFAULT_SERVER_URL = "http://localhost:3000";

// Listen for messages from content scripts or popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "sync_session") {
    handleSyncSession(request.accountId, sendResponse);
    return true; // Keep message channel open for async response
  }
});

async function handleSyncSession(accountId, sendResponse) {
  try {
    // Get server URL from storage, or use default
    const storage = await chrome.storage.local.get(["privServerUrl"]);
    const serverUrl = storage.privServerUrl || DEFAULT_SERVER_URL;
    
    // Get cookies for XM Global
    const cookies = await chrome.cookies.getAll({ domain: "my.xm.com" });
    if (!cookies || cookies.length === 0) {
      console.warn("[PRIV-Connector] No cookies found for my.xm.com");
      sendResponse({ success: false, error: "No cookies found. Please log in to XM Global first." });
      return;
    }
    
    const cookieString = cookies.map(c => `${c.name}=${c.value}`).join("; ");
    if (!cookieString.includes("PHPSESSID")) {
      console.warn("[PRIV-Connector] PHPSESSID cookie not found");
      sendResponse({ success: false, error: "Active XM session cookie not found. Please log in." });
      return;
    }

    const brokerId = "xm_user_account_" + accountId;
    console.log(`[PRIV-Connector] Syncing session for ${brokerId} to ${serverUrl}...`);

    // Clean up the URL to ensure it has no trailing slash and includes protocol
    const cleanServerUrl = serverUrl.replace(/\/$/, "");
    const endpoint = `${cleanServerUrl}/api/auth/xm-bridge`;

    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        broker_id: brokerId,
        session_token: cookieString
      })
    });

    if (!response.ok) {
      throw new Error(`Server returned status ${response.status}`);
    }

    const result = await response.json();
    if (result.success) {
      console.log("[PRIV-Connector] Session successfully synchronized with PRIV Core.");
      // Save last sync time and account ID
      await chrome.storage.local.set({
        lastSyncTime: new Date().toISOString(),
        lastSyncAccount: accountId,
        syncStatus: "success",
        lastError: null
      });
      sendResponse({ success: true, timestamp: new Date().toISOString(), accountId });
    } else {
      console.error("[PRIV-Connector] Sync failed:", result.error);
      await chrome.storage.local.set({ syncStatus: "failed", lastError: result.error });
      sendResponse({ success: false, error: result.error });
    }
  } catch (e) {
    console.error("[PRIV-Connector] Error during sync:", e);
    await chrome.storage.local.set({ syncStatus: "failed", lastError: e.message });
    sendResponse({ success: false, error: e.message });
  }
}
