// Ported/adapted from the official Deriv PrivCore_lite reference app
// (source: repos/priv_core/src/external/deriv-core/auth/accounts.ts)

import { DerivAuthInfo, DerivAccount, storeDerivAccounts, setActiveLoginId, setAccountType } from "./storage";
import { DERIV_APP_ID } from "./oauth";

const API_BASE = "https://api.derivws.com/trading/v1/options";

export async function fetchDerivAccounts(authInfo: DerivAuthInfo): Promise<DerivAccount[]> {
  const response = await fetch(`${API_BASE}/accounts`, {
    headers: {
      Authorization: `Bearer ${authInfo.access_token}`,
      "Deriv-App-ID": DERIV_APP_ID,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch Deriv accounts (${response.status})`);
  }

  const data = await response.json();
  const accounts: DerivAccount[] = data.data;

  storeDerivAccounts(accounts);

  if (accounts.length > 0) {
    const firstAccount = accounts.find((a) => a.account_type === "demo") || accounts[0];
    setActiveLoginId(firstAccount.account_id);
    setAccountType(firstAccount.account_type);
  }

  return accounts;
}
