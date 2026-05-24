# backend/trading_engine/trade_executor.py

import pandas as pd
import numpy as np
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional, Union, TypedDict
import asyncio

# --- Import Core Components ---
# The executor now imports the INSTANCE of the router, not the class.
# This instance is created in broker_router.py and configured in dependencies.py
from .broker_router import broker_router
from .broker_interface import BaseTradeAPIAdapter


logger = logging.getLogger(__name__)

# --- Configuration Constants ---
DEFAULT_SLIPPAGE: int = 3
DEFAULT_MAGIC_NUMBER: int = 1234
MIN_STOP_LEVEL_POINTS: int = 10
DEFAULT_DIGITS: int = 5

# --- Enums and Data Models ---
class MoneyManagementMode:
    FREEMARGIN = 0
    BALANCE = 1
    LOSSFREEMARGIN = 2
    LOSSBALANCE = 3
    FIXED_LOT = 4
    THEMASTERMIND_MM_FRACTIONAL = 5
    THEMASTERMIND_MM_FULL = 6

class PositionDict(TypedDict):
    id: int
    type: str
    symbol: str
    volume: float
    entry_price: float
    current_price: float
    stop_loss: float
    take_profit: float
    open_time: str
    magic: int
    comment: str

# --- Global Variables for Trade Cooldown ---
_last_trade_times: Dict[Tuple[str, str], datetime] = {}

def _get_time_level_name(symbol: str, trade_type: str) -> Tuple[str, str]:
    return (symbol, trade_type)

def is_trade_time_level_clear(symbol: str, trade_type: str, min_delay_seconds: int) -> bool:
    key = _get_time_level_name(symbol, trade_type)
    last_trade_time = _last_trade_times.get(key)
    if last_trade_time is None:
        return True

    time_since_last_trade = (datetime.now() - last_trade_time).total_seconds()
    is_clear = time_since_last_trade >= min_delay_seconds
    if not is_clear:
        logger.info(f"Priv Trade cooldown active for {symbol} {trade_type}. Time left: {min_delay_seconds - time_since_last_trade:.1f}s")
    return is_clear

def set_trade_time_level(symbol: str, trade_type: str):
    key = _get_time_level_name(symbol, trade_type)
    _last_trade_times[key] = datetime.now()
    logger.debug(f"Priv Trade time level set for {symbol} {trade_type} at {datetime.now()}")


def _get_lot_step_and_limits(symbol: str, symbol_info: Dict[str, Any]) -> Tuple[float, float, float]:
    step = symbol_info.get("volume_step", 0.01)
    min_lot = symbol_info.get("volume_min", 0.01)
    max_lot = symbol_info.get("volume_max", 100.0)
    return float(step), float(min_lot), float(max_lot)

async def _get_margin_per_lot(symbol: str, order_type: str, symbol_prices: Dict[str, float], symbol_info: Dict[str, Any]) -> float:
    active_adapter = await broker_router.select_adapter(criteria={"symbol": symbol})
    if not active_adapter:
        logger.warning("Priv: No active adapter to get margin info. Using heuristic.")
        return 1000.0

    adapter_name = active_adapter.name
    if "Deriv" in adapter_name:
        logger.debug("Priv: Deriv margin calculation is complex. Using heuristic.")
        return symbol_prices.get("ask", 1.0) * 100000 / 500
    elif "Alpaca" in adapter_name:
        logger.debug("Priv: Alpaca margin calculation requires asset details. Using heuristic.")
        return symbol_prices.get("ask", 1.0) * 100
    elif "MetaTrader" in adapter_name:
        logger.debug("Priv: MT5 margin calculation can be precise. Using heuristic.")
        return symbol_prices.get("ask", 1.0) * 100000 / 200
    else: # Mock Adapter
        return 1000.0

