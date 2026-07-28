import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx
import websockets
from deriv_api.errors import ResponseError as DerivAPIError

from ..broker_interface import BaseTradeAPIAdapter

logger = logging.getLogger(__name__)

REST_BASE_URL = "https://api.derivws.com"


class DerivOptionsAPIAdapter(BaseTradeAPIAdapter):
    """
    Adapter for Deriv's newer REST+WebSocket "Options" trading platform
    (developers.deriv.com), as distinct from the legacy WebSocket-only API
    that DerivAPIAdapter (deriv_adapter.py) targets. Used for apps
    registered on developers.deriv.com/dashboard (e.g. the PRIV business
    app), authenticated via a Personal Access Token (PAT) issued from that
    same portal - NOT the personal-account tokens from home.deriv.com,
    which belong to the legacy API and will not work here.

    Auth flow (per Deriv's own docs):
      1. REST: get-or-create an Options account (POST/GET /trading/v1/options/accounts)
      2. REST: exchange the PAT for a short-lived OTP-embedded WebSocket URL
         (POST /trading/v1/options/accounts/{account_id}/otp)
      3. Open a raw WebSocket to that URL - the OTP in the URL itself
         authenticates the session, no `authorize` call needed.

    Once connected, the actual trading message protocol (proposal, buy,
    sell, portfolio, contract_update, cancel) is the same JSON-RPC schema
    as the legacy API, so this adapter wraps the raw connection with the
    same `deriv_api.DerivAPI` class used by DerivAPIAdapter and reuses its
    verified call patterns rather than reimplementing them.

    Note on connection lifetime: the OTP-issued WebSocket session can drop
    silently (e.g. idle timeout) between calls even while self.is_connected
    still reads True from the last successful call. _raw_call() detects a
    dead socket and reconnects+retries once automatically, so callers don't
    need to handle that themselves.
    """

    name = "deriv_options"

    def __init__(self, app_id: str, api_token: str, account_type: str = "demo", currency: str = "USD"):
        if account_type not in ("demo", "real"):
            raise ValueError("account_type must be 'demo' or 'real'")
        self.app_id = app_id
        self.api_token = api_token
        self.account_type = account_type
        self.currency = currency
        self.account_id: Optional[str] = None
        self._raw_ws = None
        self.is_connected = False

    def _headers(self) -> Dict[str, str]:
        return {
            "Deriv-App-ID": str(self.app_id),
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    async def _get_or_create_account(self, client: httpx.AsyncClient) -> str:
        """Get an existing Options account matching account_type, or create one."""
        resp = await client.get(
            f"{REST_BASE_URL}/trading/v1/options/accounts", headers=self._headers()
        )
        if resp.status_code == 200:
            accounts = resp.json().get("data", [])
            for acc in accounts:
                if acc.get("account_type") == self.account_type:
                    logger.info(f"DerivOptionsAPIAdapter: found existing {self.account_type} account {acc['account_id']}")
                    return acc["account_id"]

        # No matching account found - create one
        create_resp = await client.post(
            f"{REST_BASE_URL}/trading/v1/options/accounts",
            headers=self._headers(),
            json={"currency": self.currency, "group": "row", "account_type": self.account_type},
        )
        if create_resp.status_code not in (200, 201):
            raise DerivAPIError(
                f"Failed to get-or-create Options account: HTTP {create_resp.status_code} - {create_resp.text}"
            )
        body = create_resp.json()
        data = body["data"]
        account = data[0] if isinstance(data, list) else data
        logger.info(f"DerivOptionsAPIAdapter: account ready {account['account_id']} (status {create_resp.status_code})")
        return account["account_id"]

    async def _request_otp_ws_url(self, client: httpx.AsyncClient, account_id: str) -> str:
        resp = await client.post(
            f"{REST_BASE_URL}/trading/v1/options/accounts/{account_id}/otp",
            headers=self._headers(),
        )
        if resp.status_code != 200:
            raise DerivAPIError(f"Failed to obtain OTP: HTTP {resp.status_code} - {resp.text}")
        return resp.json()["data"]["url"]

    async def connect(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                self.account_id = await self._get_or_create_account(client)
                ws_url = await self._request_otp_ws_url(client, self.account_id)

            # OTP tokens are short-lived - connect immediately after issuing.
            self._raw_ws = await asyncio.wait_for(websockets.connect(ws_url), timeout=15)
            self.is_connected = True
            logger.info(f"DerivOptionsAPIAdapter connected successfully. Account: {self.account_id}")
            return True
        except Exception as e:
            logger.error(f"DerivOptionsAPIAdapter connection failed: {e}", exc_info=True)
            self.is_connected = False
            return False

    async def _raw_call(self, request, _retried: bool = False):
        """
        Send a message directly over the raw websocket, bypassing DerivAPI's
        convenience methods. Required for calls whose request schema has
        diverged on this newer Options platform (proposal/buy use
        underlying_symbol instead of symbol) - python-deriv-api's local
        client-side validation is generated from the legacy API and does
        not know about the rename, so it rejects the new field name before
        anything is even sent. Going raw sidesteps that stale validation
        while still reusing the same authenticated connection.

        If the socket has silently died since is_connected was last set
        True (the OTP-issued session can drop between calls), this
        reconnects and retries the call exactly once before giving up.
        """
        import json
        req_id = request.setdefault("req_id", id(request) % 1000000)
        try:
            await self._raw_ws.send(json.dumps(request))
            while True:
                raw = await asyncio.wait_for(self._raw_ws.recv(), timeout=15)
                data = json.loads(raw)
                if data.get("req_id") == req_id:
                    if data.get("error"):
                        raise DerivAPIError(data)
                    return data
        except (websockets.exceptions.ConnectionClosed, OSError, asyncio.TimeoutError) as e:
            if _retried:
                logger.error(f"DerivOptionsAPIAdapter: retry after reconnect also failed: {e}")
                self.is_connected = False
                raise
            logger.warning(f"DerivOptionsAPIAdapter: socket dead ({e!r}), reconnecting and retrying once")
            self.is_connected = False
            if not await self.connect():
                raise
            request.pop("req_id", None)
            return await self._raw_call(request, _retried=True)

    async def get_historical_data(self, symbol, timeframe='daily', limit=250):
        import pandas as pd
        if not self.is_connected:
            if not await self.connect():
                return None
        gran_map = {'1m':60,'5m':300,'15m':900,'30m':1800,'1h':3600,'4h':14400,'daily':86400,'1d':86400}
        granularity = gran_map.get(timeframe, 3600)
        try:
            resp = await self._raw_call({'ticks_history': symbol, 'adjust_start_time': 1, 'count': limit, 'end': 'latest', 'granularity': granularity, 'style': 'candles'})
            candles = resp.get('candles', [])
            if not candles:
                return None
            df = pd.DataFrame(candles)
            df['timestamp'] = pd.to_datetime(df['epoch'], unit='s')
            df = df.set_index('timestamp')[['open','high','low','close']]
            return df.astype(float)
        except Exception as e:
            logger.error('Deriv Options get_historical_data failed: ' + str(e))
            return None

    async def disconnect(self) -> None:
        if self._raw_ws:
            await self._raw_ws.close()
        self.is_connected = False

    async def get_account_info(self) -> Dict[str, Any]:
        if not self.is_connected:
            if not await self.connect():
                return {}
        try:
            resp = await self._raw_call({"balance": 1})
            bal = resp.get("balance", {})
            return {
                "account_id": self.account_id,
                "balance": bal.get("balance"),
                "currency": bal.get("currency"),
                "account_type": self.account_type,
            }
        except DerivAPIError as e:
            logger.error(f"Deriv Options API error fetching balance: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching Deriv Options balance: {e}", exc_info=True)
            self.is_connected = False
        return {}

    async def get_open_positions(self) -> List[Dict[str, Any]]:
        if not self.is_connected:
            if not await self.connect():
                return []
        try:
            resp = await self._raw_call({"portfolio": 1})
            contracts = resp.get("portfolio", {}).get("contracts", [])
            return [
                {
                    "order_id": str(c.get("contract_id")),
                    "symbol": c.get("underlying_symbol") or c.get("symbol"),
                    "contract_type": c.get("contract_type"),
                    "buy_price": c.get("buy_price"),
                    "payout": c.get("payout"),
                    "purchase_time": c.get("purchase_time"),
                    "date_expiry": c.get("expiry_time"),
                    "longcode": c.get("longcode"),
                }
                for c in contracts
            ]
        except DerivAPIError as e:
            logger.error(f"Deriv Options API error fetching portfolio: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching Deriv Options portfolio: {e}", exc_info=True)
            self.is_connected = False
        return []

    async def get_pending_orders(self) -> List[Dict[str, Any]]:
        # Same rationale as the legacy DerivAPIAdapter: contracts execute
        # immediately on buy, there is no traditional pending-order queue.
        return []

    async def send_order(self, symbol: str, order_type: str = None, volume: float = None,
                          price: float = None, stop_loss: float = None, take_profit: float = None,
                          contract_type: str = None, amount: float = None,
                          duration: int = 5, duration_unit: str = "m", **kwargs) -> Optional[Dict[str, Any]]:
        """
        Accepts BOTH the generic broker_manager interface (order_type/volume,
        as used by execute_trade()) AND direct contract_type/amount calls.
        order_type of "BUY"/"MARKET" maps to CALL, "SELL" maps to PUT - a
        reasonable default for directional binary contracts; callers wanting
        a specific contract_type (e.g. multipliers) should pass it directly.
        """
        if contract_type is None:
            if order_type in ("SELL", "PUT"):
                contract_type = "PUT"
            else:
                contract_type = "CALL"
        if amount is None:
            amount = abs(volume) if volume is not None else 10.0
        if not self.is_connected:
            if not await self.connect():
                return None
        try:
            proposal_resp = await self._raw_call({
                "proposal": 1,
                "amount": amount,
                "basis": kwargs.get("basis", "stake"),
                "contract_type": contract_type,
                "currency": self.currency,
                "duration": duration,
                "duration_unit": duration_unit,
                "underlying_symbol": symbol,  # renamed from symbol on this newer Options platform
            })
            proposal_id = proposal_resp["proposal"]["id"]
            ask_price = proposal_resp["proposal"]["ask_price"]
            buy_resp = await self._raw_call({"buy": proposal_id, "price": ask_price})
            buy_data = buy_resp.get("buy", {})
            logger.info(f"DerivOptionsAPIAdapter: contract bought {buy_data.get('contract_id')}")
            return {
                "order_id": str(buy_data.get("contract_id")),
                "buy_price": buy_data.get("buy_price"),
                "payout": buy_data.get("payout"),
                "longcode": buy_data.get("longcode"),
            }
        except DerivAPIError as e:
            logger.error(f"Deriv Options API error placing order: {e}")
        except Exception as e:
            logger.error(f"Unexpected error placing Deriv Options order: {e}", exc_info=True)
            self.is_connected = False
        return None

    async def close_position(self, order_id, price: float = 0, **kwargs) -> bool:
        if not self.is_connected:
            if not await self.connect():
                return False
        try:
            resp = await self._raw_call({"sell": int(order_id), "price": price or 0})
            if resp.get("error"):
                logger.error(f"Deriv Options API error selling contract {order_id}: {resp['error'].get('message')}")
                return False
            return True
        except DerivAPIError as e:
            logger.error(f"Deriv Options API error selling contract {order_id}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error selling Deriv Options contract {order_id}: {e}", exc_info=True)
            self.is_connected = False
        return False

    async def modify_position(self, order_id, new_sl: Optional[float] = None,
                               new_tp: Optional[float] = None, **kwargs) -> bool:
        # Same limitation as the legacy adapter: only Multiplier/Accumulator
        # contracts support stop_loss/take_profit updates on Deriv, not the
        # CALL/PUT contracts send_order() creates by default.
        if not self.is_connected:
            if not await self.connect():
                return False
        if new_sl is None and new_tp is None:
            return False
        limit_order: Dict[str, Any] = {}
        if new_sl is not None:
            limit_order["stop_loss"] = new_sl
        if new_tp is not None:
            limit_order["take_profit"] = new_tp
        try:
            resp = await self._raw_call({
                "contract_update": 1,
                "contract_id": int(order_id),
                "limit_order": limit_order,
            })
            if resp.get("error"):
                logger.error(f"Deriv Options API error updating contract {order_id}: {resp['error'].get('message')}")
                return False
            return True
        except DerivAPIError as e:
            logger.error(f"Deriv Options API error updating contract {order_id}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error updating Deriv Options contract {order_id}: {e}", exc_info=True)
            self.is_connected = False
        return False

    async def delete_pending_order(self, order_id) -> bool:
        if not self.is_connected:
            if not await self.connect():
                return False
        try:
            resp = await self._raw_call({"cancel": int(order_id)})
            if resp.get("error"):
                logger.error(f"Deriv Options API error cancelling contract {order_id}: {resp['error'].get('message')}")
                return False
            return True
        except DerivAPIError as e:
            logger.error(f"Deriv Options API error cancelling contract {order_id}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error cancelling Deriv Options contract {order_id}: {e}", exc_info=True)
            self.is_connected = False
        return False
