// popup.js
// SANS PRIV XM Connector - Popup Script

const DEFAULT_SERVER_URL = "http://localhost:3000";

document.addEventListener("DOMContentLoaded", async () => {
  const statusDot = document.getElementById("statusDot");
  const statusLabel = document.getElementById("statusLabel");
  const syncStatusText = document.getElementById("syncStatusText");
  const accountIdText = document.getElementById("accountIdText");
  const lastSyncText = document.getElementById("lastSyncText");
  const serverUrlInput = document.getElementById("serverUrl");
  
  const saveBtn = document.getElementById("saveBtn");
  const syncBtn = document.getElementById("syncBtn");
  const dashboardBtn = document.getElementById("dashboardBtn");

  // Load saved configurations and status
  await updateStatusUI();

  // Save server URL configuration
  saveBtn.addEventListener("click", async () => {
    let url = serverUrlInput.value.trim();
    if (!url) {
      url = DEFAULT_SERVER_URL;
    }
    
    // Simple validation
    try {
      if (!url.startsWith("http://") && !url.startsWith("https://")) {
        url = "http://" + url;
      }
      new URL(url); // Check if valid URL structure
    } catch (e) {
      alert("Invalid URL format. Please enter a valid server endpoint.");
      return;
    }

    await chrome.storage.local.set({ privServerUrl: url });
    serverUrlInput.value = url;
    
    // Visual feedback
    const originalText = saveBtn.textContent;
    saveBtn.textContent = "Saved Successfully!";
    saveBtn.style.borderColor = "#10b981";
    saveBtn.style.color = "#10b981";
    setTimeout(() => {
      saveBtn.textContent = originalText;
      saveBtn.style.borderColor = "";
      saveBtn.style.color = "";
    }, 2000);
  });

  // Manual synchronization
  syncBtn.addEventListener("click", async () => {
    syncBtn.disabled = true;
    syncBtn.innerHTML = '<svg class="animate-spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg> Syncing...';
    
    try {
      // Find active XM member area tabs
      const tabs = await chrome.tabs.query({ url: "https://my.xm.com/member/*" });
      
      if (tabs.length === 0) {
        // Fallback: check if we have a last known account in storage
        const storage = await chrome.storage.local.get(["lastKnownAccount"]);
        if (storage.lastKnownAccount) {
          // Trigger sync using the last known account
          await triggerSync(storage.lastKnownAccount);
        } else {
          alert("Active XM member portal tab not found.\n\nPlease open your XM Global member area in Chrome and log in to sync your session.");
        }
      } else {
        // If tab is open, we can send a message to content.js in that tab, or just run sync directly if we know account id
        const storage = await chrome.storage.local.get(["lastKnownAccount"]);
        const accountId = storage.lastKnownAccount || "unknown";
        await triggerSync(accountId);
      }
    } catch (err) {
      console.error(err);
      alert("Synchronization failed: " + err.message);
    } finally {
      syncBtn.disabled = false;
      syncBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg> Synchronize Now';
      await updateStatusUI();
    }
  });

  // Open PRIV Dashboard
  dashboardBtn.addEventListener("click", async () => {
    const storage = await chrome.storage.local.get(["privServerUrl"]);
    const serverUrl = storage.privServerUrl || DEFAULT_SERVER_URL;
    chrome.tabs.create({ url: serverUrl });
  });

  async function triggerSync(accountId) {
    return new Promise((resolve) => {
      chrome.runtime.sendMessage({
        action: "sync_session",
        accountId: accountId
      }, (response) => {
        if (chrome.runtime.lastError) {
          alert("Error connecting to background worker: " + chrome.runtime.lastError.message);
          resolve(false);
          return;
        }
        if (response && response.success) {
          resolve(true);
        } else {
          alert("Sync failed: " + (response ? response.error : "Unknown error"));
          resolve(false);
        }
      });
    });
  }

  async function updateStatusUI() {
    const storage = await chrome.storage.local.get([
      "privServerUrl",
      "lastSyncTime",
      "lastSyncAccount",
      "syncStatus",
      "lastError"
    ]);

    // Update Server URL Input
    serverUrlInput.value = storage.privServerUrl || DEFAULT_SERVER_URL;

    // Update Status Indicators
    if (storage.syncStatus === "success") {
      statusDot.className = "status-indicator active";
      statusLabel.textContent = "Bridge Securely Synced";
      syncStatusText.textContent = "Synced";
      syncStatusText.style.color = "#10b981";
      
      const accountId = storage.lastSyncAccount || "Unknown";
      accountIdText.textContent = `XM-ID ${accountId}`;
      
      if (storage.lastSyncTime) {
        const date = new Date(storage.lastSyncTime);
        lastSyncText.textContent = date.toLocaleTimeString();
      } else {
        lastSyncText.textContent = "Never";
      }
    } else if (storage.syncStatus === "failed") {
      statusDot.className = "status-indicator error";
      statusLabel.textContent = "Sync Interrupted";
      syncStatusText.textContent = "Error";
      syncStatusText.style.color = "#ef4444";
      accountIdText.textContent = storage.lastSyncAccount ? `XM-ID ${storage.lastSyncAccount}` : "None";
      lastSyncText.textContent = storage.lastError ? `Err: ${storage.lastError.substring(0, 15)}...` : "Failed";
    } else {
      statusDot.className = "status-indicator";
      statusLabel.textContent = "Bridge Unsynchronized";
      syncStatusText.textContent = "Pending";
      syncStatusText.style.color = "#9ca3af";
      accountIdText.textContent = "None";
      lastSyncText.textContent = "Never";
    }
  }
});