async def calculate_lot_size(
    symbol: str,
    order_type: str,
    money_management_amount: float,
    mm_mode: int,
    account_equity: float,
    account_free_margin: float,
    current_prices: Dict[str, float],
    symbol_info: Dict[str, Any],
    stop_loss_points: Optional[int] = None
) -> float:
    calculated_lot = 0.0
    point_size = symbol_info.get("point", 0.00001)
    
    if mm_mode == MoneyManagementMode.FIXED_LOT:
        calculated_lot = abs(money_management_amount)
    elif mm_mode == MoneyManagementMode.FREEMARGIN:
        target_margin = account_free_margin * money_management_amount
        margin_per_lot = await _get_margin_per_lot(symbol, order_type, current_prices, symbol_info)
        if margin_per_lot > 0:
            calculated_lot = target_margin / margin_per_lot
        else:
            logger.warning(f"Priv could not determine margin per lot for {symbol}.")
            return 0.0
    elif mm_mode == MoneyManagementMode.BALANCE:
        target_margin = account_equity * money_management_amount
        margin_per_lot = await _get_margin_per_lot(symbol, order_type, current_prices, symbol_info)
        if margin_per_lot > 0:
            calculated_lot = target_margin / margin_per_lot
        else:
            logger.warning(f"Priv could not determine margin per lot for {symbol}.")
            return 0.0
    elif mm_mode == MoneyManagementMode.LOSSFREEMARGIN:
        if stop_loss_points is None or stop_loss_points <= 0:
            logger.error(f"Priv Stop loss points required for loss-based money management mode {mm_mode}.")
            return 0.0
        
        loss_per_unit_at_sl = stop_loss_points * point_size 
        if "stocks" in symbol.lower() or "spy" in symbol.lower():
             loss_per_unit_at_sl *= 1
        else:
             loss_per_unit_at_sl *= 100000

        if loss_per_unit_at_sl <= 0:
            logger.warning("Priv calculated loss per unit is zero or negative. Cannot determine lot size.")
            return 0.0
        allowed_loss = account_free_margin * money_management_amount
        calculated_lot = allowed_loss / loss_per_unit_at_sl
    elif mm_mode == MoneyManagementMode.LOSSBALANCE:
        if stop_loss_points is None or stop_loss_points <= 0:
            logger.error(f"Priv Stop loss points required for loss-based money management mode {mm_mode}.")
            return 0.0
        
        loss_per_unit_at_sl = stop_loss_points * point_size
        if "stocks" in symbol.lower() or "spy" in symbol.lower():
             loss_per_unit_at_sl *= 1
        else:
             loss_per_unit_at_sl *= 100000
        
        if loss_per_unit_at_sl <= 0:
            logger.warning("Priv calculated loss per unit is zero or negative. Cannot determine lot size.")
            return 0.0
        allowed_loss = account_equity * money_management_amount
        calculated_lot = allowed_loss / loss_per_unit_at_sl
    elif mm_mode == MoneyManagementMode.THEMASTERMIND_MM_FRACTIONAL:
        calculated_lot = np.ceil(account_equity * money_management_amount / 298.0) / 10.0 - 0.1
        calculated_lot = max(calculated_lot, 0.1)
    elif mm_mode == MoneyManagementMode.THEMASTERMIND_MM_FULL:
        calculated_lot = np.ceil(account_equity * money_management_amount / 100.0) / 10.0 - 1.0
        calculated_lot = np.ceil(calculated_lot)
        calculated_lot = max(calculated_lot, 1.0)
    else:
        logger.error(f"Priv Unknown money management mode: {mm_mode}")
        return 0.0

    step, min_lot, max_lot = _get_lot_step_and_limits(symbol, symbol_info)

    calculated_lot = np.floor(calculated_lot / step) * step
    calculated_lot = max(min_lot, min(calculated_lot, max_lot))

    margin_needed = await _get_margin_per_lot(symbol, order_type, current_prices, symbol_info) * calculated_lot
    
    if margin_needed > account_free_margin:
        logger.warning(f"Priv calculated lot {calculated_lot} needs {margin_needed:.2f} margin, "
                       f"but only {account_free_margin:.2f} available. Adjusting to max affordable lot.")
        
        effective_margin_per_lot = await _get_margin_per_lot(symbol, order_type, current_prices, symbol_info)
        if effective_margin_per_lot > 0:
            max_affordable_lot = np.floor(account_free_margin / effective_margin_per_lot / step) * step
            calculated_lot = max(min_lot, min(calculated_lot, max_affordable_lot))
            if calculated_lot < min_lot:
                logger.error(f"Priv Not enough free margin for minimum lot of {symbol}.")
                return 0.0
        else:
            logger.error(f"Priv Cannot calculate max affordable lot due to zero margin_per_lot from adapter.")
            return 0.0

    return round(calculated_lot, 2)

