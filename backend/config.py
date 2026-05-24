# backend/config.py
# Centralized configuration module for the Sans Mercantile application.

import os
from pydantic import BaseModel, field_validator, ConfigDict
from dotenv import load_dotenv
from enum import Enum
from typing import Optional, List

# Load environment variables from .env file
load_dotenv()

# Legacy import shim for 'from backend.config import settings'
import sys
import types
_IS_TEST = any('pytest' in arg or 'unittest' in arg for arg in sys.argv) or os.getenv('DEMO_MODE', 'false').lower() == 'true' or os.getenv('SANDBOX_MODE', 'false').lower() == 'true'

class TradingStrategyMode(str, Enum):
    """
    Enum for trading strategy modes. This allows for dynamic switching
    of the AI's core trading logic without needing a restart.
    """
    FUNDAMENTAL_ONLY = "FUNDAMENTAL_ONLY"
    TECHNICAL_ONLY = "TECHNICAL_ONLY"
    BOTH = "BOTH"
    NONE = "NONE"

class Settings:
    """Main settings for the application. Uses os.getenv() to avoid automatic env validation."""
    
    APP_NAME: str = "Sans Mercantile PRIV AI"
    APP_VERSION: str = "2.0.0"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001", "http://localhost:8000"]
    GCP_PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "sans-mercantile-devops")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "false").lower() == "true"
    
    # --- Background Task Configuration ---
    NEWS_FETCH_INTERVAL_SECONDS: int = int(os.getenv("NEWS_FETCH_INTERVAL_SECONDS", "300"))  # 5 minutes default
    ARBITRAGE_SCAN_INTERVAL_SECONDS: int = int(os.getenv("ARBITRAGE_SCAN_INTERVAL_SECONDS", "60"))  # 1 minute default
    
    def __init__(self):
        """Copy all class-level attributes to instance attributes for compatibility."""
        # Explicitly assign critical attributes that agents expect
        self.NEWS_FETCH_INTERVAL_SECONDS = self.__class__.NEWS_FETCH_INTERVAL_SECONDS
        self.ARBITRAGE_SCAN_INTERVAL_SECONDS = self.__class__.ARBITRAGE_SCAN_INTERVAL_SECONDS
        self.ALLOWED_ORIGINS = self.__class__.ALLOWED_ORIGINS
        
        # Copy all other class attributes
        for attr_name in dir(self.__class__):
            if not attr_name.startswith('_') and attr_name not in ('__init__', 'NEWS_FETCH_INTERVAL_SECONDS', 'ARBITRAGE_SCAN_INTERVAL_SECONDS', 'ALLOWED_ORIGINS'):
                try:
                    attr_value = getattr(self.__class__, attr_name)
                    # Only copy data attributes, not methods
                    if not callable(attr_value):
                        setattr(self, attr_name, attr_value)
                except AttributeError:
                    pass

    # --- Database Configuration ---
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+psycopg2://user:password@host/db")
    CLOUD_SQL_INSTANCE_CONNECTION_NAME: Optional[str] = os.getenv("CLOUD_SQL_INSTANCE_CONNECTION_NAME")
    DB_USER: Optional[str] = os.getenv("DB_USER")
    DB_PASS: Optional[str] = os.getenv("DB_PASS")
    DB_NAME: Optional[str] = os.getenv("DB_NAME")

    # --- Broker Configurations ---
    ENABLE_MOCK_ADAPTER: bool = os.getenv("ENABLE_MOCK_ADAPTER", "true").lower() == "true"
    
    ENABLE_ALPACA_PAPER_ADAPTER: bool = os.getenv("ENABLE_ALPACA_PAPER_ADAPTER", "false").lower() == "true"
    ALPACA_PAPER_API_KEY_ID: str = os.getenv("ALPACA_PAPER_API_KEY_ID", "")
    ALPACA_PAPER_SECRET_KEY: str = os.getenv("ALPACA_PAPER_SECRET_KEY", "")
    
    ENABLE_ALPACA_ADAPTER: bool = os.getenv("ENABLE_ALPACA_ADAPTER", "false").lower() == "true"
    ENABLE_ALPACA_SANDBOX_ADAPTER: bool = os.getenv("ENABLE_ALPACA_SANDBOX_ADAPTER", "false").lower() == "true"
    ALPACA_API_KEY: Optional[str] = os.getenv("ALPACA_API_KEY")
    ALPACA_SECRET_KEY: Optional[str] = os.getenv("ALPACA_SECRET_KEY")

    ENABLE_DERIV_ADAPTER: bool = os.getenv("ENABLE_DERIV_ADAPTER", "false").lower() == "true"
    DERIV_APP_ID: Optional[str] = os.getenv("DERIV_APP_ID")
    # Accept common alternative env names for the Deriv API token to be tolerant of user naming
    DERIV_API_TOKEN: Optional[str] = os.getenv("DERIV_API_TOKEN") or os.getenv("Deriv_API_Token") or os.getenv("DERIV_API_TOKEN_KEY") or os.getenv("DERIV_API_TOKEN")

    ENABLE_DERIV_APP_CONSOLE_ADAPTER: bool = os.getenv("ENABLE_DERIV_APP_CONSOLE_ADAPTER", "false").lower() == "true"
    DERIV_APP_CONSOLE_APP_ID: int = int(os.getenv("DERIV_APP_CONSOLE_APP_ID", 0))
    DERIV_APP_CONSOLE_API_TOKEN: Optional[str] = os.getenv("DERIV_APP_CONSOLE_API_TOKEN")

    ENABLE_DERIV_PRIV1_ADAPTER: bool = os.getenv("ENABLE_DERIV_PRIV1_ADAPTER", "false").lower() == "true"
    DERIV_PRIV1_APP_ID: int = int(os.getenv("DERIV_PRIV1_APP_ID", 0))
    DERIV_PRIV1_API_TOKEN: Optional[str] = os.getenv("DERIV_PRIV1_API_TOKEN")

    BINANCE_API_KEY: str = os.getenv("BINANCE_API_KEY", "")
    BINANCE_SECRET_KEY: str = os.getenv("BINANCE_SECRET_KEY", "")

    ENABLE_MT5_ADAPTER: bool = os.getenv("ENABLE_MT5_ADAPTER", "false").lower() == "true"
    MT5_SERVER: str = os.getenv("MT5_SERVER", "YourBroker-Server")
    # MT5_LOGIN needs to be int but might have placeholder string - use default
    MT5_LOGIN: Optional[int] = 0  # Default value
    MT5_PASSWORD: str = os.getenv("MT5_PASSWORD", "")
    MT5_PATH: str = os.getenv("MT5_PATH", "")

    ENABLE_XM_ADAPTER: bool = os.getenv("ENABLE_XM_ADAPTER", "false").lower() == "true"
    XM_ACCOUNT_ID: Optional[int] = int(os.getenv("XM_ACCOUNT_ID", 0)) if os.getenv("XM_ACCOUNT_ID") else None
    XM_PASSWORD: Optional[str] = os.getenv("XM_PASSWORD")

    # --- Interactive Brokers Configuration ---
    ENABLE_IB_ADAPTER: bool = os.getenv("ENABLE_IB_ADAPTER", "false").lower() == "true"
    IB_HOST: str = os.getenv("IB_HOST", "127.0.0.1")
    IB_PORT: int = int(os.getenv("IB_PORT", "7497"))  # 7497 for paper, 7496 for live
    IB_CLIENT_ID: int = int(os.getenv("IB_CLIENT_ID", "1"))
    IB_ACCOUNT: Optional[str] = os.getenv("IB_ACCOUNT")  # Optional: specific account number
    IB_READONLY: bool = os.getenv("IB_READONLY", "false").lower() == "true"

    TRADING_BROKER_ROUTER: str = os.getenv("TRADING_BROKER_ROUTER", "default_broker_router")
    
    # --- Data Provider Configurations ---
    TWELVEDATA_API_KEY: str = os.getenv("TWELVEDATA_API_KEY", "")
    TWELVEDATA_BASE_URL: str = "https://api.twelvedata.com"
    SIMFIN_API_KEY: str = os.getenv("SIMFIN_API_KEY", "")
    SIMFIN_BASE_URL: str = "https://simfin.com/api/v2"
    EODHD_API_KEY: str = os.getenv("EODHD_API_KEY", "")
    EODHD_BASE_URL: str = "https://eodhistoricaldata.com/api"
    POLYGON_API_KEY: str = os.getenv("POLYGON_API_KEY", "")
    POLYGON_BASE_URL: str = "https://api.polygon.io"
    FINNHUB_API_KEY: str = os.getenv("FINNHUB_API_KEY", "")
    FINNHUB_BASE_URL: str = "https://finnhub.io/api/v1"
    ECONOMIC_CALENDAR_URL: str = "https://www.investing.com/economic-calendar/"
    NEWS_API_KEY_AI: str = os.getenv("NEWS_API_KEY_AI", "")
    NEWS_API_KEY_ORG: str = os.getenv("NEWS_API_KEY_ORG", "")

    # --- RSS / News Ingestion Defaults ---
    COMMODITY_NEWS_RSS_LIMIT: int = int(os.getenv("COMMODITY_NEWS_RSS_LIMIT", "3"))
    FUTURES_NEWS_RSS_LIMIT: int = int(os.getenv("FUTURES_NEWS_RSS_LIMIT", "3"))
    CREDIT_NEWS_RSS_LIMIT: int = int(os.getenv("CREDIT_NEWS_RSS_LIMIT", "3"))

    D_ID_API_KEY: Optional[str] = os.getenv("D_ID_API_KEY")

    # --- Governance & Simulation ---
    ETHICAL_PRINCIPLES_PATH: str = "backend/governance/ethical_principles.json"
    COMPLIANCE_RULES_PATH: str = "backend/governance/compliance_rules.json"
    POLICY_DEFINITIONS_PATH: str = "backend/governance/policies.json"

    # --- Advanced Computing & Security ---
    PQC_ENCRYPTION_ENABLED: bool = True
    QUANTUM_ENDPOINT: Optional[str] = os.getenv("QUANTUM_ENDPOINT")
    QUANTUM_API_KEY: Optional[str] = os.getenv("QUANTUM_API_KEY")
    NEUROMORPHIC_ENDPOINT: Optional[str] = os.getenv("NEUROMORPHIC_ENDPOINT")
    NEUROMORPHIC_API_KEY: Optional[str] = os.getenv("NEUROMORPHIC_API_KEY")
    BLOCKCHAIN_PROVIDER_URL: Optional[str] = os.getenv("BLOCKCHAIN_PROVIDER_URL")
    BLOCKCHAIN_LOGGER_PRIVATE_KEY: Optional[str] = os.getenv("BLOCKCHAIN_LOGGER_PRIVATE_KEY")
    BLOCKCHAIN_LOGGER_CONTRACT_ADDRESS: Optional[str] = os.getenv("BLOCKCHAIN_LOGGER_CONTRACT_ADDRESS")
    KMS_KEY_RING_NAME: str = os.getenv("KMS_KEY_RING_NAME", "priv-zkp-keys")
    KMS_LOCATION: str = os.getenv("KMS_LOCATION", "global")
    PROVING_KEY_NAME: str = os.getenv("PROVING_KEY_NAME", "priv-halo2-proving-key")
    VERIFICATION_KEY_NAME: str = os.getenv("VERIFICATION_KEY_NAME", "priv-halo2-verification-key")

    # --- Multi-Cloud Capabilities ---
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    AZURE_TENANT_ID: Optional[str] = os.getenv("AZURE_TENANT_ID")
    AZURE_CLIENT_ID: Optional[str] = os.getenv("AZURE_CLIENT_ID")
    AZURE_CLIENT_SECRET: Optional[str] = os.getenv("AZURE_CLIENT_SECRET")

    # --- Watchdog Configuration ---
    ENABLE_WATCHDOG: bool = os.getenv("ENABLE_WATCHDOG", "true").lower() == "true"

    # The main interval for the watchdog's check loop.
    WATCHDOG_INTERVAL_SECONDS: int = int(os.getenv("WATCHDOG_INTERVAL_SECONDS", "60"))

    # What action to take when a critical issue is found.
    # Options: "LOG_ONLY", "CRITICAL_ALERT", "SHUTDOWN_AI_TRADING", "FULL_SHUTDOWN"
    WATCHDOG_ESCALATION_LEVEL: str = os.getenv("WATCHDOG_ESCALATION_LEVEL", "CRITICAL_ALERT")

    # Comma-separated list of emails for alerts.
    WATCHDOG_ALERT_EMAIL_RECIPIENTS: List[str] = [
        email.strip() for email in os.getenv("WATCHDOG_ALERT_EMAIL_RECIPIENTS", "").split(',') if email.strip()
    ]
    WATCHDOG_ALERT_PUBSUB_TOPIC: str = os.getenv("WATCHDOG_ALERT_PUBSUB_TOPIC", "priv-watchdog-alerts")
    WATCHDOG_HUMAN_OVERRIDE_TIMEOUT_MINUTES: int = int(os.getenv("WATCHDOG_HUMAN_OVERRIDE_TIMEOUT_MINUTES", "60"))

    # --- Performance & Health Thresholds ---
    WATCHDOG_DB_LATENCY_THRESHOLD_MS: int = int(os.getenv("WATCHDOG_DB_LATENCY_THRESHOLD_MS", "1500"))
    WATCHDOG_FIRESTORE_LATENCY_THRESHOLD_MS: int = int(os.getenv("WATCHDOG_FIRESTORE_LATENCY_THRESHOLD_MS", "1500"))
    WATCHDOG_EXTERNAL_API_ERROR_RATE_THRESHOLD: float = float(os.getenv("WATCHDOG_EXTERNAL_API_ERROR_RATE_THRESHOLD", "0.05")) # 5%
    WATCHDOG_MEMORY_USAGE_THRESHOLD_PERCENT: int = int(os.getenv("WATCHDOG_MEMORY_USAGE_THRESHOLD_PERCENT", "90"))
    WATCHDOG_CPU_USAGE_THRESHOLD_PERCENT: int = int(os.getenv("WATCHDOG_CPU_USAGE_THRESHOLD_PERCENT", "90"))

    # --- Technical Agent Defaults (sensible safe defaults to avoid AttributeError) ---
    TECHNICAL_AGENT_ANALYSIS_INTERVAL_SECONDS: int = int(os.getenv("TECHNICAL_AGENT_ANALYSIS_INTERVAL_SECONDS", "10"))
    TECHNICAL_AGENT_SYMBOLS_TO_ANALYZE: list = ["EURUSD", "GBPUSD"]
    TECHNICAL_AGENT_TIMEFRAME: str = os.getenv("TECHNICAL_AGENT_TIMEFRAME", "daily")
    TECHNICAL_AGENT_LOOKBACK_BARS: int = int(os.getenv("TECHNICAL_AGENT_LOOKBACK_BARS", "250"))
    TECHNICAL_AGENT_SYMBOL_DELAY_SECONDS: float = float(os.getenv("TECHNICAL_AGENT_SYMBOL_DELAY_SECONDS", "0.5"))
    TECHNICAL_AGENT_CRITICAL_SYMBOLS_FOR_REALTIME_ANALYSIS: list = ["EURUSD"]
    TECHNICAL_RSI_OVERBOUGHT: int = int(os.getenv("TECHNICAL_RSI_OVERBOUGHT", "70"))
    TECHNICAL_RSI_OVERSOLD: int = int(os.getenv("TECHNICAL_RSI_OVERSOLD", "30"))
    TECHNICAL_MACD_BULLISH_THRESHOLD: float = float(os.getenv("TECHNICAL_MACD_BULLISH_THRESHOLD", "0.1"))
    TECHNICAL_MACD_BEARISH_THRESHOLD: float = float(os.getenv("TECHNICAL_MACD_BEARISH_THRESHOLD", "-0.1"))
    TECHNICAL_SMA_CROSSOVER_THRESHOLD_PCT: float = float(os.getenv("TECHNICAL_SMA_CROSSOVER_THRESHOLD_PCT", "0.005"))
    TECHNICAL_MIN_CONFIRMATIONS: int = int(os.getenv("TECHNICAL_MIN_CONFIRMATIONS", "2"))
    TECHNICAL_CONFIDENCE_PER_SIGNAL: float = float(os.getenv("TECHNICAL_CONFIDENCE_PER_SIGNAL", "0.15"))
    TECHNICAL_TRADE_PROPOSAL_VOLUME: float = float(os.getenv("TECHNICAL_TRADE_PROPOSAL_VOLUME", "0.05"))

    # --- Real-time IoT Sensor Configuration (MQTT) ---
    ENABLE_REAL_IOT_SENSORS: bool = True
    MQTT_BROKER_URL: str = os.getenv("MQTT_BROKER_URL", "mqtt.eclipse.org")
    MQTT_BROKER_PORT: int = int(os.getenv("MQTT_BROKER_PORT", 1883))
    MQTT_TOPIC_ENVIRONMENTAL: str = os.getenv("MQTT_TOPIC_ENVIRONMENTAL", "sans-mercantile/iot/environmental")
    MQTT_USERNAME: Optional[str] = os.getenv("MQTT_USERNAME")
    MQTT_PASSWORD: Optional[str] = os.getenv("MQTT_PASSWORD")

    # --- AI & Adapter Configurations ---
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    ENABLE_AZURE_ADAPTER: bool = False
    AZURE_OPENAI_ENDPOINT: str = str(os.getenv("AZURE_OPENAI_ENDPOINT", ""))
    AZURE_OPENAI_KEY: str = str(os.getenv("AZURE_OPENAI_KEY", ""))
    AZURE_OPENAI_DEPLOYMENT_NAME: str = str(os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", ""))
    OPENAI_API_VERSION: str = str(os.getenv("OPENAI_API_VERSION", "2023-05-15"))
    LLM_MODEL_NAME: str = os.getenv("LLM_MODEL_NAME", "gpt-4o-mini")
    LIVE_MODEL_DIR: str = os.getenv("LIVE_MODEL_DIR", "models/live")
    PORTFOLIO_UPDATES_TOPIC: str = os.getenv("PORTFOLIO_UPDATES_TOPIC", "priv-portfolio-updates")
    UVICORN_PORT: int = int(os.getenv("UVICORN_PORT", 8000))
    SENDGRID_API_KEY: Optional[str] = os.getenv("SENDGRID_API_KEY")
    TWILIO_ACCOUNT_SID: Optional[str] = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: Optional[str] = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER: Optional[str] = os.getenv("TWILIO_PHONE_NUMBER")
    CONVERSATION_LOG_PATH: str = os.getenv("CONVERSATION_LOG_PATH", "logs/conversation_log.jsonl")

    # --- Venture Adapter Configurations ---
    HEALTHCARE_API_KEY: Optional[str] = os.getenv("HEALTHCARE_API_KEY")
    HEALTHCARE_API_ENDPOINT: Optional[str] = os.getenv("HEALTHCARE_API_ENDPOINT")
    LEGAL_API_KEY: Optional[str] = os.getenv("LEGAL_API_KEY")
    LEGAL_API_ENDPOINT: Optional[str] = os.getenv("LEGAL_API_ENDPOINT")

    # --- Strategy & Kill Switch ---
    TRADING_STRATEGY_MODE: TradingStrategyMode = TradingStrategyMode.NONE
    KILL_SWITCH_AI_TRADING: bool = False

    def __init__(self):
        """
        Initialize instance with all class attributes as instance attributes.
        This ensures CORS middleware can read ALLOWED_ORIGINS correctly.
        """
        # Copy all class attributes to instance
        for key in dir(self.__class__):
            if not key.startswith('_') and key != 'TRADING_STRATEGY_MODE' and key != 'KILL_SWITCH_AI_TRADING':
                try:
                    setattr(self, key, getattr(self.__class__, key))
                except:
                    pass
        
        # Check if we are running in a Google Cloud environment or if a specific
        # Cloud SQL instance is configured.
        is_cloud_run = "K_SERVICE" in os.environ
        use_cloud_sql = self.CLOUD_SQL_INSTANCE_CONNECTION_NAME and (is_cloud_run or not self.DEMO_MODE)

        if use_cloud_sql:
            # Environment is configured for Cloud SQL Auth Proxy via Unix Socket
            self.DATABASE_URL = (
                f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASS}@"
                f"/{self.DB_NAME}?host=/cloudsql/{self.CLOUD_SQL_INSTANCE_CONNECTION_NAME}"
            )
        elif self.DEMO_MODE:
            # DEMO_MODE is on and we're not using Cloud SQL, so use a standard local connection.
            # This assumes your .env file will provide a local DB_HOST (e.g., "localhost" or a Docker service name).
            db_host = os.getenv("DB_HOST", "localhost")
            self.DATABASE_URL = (
                 f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASS}@"
                 f"{db_host}:5432/{self.DB_NAME}"
            )
        # If neither of the above, it will fall back to the DATABASE_URL from the .env file.

