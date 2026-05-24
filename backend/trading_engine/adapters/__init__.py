# backend/trading_engine/adapters/__init__.py
"""
Trading engine adapters with graceful import handling.
Each adapter is imported separately to avoid dependency conflicts.
"""

import logging

logger = logging.getLogger(__name__)

# Import each adapter with error handling
__all__ = []

try:
    from .alpaca_adapter import AlpacaAPIAdapter
    __all__.append("AlpacaAPIAdapter")
except Exception as e:
    logger.warning(f"Alpaca adapter not available: {e}")
    AlpacaAPIAdapter = None

try:
    from .binance_adapter import BinanceAdapter
    __all__.append("BinanceAdapter")
except Exception as e:
    logger.warning(f"Binance adapter not available: {e}")
    BinanceAdapter = None

try:
    from .deriv_adapter import DerivAPIAdapter
    __all__.append("DerivAPIAdapter")
except Exception as e:
    logger.warning(f"Deriv adapter not available: {e}")
    DerivAPIAdapter = None

try:
    from .mt5_adapter import MetaTrader5Adapter
    __all__.append("MetaTrader5Adapter")
except Exception as e:
    logger.warning(f"MT5 adapter not available: {e}")
    MetaTrader5Adapter = None

try:
    from .ib_adapter import InteractiveBrokersAdapter
    __all__.append("InteractiveBrokersAdapter")
except Exception as e:
    logger.warning(f"IB adapter not available: {e}")
    InteractiveBrokersAdapter = None