def _is_stop_correct(sl_tp_value: float, current_price: float, symbol_info: Dict[str, Any], is_stop_loss: bool, order_type: str) -> bool:
    point_size = symbol_info.get("point", 0.00001)
    stops_level_points = symbol_info.get("stops_level", MIN_STOP_LEVEL_POINTS)
    min_distance = stops_level_points * point_size

    if "BUY" in order_type.upper():
        if is_stop_loss:
            if current_price - sl_tp_value < min_distance:
                logger.warning(f"Priv BUY SL {sl_tp_value:.{symbol_info.get('digits', 5)}f} too close to market ({current_price:.{symbol_info.get('digits', 5)}f}). Min distance: {min_distance:.5f}")
                return False
        else: # Is Take Profit
            if sl_tp_value - current_price < min_distance:
                logger.warning(f"Priv BUY TP {sl_tp_value:.{symbol_info.get('digits', 5)}f} too close to market ({current_price:.{symbol_info.get('digits', 5)}f}). Min distance: {min_distance:.5f}")
                return False
    elif "SELL" in order_type.upper():
        if is_stop_loss:
            if sl_tp_value - current_price < min_distance:
                logger.warning(f"Priv SELL SL {sl_tp_value:.{symbol_info.get('digits', 5)}f} too close to market ({current_price:.{symbol_info.get('digits', 5)}f}). Min distance: {min_distance:.5f}")
                return False
        else: # Is Take Profit
            if current_price - sl_tp_value < min_distance:
                logger.warning(f"Priv SELL TP {sl_tp_value:.{symbol_info.get('digits', 5)}f} too close to market ({current_price:.{symbol_info.get('digits', 5)}f}). Min distance: {min_distance:.5f}")
                return False
    return True

def _normalize_price(price: float, digits: int) -> float:
    return round(price, digits)

async def execute_market_order(
    symbol: str,
    order_type: str,
    volume: float,
    current_prices: Dict[str, float],
    symbol_info: Dict[str, Any],
    stop_loss_points: Optional[int] = None,
    take_profit_points: Optional[int] = None,
    deviation: int = DEFAULT_SLIPPAGE,
    comment: str = "",
    magic_number: int = DEFAULT_MAGIC_NUMBER,
    min_trade_delay_seconds: int = 0
) -> Optional[Union[int, str]]:
    if not is_trade_time_level_clear(symbol, order_type, min_trade_delay_seconds):
        logger.info(f"Priv Trade delay active for {symbol} {order_type}.")
        return None
    
    price = current_prices["ask"] if order_type.upper() == "BUY" else current_prices["bid"]
    digits = symbol_info.get("digits", DEFAULT_DIGITS)
    point_size = symbol_info.get("point", 0.00001)

    sl_price = None
    tp_price = None

    if stop_loss_points is not None and stop_loss_points > 0:
        sl_price_calc = price - stop_loss_points * point_size if order_type.upper() == "BUY" else price + stop_loss_points * point_size
        if _is_stop_correct(sl_price_calc, price, symbol_info, True, order_type):
            sl_price = _normalize_price(sl_price_calc, digits)
        else:
            logger.warning(f"Priv Calculated SL for {order_type} {symbol} is too close to market. Not setting SL at open.")
    
    if take_profit_points is not None and take_profit_points > 0:
        tp_price_calc = price + take_profit_points * point_size if order_type.upper() == "BUY" else price - take_profit_points * point_size
        if _is_stop_correct(tp_price_calc, price, symbol_info, False, order_type):
            tp_price = _normalize_price(tp_price_calc, digits)
        else:
            logger.warning(f"Priv Calculated TP for {order_type} {symbol} is too close to market. Not setting TP at open.")
            
    tries = 0
    max_tries = 5
    retry_time_seconds = 1
    order_id = None

    while tries < max_tries:
        active_adapter = await broker_router.select_adapter(criteria={"symbol": symbol, "order_type": order_type})
        if not active_adapter:
            logger.error(f"Priv No active broker adapter found for {symbol} {order_type}. Cannot send order.")
            break

        order_id = await active_adapter.send_order(
            order_type=order_type,
            symbol=symbol,
            volume=volume,
            price=price,
            slippage=deviation,
            stop_loss=sl_price,
            take_profit=tp_price,
            comment=comment,
            magic_number=magic_number
        )
        if order_id:
            logger.info(f"Priv Market {order_type} order for {symbol} (Vol: {volume}, Price: {price}) sent via {active_adapter.name}. Order ID: {order_id}")
            set_trade_time_level(symbol, order_type)
            break
        else:
            tries += 1
            logger.error(f"Priv Attempt {tries}/{max_tries}: Failed to send market {order_type} order for {symbol}.")
            if tries < max_tries:
                await asyncio.sleep(retry_time_seconds)
    
    return order_id

