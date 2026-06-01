/*
Simple test script to POST to /api/brokers/register
Usage:
  node tools/test_register_broker.js --account 12345 --server "XMGlobal-Real 14" --cookie "PHPSESSID=...;"
Or set SESSION_TOKEN env var and run with account arg.
*/

const argv = process.argv.slice(2);
const argMap = {};
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a.startsWith('--')) {
    const k = a.slice(2);
    const v = argv[i+1] && !argv[i+1].startsWith('--') ? argv[++i] : true;
    argMap[k] = v;
  }
}

const account = argMap.account || argMap.a || process.env.TEST_XM_ACCOUNT || "12345";
const server = argMap.server || process.env.TEST_XM_SERVER || "XMGlobal-Real 14";
const sessionToken = argMap.cookie || argMap.session_token || process.env.SESSION_TOKEN || process.env.XM_SESSION_TOKEN || "";
const host = argMap.host || process.env.BROKER_HOST || "http://localhost:3000";
const fetch = globalThis.fetch;
if (!fetch) {
  console.error('Node runtime has no global fetch. Use Node 18+ or run via a fetch polyfill.');
  process.exit(1);
}

(async () => {
  try {
    const brokerId = "xm_user_account_" + account;
    const body = {
      broker_id: brokerId,
      broker_type: "xm",
      config: { account_id: account, server }
    };
    if (sessionToken) body.session_token = sessionToken;

    console.log("Posting register payload to", host + "/api/brokers/register");
    const res = await fetch(host + "/api/brokers/register", {
      method: "POST",
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    const txt = await res.text();
    console.log("Status:", res.status);
    try { console.log("JSON:", JSON.parse(txt)); } catch (e) { console.log(txt); }
  } catch (e) {
    console.error("Error:", e);
    process.exit(2);
  }
})();