settings = Settings()

# Explicitly ensure ALLOWED_ORIGINS and NEWS_FETCH_INTERVAL_SECONDS are accessible as instance attributes
# This is necessary because converting from Pydantic BaseModel to plain Python class means
# class attributes don't automatically become instance attributes
if not hasattr(settings, 'ALLOWED_ORIGINS') or settings.ALLOWED_ORIGINS is None:
    settings.ALLOWED_ORIGINS = ["http://localhost:3000", "http://localhost:3001", "http://localhost:8000"]

if not hasattr(settings, 'NEWS_FETCH_INTERVAL_SECONDS') or settings.NEWS_FETCH_INTERVAL_SECONDS is None:
    settings.NEWS_FETCH_INTERVAL_SECONDS = 300  # 5 minutes default

# Ensure ARBITRAGE_SCAN_INTERVAL_SECONDS is always available on the settings instance.
# Some code paths instantiate Settings using the later __init__ which doesn't copy
# the class-level ARBITRAGE_SCAN_INTERVAL_SECONDS. Provide a safe default here to
# avoid AttributeError during agent shutdown.
if not hasattr(settings, 'ARBITRAGE_SCAN_INTERVAL_SECONDS') or settings.ARBITRAGE_SCAN_INTERVAL_SECONDS is None:
    settings.ARBITRAGE_SCAN_INTERVAL_SECONDS = int(os.getenv("ARBITRAGE_SCAN_INTERVAL_SECONDS", "60"))  # 1 minute default