async def execute_pending_order(
    symbol: str,
    order_type: str,
    volume: float,
    entry_price: float,
    current_prices: Dict[str, float],
    symbol_info: Dict[str, Any],
    stop_loss_points: Optional[int] = None,
    take_profit_points: Optional[int] = None,
    deviation: int = DEFAULT_SLIPPAGE,
    comment: str = "",
    magic_number: int = DEFAULT_MAGIC_NUMBER,
    min_trade_delay_seconds: int = 0
) -> Optional[Union[int, str]]:
    if not is_trade_time_level_clear(symbol, order_type, min_trade_delay_seconds):
        logger.info(f"Priv Trade delay active for {symbol} {order_type}.")
        return None

    price_to_use = entry_price
    digits = symbol_info.get("digits", DEFAULT_DIGITS)
    point_size = symbol_info.get("point", 0.0001)
    sl_price = None
    tp_price = None

    if stop_loss_points is not None and stop_loss_points > 0:
        sl_price_calc = entry_price - stop_loss_points * point_size if "BUY" in order_type.upper() else entry_price + stop_loss_points * point_size
        sl_price = _normalize_price(sl_price_calc, digits)

    if take_profit_points is not None and take_profit_points > 0:
        tp_price_calc = entry_price + take_profit_points * point_size if "BUY" in order_type.upper() else entry_price - take_profit_points * point_size
        tp_price = _normalize_price(tp_price_calc, digits)
    
    min_distance_from_market_price = symbol_info.get("stops_level", MIN_STOP_LEVEL_POINTS) * point_size

    if order_type.upper() == "BUY_LIMIT" and current_prices["ask"] - entry_price < min_distance_from_market_price:
        logger.warning(f"Priv {order_type} price {entry_price} too close to current Ask {current_prices['ask']}.")
        return None
    elif order_type.upper() == "BUY_STOP" and entry_price - current_prices["ask"] < min_distance_from_market_price:
        logger.warning(f"Priv {order_type} price {entry_price} too close to current Ask {current_prices['ask']}.")
        return None
    elif order_type.upper() == "SELL_LIMIT" and entry_price - current_prices["bid"] < min_distance_from_market_price:
        logger.warning(f"Priv {order_type} price {entry_price} too close to current Bid {current_prices['bid']}.")
        return None
    elif order_type.upper() == "SELL_STOP" and current_prices["bid"] - entry_price < min_distance_from_market_price:
        logger.warning(f"Priv {order_type} price {entry_price} too close to current Bid {current_prices['bid']}.")
        return None

    tries = 0
    max_tries = 5
    retry_time_seconds = 1
    order_id = None

    while tries < max_tries:
        active_adapter = await broker_router.select_adapter(criteria={"symbol": symbol, "order_type": order_type})
        if not active_adapter:
            logger.error(f"Priv No active broker adapter found for {symbol} {order_type}. Cannot send order.")
            break

        order_id = await active_adapter.send_order(
            order_type=order_type,
            symbol=symbol,
            volume=volume,
            price=price_to_use,
            slippage=deviation,
            stop_loss=sl_price,
            take_profit=tp_price,
            comment=comment,
            magic_number=magic_number
        )
        if order_id:
            logger.info(f"Priv Pending {order_type} order for {symbol} (Vol: {volume}, Price: {entry_price}) placed via {active_adapter.name}. Order ID: {order_id}")
            set_trade_time_level(symbol, order_type)
            break
        else:
            tries += 1
            logger.error(f"Priv Attempt {tries}/{max_tries}: Failed to place pending {order_type} order for {symbol}.")
            if tries < max_tries:
                await asyncio.sleep(retry_time_seconds)
    
    return order_id

