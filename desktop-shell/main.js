const { app, BrowserWindow, shell } = require("electron");

const START_URL = "https://priv.sansmercantile.com/";
const APP_HOST = "priv.sansmercantile.com";

function createWindow() {
  const win = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 960,
    minHeight: 600,
    backgroundColor: "#050505",
    autoHideMenuBar: true,
    title: "Priv Core",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  win.webContents.setWindowOpenHandler(({ url }) => {
    try {
      if (new URL(url).host === APP_HOST) return { action: "allow" };
    } catch (_) {
      /* fall through to external */
    }
    shell.openExternal(url);
    return { action: "deny" };
  });

  win.webContents.on("will-navigate", (event, url) => {
    try {
      if (new URL(url).host !== APP_HOST) {
        event.preventDefault();
        shell.openExternal(url);
      }
    } catch (_) {
      /* ignore malformed urls */
    }
  });

  win.loadURL(START_URL);
}

app.whenReady().then(() => {
  createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