for _rss_key, _rss_default in (
    ("COMMODITY_NEWS_RSS_LIMIT", 3),
    ("FUTURES_NEWS_RSS_LIMIT", 3),
    ("CREDIT_NEWS_RSS_LIMIT", 3),
):
    if not hasattr(settings, _rss_key):
        setattr(settings, _rss_key, int(os.getenv(_rss_key, str(_rss_default))))

# Reduce watchdog aggressiveness when running in DEMO_MODE locally to avoid
# noisy shutdowns caused by strict resource checks during development.
if getattr(settings, 'DEMO_MODE', False):
    try:
        settings.WATCHDOG_MEMORY_USAGE_THRESHOLD_PERCENT = int(os.getenv('WATCHDOG_MEMORY_USAGE_THRESHOLD_PERCENT', '95'))
        settings.WATCHDOG_ESCALATION_LEVEL = os.getenv('WATCHDOG_ESCALATION_LEVEL', 'LOG_ONLY')
        settings.WATCHDOG_DB_LATENCY_THRESHOLD_MS = int(os.getenv('WATCHDOG_DB_LATENCY_THRESHOLD_MS', '5000'))
        settings.WATCHDOG_FIRESTORE_LATENCY_THRESHOLD_MS = int(os.getenv('WATCHDOG_FIRESTORE_LATENCY_THRESHOLD_MS', '5000'))
    except Exception:
        # Fallback: keep existing values if parsing fails
        pass