async def close_position_by_id(
    order_id: Union[int, str],
    volume: float,
    symbol: str,
    current_prices: Dict[str, float],
    order_type: str,
    deviation: int = DEFAULT_SLIPPAGE
) -> bool:
    close_price = current_prices["bid"] if order_type.upper() == "BUY" else current_prices["ask"]
    tries = 0
    max_tries = 5
    retry_time_seconds = 1
    result = False

    while tries < max_tries:
        active_adapter = await broker_router.select_adapter(criteria={"symbol": symbol, "order_id": order_id, "action_type": f"CLOSE_{order_type}"})
        if not active_adapter:
            logger.error(f"Priv No active broker adapter found to close {symbol} {order_type} {order_id}. Cannot close position.")
            break

        result = await active_adapter.close_position(order_id, volume, close_price, deviation)
        if result:
            logger.info(f"Priv Position {order_id} ({symbol}) closed successfully at {close_price} via {active_adapter.name}.")
            break
        else:
            tries += 1
            logger.error(f"Priv Attempt {tries}/{max_tries}: Failed to close position {order_id} ({symbol}).")
            if tries < max_tries:
                await asyncio.sleep(retry_time_seconds)
    
    return result

async def modify_position_sltp(
    order_id: Union[int, str],
    symbol: str,
    new_sl_price: Optional[float] = None,
    new_tp_price: Optional[float] = None
) -> bool:
    if new_sl_price is None and new_tp_price is None:
        logger.info(f"Priv No valid SL or TP provided for modification of order {order_id}.")
        return False

    tries = 0
    max_tries = 5
    retry_time_seconds = 1
    result = False

    while tries < max_tries:
        active_adapter = await broker_router.select_adapter(criteria={"symbol": symbol, "order_id": order_id})
        if not active_adapter:
            logger.error(f"Priv No active broker adapter found to modify {symbol} {order_id}. Cannot modify position.")
            break

        result = await active_adapter.modify_position(order_id, new_sl_price, new_tp_price)
        if result:
            logger.info(f"Priv Position {order_id} ({symbol}) modified with SL: {new_sl_price}, TP: {new_tp_price} via {active_adapter.name}.")
            break
        else:
            tries += 1
            logger.error(f"Priv Attempt {tries}/{max_tries}: Failed to modify position {order_id} ({symbol}).")
            if tries < max_tries:
                await asyncio.sleep(retry_time_seconds)
    
    return result

async def modify_pending_order_sltp(
    order_id: Union[int, str],
    new_sl_price: Optional[float] = None,
    new_tp_price: Optional[float] = None
) -> bool:
    logger.warning(f"Priv: `modify_pending_order_sltp` is simplified. Attempting to modify via standard modify_position.")
    all_pending_orders = []
    
    for adapter in broker_router.adapters:
        if adapter.is_connected:
            all_pending_orders.extend(await adapter.get_pending_orders())

    target_order = next((o for o in all_pending_orders if o.get("id") == order_id), None)
    if not target_order:
        logger.warning(f"Priv: Pending order {order_id} not found across adapters for modification.")
        return False
    
    symbol = target_order.get("symbol")
    if not symbol:
        logger.error(f"Priv: Could not determine symbol for pending order {order_id}. Cannot modify.")
        return False

    return await modify_position_sltp(order_id, symbol, new_sl_price, new_tp_price)


async def delete_pending_order(order_id: Union[int, str]) -> bool:
    active_adapter = await broker_router.select_adapter(criteria={"order_id": order_id, "action_type": "delete_pending"})
    if not active_adapter:
        logger.error(f"Priv No active broker adapter found for pending order deletion. Cannot delete order {order_id}.")
        return False
    return await active_adapter.delete_pending_order(order_id)

