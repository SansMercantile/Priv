(async function() {
  console.log("[PRIV-Connector] Monitoring XM session...");

  // Function to extract cookies and push to PRIV server
  async function syncSession() {
    try {
      // Get all cookies for the current domain
      const cookies = await chrome.cookies.getAll({ domain: "my.xm.com" });
      const cookieString = cookies.map(c => `${c.name}=${c.value}`).join("; ");
      
      if (!cookieString || !cookieString.includes("PHPSESSID")) {
        console.log("[PRIV-Connector] No valid session found. User might not be logged in.");
        return;
      }

      // We need the account ID to identify the broker. 
      // We can try to find it in the DOM or use a default if the user is already configured.
      const accountIdMatch = document.body.innerText.match(/Account ID:\s*(\d+)/i);
      const accountId = accountIdMatch ? accountIdMatch[1] : "unknown";
      const brokerId = "xm_user_account_" + accountId;

      console.log(`[PRIV-Connector] Syncing session for ${brokerId}...`);

      const response = await fetch("http://localhost:3000/api/auth/xm-bridge", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          broker_id: brokerId,
          session_token: cookieString
        })
      });

      const result = await response.json();
      if (result.success) {
        console.log("[PRIV-Connector] Session successfully synchronized with PRIV Core.");
        // Optionally notify the user via a small toast or alert
      } else {
        console.error("[PRIV-Connector] Sync failed:", result.error);
      }
    } catch (e) {
      console.error("[PRIV-Connector] Error during sync:", e);
    }
  }

  // Sync on load
  syncSession();

  // Also sync periodically or on specific events (like navigation)
  setInterval(syncSession, 60000);
})();