# Provide safe defaults for the Technical Agent configuration so the agent
# can start and stop cleanly even when environment variables are absent.
_tech_defaults = {
    'TECHNICAL_AGENT_ANALYSIS_INTERVAL_SECONDS': 10,
    'TECHNICAL_AGENT_SYMBOLS_TO_ANALYZE': ["EURUSD", "GBPUSD"],
    'TECHNICAL_AGENT_TIMEFRAME': 'daily',
    'TECHNICAL_AGENT_LOOKBACK_BARS': 250,
    'TECHNICAL_AGENT_SYMBOL_DELAY_SECONDS': 0.5,
    'TECHNICAL_AGENT_CRITICAL_SYMBOLS_FOR_REALTIME_ANALYSIS': ["EURUSD"],
    'TECHNICAL_RSI_OVERBOUGHT': 70,
    'TECHNICAL_RSI_OVERSOLD': 30,
    'TECHNICAL_MACD_BULLISH_THRESHOLD': 0.1,
    'TECHNICAL_MACD_BEARISH_THRESHOLD': -0.1,
    'TECHNICAL_SMA_CROSSOVER_THRESHOLD_PCT': 0.005,
    'TECHNICAL_MIN_CONFIRMATIONS': 2,
    'TECHNICAL_CONFIDENCE_PER_SIGNAL': 0.15,
    'TECHNICAL_TRADE_PROPOSAL_VOLUME': 0.05,
}
for _k, _v in _tech_defaults.items():
    if not hasattr(settings, _k):
        setattr(settings, _k, _v)

# Clean up temporary helper
try:
    del _tech_defaults
except Exception:
    pass