async def apply_trailing_pending_orders(
    pending_orders: List[Dict[str, Any]],
    symbol_prices_map: Dict[str, Dict[str, float]],
    symbol_info_map: Dict[str, Dict[str, Any]],
    st_tr_stop_points: int,
    st_tr_step_points: int,
    lim_tr_stop_points: int,
    lim_tr_step_points: int
) -> None:
    for order in pending_orders:
        symbol = order["symbol"]
        order_type = order["type"]
        entry_price = order["price"]
        current_symbol_prices = symbol_prices_map.get(symbol)
        symbol_metadata = symbol_info_map.get(symbol)
        if not current_symbol_prices or not symbol_metadata: continue

        point_size = symbol_metadata.get("point", 0.0001)
        current_market_price = current_symbol_prices["bid"] if "BUY" in order_type.upper() else current_symbol_prices["ask"]
        should_modify = False
        new_pending_price = entry_price
        new_sl = order.get("stop_loss")
        new_tp = order.get("take_profit")

        if "LIMIT" in order_type.upper():
            tr_stop = lim_tr_stop_points
            tr_step = lim_tr_step_points
            if tr_stop <= 0 or tr_step <= 0: continue
            if "BUY_LIMIT" in order_type.upper() and current_market_price > entry_price + (tr_stop + tr_step) * point_size:
                new_pending_price = current_market_price - tr_stop * point_size
                should_modify = True
            elif "SELL_LIMIT" in order_type.upper() and current_market_price < entry_price - (tr_stop + tr_step) * point_size:
                new_pending_price = current_market_price + tr_stop * point_size
                should_modify = True
        elif "STOP" in order_type.upper() and "TRAILING_STOP" not in order_type.upper():
            tr_stop = st_tr_stop_points
            tr_step = st_tr_step_points
            if tr_stop <= 0 or tr_step <= 0: continue
            if "BUY_STOP" in order_type.upper() and current_market_price < entry_price - (tr_stop + tr_step) * point_size:
                new_pending_price = current_market_price + tr_stop * point_size
                should_modify = True
            elif "SELL_STOP" in order_type.upper() and current_market_price > entry_price + (tr_stop + tr_step) * point_size:
                new_pending_price = current_market_price - tr_stop * point_size
                should_modify = True

        if should_modify:
            min_dist = symbol_metadata.get("stops_level", MIN_STOP_LEVEL_POINTS) * point_size
            is_valid = True
            if "BUY_LIMIT" in order_type.upper() and current_market_price - new_pending_price < min_dist: is_valid = False
            elif "BUY_STOP" in order_type.upper() and new_pending_price - current_market_price < min_dist: is_valid = False
            elif "SELL_LIMIT" in order_type.upper() and new_pending_price - current_market_price < min_dist: is_valid = False
            elif "SELL_STOP" in order_type.upper() and current_market_price - new_pending_price < min_dist: is_valid = False

            if is_valid:
                sl_dist = abs(entry_price - order.get("stop_loss", 0))
                tp_dist = abs(entry_price - order.get("take_profit", 0))
                if order.get("stop_loss"): new_sl = new_pending_price - sl_dist if "BUY" in order_type.upper() else new_pending_price + sl_dist
                if order.get("take_profit"): new_tp = new_pending_price + tp_dist if "BUY" in order_type.upper() else new_pending_price - tp_dist
                await modify_pending_order_sltp(order["id"], new_sl, new_tp)
            else:
                logger.warning(f"Skipping trail for pending order {order['id']} as new price is too close to market.")

async def apply_trailing_stop(
    position: Dict[str, Any], current_prices: Dict[str, float], symbol_info: Dict[str, Any],
    trailing_stop_points: int, trailing_step_points: int, wait_profit_to_trail: bool
) -> bool:
    if trailing_stop_points <= 0 or trailing_step_points <= 0: return False
    point = symbol_info.get("point", 0.00001)
    digits = symbol_info.get("digits", DEFAULT_DIGITS)
    sl = position.get("stop_loss")
    entry = position["entry_price"]
    symbol = position["symbol"]
    
    if position["type"].upper() == "BUY":
        price = current_prices["bid"]
        if wait_profit_to_trail and price < entry + trailing_stop_points * point: return False
        new_sl = price - trailing_stop_points * point
        if sl is None or new_sl > sl + trailing_step_points * point:
            return await modify_position_sltp(position["id"], symbol, new_sl_price=_normalize_price(new_sl, digits))
    elif position["type"].upper() == "SELL":
        price = current_prices["ask"]
        if wait_profit_to_trail and price > entry - trailing_stop_points * point: return False
        new_sl = price + trailing_stop_points * point
        if sl is None or new_sl < sl - trailing_step_points * point:
            return await modify_position_sltp(position["id"], symbol, new_sl_price=_normalize_price(new_sl, digits))
    return False

async def apply_move_to_breakeven(
    position: Dict[str, Any], current_prices: Dict[str, float], symbol_info: Dict[str, Any],
    profit_to_move_points: int, pips_to_move_sl: int
) -> bool:
    if profit_to_move_points <= 0: return False
    point = symbol_info.get("point", 0.00001)
    digits = symbol_info.get("digits", DEFAULT_DIGITS)
    sl = position.get("stop_loss")
    entry = position["entry_price"]
    symbol = position["symbol"]
    offset = pips_to_move_sl * point
    
    if position["type"].upper() == "BUY":
        price = current_prices["bid"]
        if price >= entry + profit_to_move_points * point:
            new_sl = entry + offset
            if sl is None or new_sl > sl:
                return await modify_position_sltp(position["id"], symbol, new_sl_price=_normalize_price(new_sl, digits))
    elif position["type"].upper() == "SELL":
        price = current_prices["ask"]
        if price <= entry - profit_to_move_points * point:
            new_sl = entry - offset
            if sl is None or new_sl < sl:
                return await modify_position_sltp(position["id"], symbol, new_sl_price=_normalize_price(new_sl, digits))
    return False

