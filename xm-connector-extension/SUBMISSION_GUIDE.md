# SANS PRIV XM Connector - Chrome Web Store Submission Guide

This guide explains how to package and upload the XM Connector extension to the Chrome Web Store.

## 1. Prepare the Assets
The extension requires three icon sizes in the `icons/` folder. Please create and save the following PNG files:
- `icon16.png` (16x16 pixels)
- `icon48.png` (48x48 pixels)
- `icon128.png` (128x128 pixels)

*Tip: Use a high-contrast emerald/black logo to match the PRIV brand.*

## 2. Package the Extension
1. Right-click the `xm-connector-extension` folder.
2. Compress it into a `.zip` file (e.g., `SANS_PRIV_Connector_v1.zip`).
3. Ensure the `manifest.json` is at the root of the zip file.

## 3. Upload to Chrome Web Store
1. Go to the [Chrome Web Store Developer Console](https://chrome.google.com/webstore/devconsole/).
2. Click **"New Item"**.
3. Upload your `.zip` file.
4. Fill in the Store Listing details:
   - **Description**: Use the description provided in the `manifest.json`.
   - **Category**: "Productivity" or "Developer Tools".
   - **Privacy Policy**: You will need to provide a URL to your privacy policy (explaining that cookies are only used for the PRIV handshake).

## 4. Review and Publish
1. Submit the extension for review.
2. Google will typically review the extension within 24-72 hours.
3. Once approved, you will receive a public URL (e.g., `chrome.google.com/webstore/detail/...`).

## 5. Integrate the Link
Once you have the public URL, replace the "Install Connector" logic in the PRIV app with a direct link to this store page.
