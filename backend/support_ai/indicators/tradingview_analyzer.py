# backend/support_ai/indicators/tradingview_analyzer.py

import logging
from typing import Dict, Any, Optional

# Make tradingview_ta optional
try:
    from tradingview_ta import TA_Handler, Interval
    TRADINGVIEW_AVAILABLE = True
except ImportError:
    TRADINGVIEW_AVAILABLE = False
    TA_Handler = None
    Interval = None
    logger = logging.getLogger(__name__)
    logger.warning("tradingview_ta not available. TradingView analysis will be disabled.")

logger = logging.getLogger(__name__)

class TradingViewAnalyzer:
    """
    Integrates with the tradingview_ta library to provide real-time technical analysis,
    including indicators, chart patterns, and market heatmaps.
    """
    def __init__(self):
        pass

    def get_technical_analysis(self, symbol: str, screener: str, exchange: str, interval: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a comprehensive technical analysis summary from TradingView.
        """
        try:
            handler = TA_Handler(
                symbol=symbol,
                screener=screener,
                exchange=exchange,
                interval=interval
            )
            analysis = handler.get_analysis()
            return analysis.__dict__
        except Exception as e:
            logger.error(f"Failed to get TradingView analysis for {symbol}: {e}", exc_info=True)
            return None

# Example usage:
# analyzer = TradingViewAnalyzer()
# analysis = analyzer.get_technical_analysis(symbol="EURUSD", screener="forex", exchange="FX_IDC", interval=Interval.INTERVAL_4_HOURS)
# if analysis:
#     print(analysis)