async def manage_global_equity_levels(
    account_equity: float, account_balance: float, global_tp_pct: float, global_sl_pct: float,
    symbol_prices_map: Dict[str, Dict[str, float]], magic: int
) -> bool:
    if global_tp_pct <= 0 and global_sl_pct <= 0: return False
    tp_thresh = account_balance * (1 + global_tp_pct / 100.0)
    sl_thresh = account_balance * (1 - global_sl_pct / 100.0)
    triggered = False

    if global_tp_pct > 0 and account_equity >= tp_thresh:
        logger.info(f"Global TP triggered! Equity ({account_equity:.2f}) >= Threshold ({tp_thresh:.2f}).")
        triggered = True
    elif global_sl_pct > 0 and account_equity <= sl_thresh:
        logger.warning(f"Global SL triggered! Equity ({account_equity:.2f}) <= Threshold ({sl_thresh:.2f}).")
        triggered = True

    if triggered:
        active_adapter = await broker_router.select_adapter()
        if not active_adapter: return False
        positions = await active_adapter.get_open_positions()
        for pos in [p for p in positions if p.get("magic") == magic]:
            prices = symbol_prices_map.get(pos["symbol"])
            if prices: await close_position_by_id(pos["id"], pos["volume"], pos["symbol"], prices, pos["type"])
        return True
    return False

async def apply_pipsing_close(
    position: Dict[str, Any], current_prices: Dict[str, float], symbol_info: Dict[str, Any], profit_points: int
) -> bool:
    if profit_points <= 0: return False
    point = symbol_info.get("point", 0.00001)
    entry = position["entry_price"]
    symbol = position["symbol"]
    
    if position["type"].upper() == "BUY":
        if (current_prices["bid"] - entry) / point >= profit_points:
            return await close_position_by_id(position["id"], position["volume"], symbol, current_prices, position["type"])
    elif position["type"].upper() == "SELL":
        if (entry - current_prices["ask"]) / point >= profit_points:
            return await close_position_by_id(position["id"], position["volume"], symbol, current_prices, position["type"])
    return False

async def manage_trades(
    account_state: Dict[str, Any], symbol_prices_map: Dict[str, Dict[str, float]],
    symbol_info_map: Dict[str, Dict[str, Any]], ai_magic_number: int = DEFAULT_MAGIC_NUMBER,
    enable_trailing_stop: bool = False, trailing_stop_points: int = 0, trailing_step_points: int = 0,
    wait_profit_to_trail: bool = True, enable_move_to_breakeven: bool = False, profit_to_move_be_points: int = 0,
    pips_to_move_be_sl: int = 0, enable_global_levels: bool = False, global_take_profit_percent: float = 0.0,
    global_stop_loss_percent: float = 0.0, enable_pipsing: bool = False, pipsing_profit_points: int = 0
) -> None:
    if enable_global_levels and await manage_global_equity_levels(account_state.get("equity", 0.0), account_state.get("balance", 0.0), global_take_profit_percent, global_stop_loss_percent, symbol_prices_map, ai_magic_number):
        return

    active_adapter = await broker_router.select_adapter()
    if not active_adapter: return
    
    open_positions = await active_adapter.get_open_positions()
    pending_orders = await active_adapter.get_pending_orders()

    await apply_trailing_pending_orders(pending_orders, symbol_prices_map, symbol_info_map, trailing_stop_points, trailing_step_points, trailing_stop_points, trailing_step_points)

    for pos in [p for p in open_positions if p.get("magic") == ai_magic_number]:
        prices = symbol_prices_map.get(pos["symbol"])
        info = symbol_info_map.get(pos["symbol"])
        if not prices or not info: continue

        if enable_pipsing and await apply_pipsing_close(pos, prices, info, pipsing_profit_points): continue
        if enable_move_to_breakeven: await apply_move_to_breakeven(pos, prices, info, profit_to_move_be_points, pips_to_move_be_sl)
        if enable_trailing_stop: await apply_trailing_stop(pos, prices, info, trailing_stop_points, trailing_step_points, wait_profit_to_trail)