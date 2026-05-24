"""Trading engine package exports.

Keep this module lightweight so importing submodules such as
`backend.trading_engine.broker_interface` does not eagerly import the full
trade executor stack and its heavy scientific dependencies.
"""

from importlib import import_module

__all__ = ["TradeExecutor", "TradingEngine"]


def __getattr__(name):
    if name in {"TradeExecutor", "TradingEngine"}:
        trade_executor = import_module(".trade_executor_class", __name__).TradeExecutor
        return trade_executor
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(__all__)


