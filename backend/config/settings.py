import os
from enum import Enum
from typing import ClassVar

class AGIPhase(str, Enum):
    INIT = "init"
    LEARNING = "learning"
    OPERATIONAL = "operational"
    MAINTENANCE = "maintenance"
    SHUTDOWN = "shutdown"
from pydantic import BaseModel, field_validator
from dotenv import load_dotenv
from enum import Enum
from typing import List, Optional

# Load environment variables from .env file
load_dotenv()

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
    """
    Settings class that uses os.getenv() for all values. NOT a BaseSettings to avoid env validation.

    PRODUCTION DEPLOYMENT:
    - Set DEMO_MODE=false in your environment
    - Provide real API keys (not demo-* keys)
    - The system will automatically detect demo keys and use mock data
    - See .env.production.example for required production configuration
    """

    # Background fetch intervals
    NEWS_FETCH_INTERVAL_SECONDS: int = int(os.getenv("NEWS_FETCH_INTERVAL_SECONDS", "300"))  # 5 minutes default
    ARBITRAGE_SCAN_INTERVAL_SECONDS: int = int(os.getenv("ARBITRAGE_SCAN_INTERVAL_SECONDS", "60"))  # 1 minute default

    # News API Keys - Use real keys in production (not demo-* keys)
    NEWS_API_KEY_ORG: str = os.getenv("NEWS_API_KEY_ORG", "demo-news-api-key-org")
    NEWS_API_KEY_AI: str = os.getenv("NEWS_API_KEY_AI", "demo-news-api-key-ai")

    WATCHDOG_ALERT_PUBSUB_TOPIC: str = "priv-watchdog-alerts"
    WATCHDOG_ALERT_EMAIL_RECIPIENTS: list = ["admin@example.com"]
    WATCHDOG_HUMAN_OVERRIDE_TIMEOUT_MINUTES: int = 30  # Default value, adjust as needed
    WATCHDOG_DB_LATENCY_THRESHOLD_MS: int = 500  # Default value, adjust as needed
    WATCHDOG_FIRESTORE_LATENCY_THRESHOLD_MS: int = 500  # Default value, adjust as needed
    WATCHDOG_EXTERNAL_API_ERROR_RATE_THRESHOLD: float = 0.05  # Default value, adjust as needed
    WATCHDOG_MEMORY_USAGE_THRESHOLD_PERCENT: float = 80.0  # Default value, adjust as needed
    WATCHDOG_CPU_USAGE_THRESHOLD_PERCENT: float = 90.0  # Default value, adjust as needed
    EODHD_BASE_URL: str = os.getenv("EODHD_BASE_URL", "https://eodhistoricaldata.com/api/")
    FINNHUB_API_KEY: str = os.getenv("FINNHUB_API_KEY", "demo")
    SIMFIN_BASE_URL: str = os.getenv("SIMFIN_BASE_URL", "https://simfin.com/api/v2/")
    WATCHDOG_ESCALATION_LEVEL: str = os.getenv("WATCHDOG_ESCALATION_LEVEL", "MEDIUM")

    # --- Inter-Agent Communication ---
    INTER_AGENT_COMMUNICATION_TOPIC: str = os.getenv("INTER_AGENT_COMMUNICATION_TOPIC", "priv-inter-agent-comm")
    """Main settings for the application."""
    APP_NAME: str = "Sans Mercantile PRIV AI"
    APP_VERSION: str = "2.0.0"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    GCP_PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "sans-mercantile-devops")
    OPENAI_API_KEY: Optional[str] = None
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "false").lower() == "true"

    # --- Database Configuration ---
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+psycopg2://user:password@host/db")
    CLOUD_SQL_INSTANCE_CONNECTION_NAME: Optional[str] = os.getenv("CLOUD_SQL_INSTANCE_CONNECTION_NAME")
    DB_USER: Optional[str] = os.getenv("DB_USER")
    DB_PASS: Optional[str] = os.getenv("DB_PASS")
    DB_NAME: Optional[str] = os.getenv("DB_NAME")

    # --- Broker Configurations ---
    ENABLE_ALPACA: bool = True
    ENABLE_BINANCE: bool = True
    ENABLE_DERIV: bool = True
    ENABLE_MT5: bool = False
    ENABLE_MOCK_BROKER: bool = True
    ENABLE_MOCK_ADAPTER: bool = os.getenv("ENABLE_MOCK_ADAPTER", "true").lower() == "true"
    ENABLE_ALPACA_PAPER_ADAPTER: bool = os.getenv("ENABLE_ALPACA_PAPER_ADAPTER", "false").lower() == "true"
    ENABLE_DERIV_APP_CONSOLE_ADAPTER: bool = os.getenv("ENABLE_DERIV_APP_CONSOLE_ADAPTER", "false").lower() == "true"
    ALPACA_API_KEY: str = os.getenv("ALPACA_API_KEY", "")
    # Accept multiple secret env var names for backwards compatibility
    ALPACA_SECRET_KEY: str = os.getenv("ALPACA_SECRET_KEY", "") or os.getenv("ALPACA_API_SECRET", "") or os.getenv("ALPACA_API_SECRET_KEY", "")
    ALPACA_PAPER_API_KEY_ID: str = os.getenv("ALPACA_PAPER_API_KEY_ID", "")
    ALPACA_PAPER_API_SECRET_KEY: str = os.getenv("ALPACA_PAPER_API_SECRET_KEY", "")
    BINANCE_API_KEY: str = os.getenv("BINANCE_API_KEY", "")
    BINANCE_SECRET_KEY: str = os.getenv("BINANCE_SECRET_KEY", "")
    DERIV_APP_ID: str = os.getenv("DERIV_APP_ID", "")
    DERIV_API_TOKEN: str = os.getenv("DERIV_API_TOKEN", "")
    DERIV_APP_CONSOLE_API_TOKEN: Optional[str] = os.getenv("DERIV_APP_CONSOLE_API_TOKEN")
    MT5_SERVER: str = os.getenv("MT5_SERVER", "")
    # Handle MT5_LOGIN specially - needs to be int but might have placeholder string
    MT5_LOGIN: Optional[int] = 0  # Default value
    MT5_PASSWORD: str = os.getenv("MT5_PASSWORD", "")
    MT5_PATH: str = os.getenv("MT5_PATH", "")
    
    # --- AI-Ops / Agent Defaults ---
    AI_OPS_MIN_CPU: float = float(os.getenv("AI_OPS_MIN_CPU", "5.0"))
    AI_OPS_MAX_CPU: float = float(os.getenv("AI_OPS_MAX_CPU", "80.0"))
    AI_OPS_MIN_MEMORY: float = float(os.getenv("AI_OPS_MIN_MEMORY", "30.0"))
    AI_OPS_MAX_MEMORY: float = float(os.getenv("AI_OPS_MAX_MEMORY", "85.0"))

    # --- FOMC / Feed defaults ---
    FOMC_CALENDAR_LOOKAHEAD_DAYS: int = int(os.getenv("FOMC_CALENDAR_LOOKAHEAD_DAYS", "7"))
    FOMC_NEWS_FETCH_LIMIT: int = int(os.getenv("FOMC_NEWS_FETCH_LIMIT", "5"))

    # --- Yield optimizer / alt data defaults ---
    YIELD_OPTIMIZER_SYMBOLS_TO_CHECK: List[str] = os.getenv("YIELD_OPTIMIZER_SYMBOLS_TO_CHECK", "").split(",") if os.getenv("YIELD_OPTIMIZER_SYMBOLS_TO_CHECK") else []
    ALT_DATA_NEWS_LIMIT: int = int(os.getenv("ALT_DATA_NEWS_LIMIT", "5"))

    # --- Technical agent defaults ---
    TECHNICAL_AGENT_ANALYSIS_INTERVAL_SECONDS: int = int(os.getenv("TECHNICAL_AGENT_ANALYSIS_INTERVAL_SECONDS", "300"))
    # Default symbols to analyze for the technical agent (prevents AttributeError when not set in env)
    TECHNICAL_AGENT_SYMBOLS_TO_ANALYZE: List[str] = os.getenv("TECHNICAL_AGENT_SYMBOLS_TO_ANALYZE", "EURUSD,GBPUSD").split(",") if os.getenv("TECHNICAL_AGENT_SYMBOLS_TO_ANALYZE") else ["EURUSD", "GBPUSD"]

    # --- Commodity / Futures / Credit news limits ---
    COMMODITY_NEWS_FETCH_LIMIT: int = int(os.getenv("COMMODITY_NEWS_FETCH_LIMIT", "5"))
    FUTURES_NEWS_FETCH_LIMIT: int = int(os.getenv("FUTURES_NEWS_FETCH_LIMIT", "5"))
    CREDIT_NEWS_FETCH_LIMIT: int = int(os.getenv("CREDIT_NEWS_FETCH_LIMIT", "5"))
    # Interval (seconds) for legal agent periodic fetch
    LEGAL_NEWS_FETCH_INTERVAL_SECONDS: int = int(os.getenv("LEGAL_NEWS_FETCH_INTERVAL_SECONDS", "3600"))
    COMMODITY_NEWS_FETCH_INTERVAL_SECONDS: int = int(os.getenv("COMMODITY_NEWS_FETCH_INTERVAL_SECONDS", "600"))
    FUTURES_NEWS_FETCH_INTERVAL_SECONDS: int = int(os.getenv("FUTURES_NEWS_FETCH_INTERVAL_SECONDS", "600"))

    UVICORN_PORT: int = int(os.getenv("UVICORN_PORT", 8000))

    # --- Data Provider Configurations ---
    TWELVEDATA_API_KEY: str = os.getenv("TWELVEDATA_API_KEY", "")
    SIMFIN_API_KEY: str = os.getenv("SIMFIN_API_KEY", "")
    SIMFIN_BASE_URL: str = os.getenv("SIMFIN_BASE_URL", "https://simfin.com/api/v2/")
    FINNHUB_API_KEY: str = os.getenv("FINNHUB_API_KEY", "demo")
    EODHD_API_KEY: str = os.getenv("EODHD_API_KEY", "")
    POLYGON_API_KEY: str = os.getenv("POLYGON_API_KEY", "")
    ECONOMIC_CALENDAR_URL: str = "https://www.investing.com/economic-calendar/"

    # EventRegistry references removed — use NewsAPI.ai advanced queries via NewsAPIClient

    # --- News provider order (primary to fallback). Comma-separated in env or default below. ---
    NEWS_PROVIDER_ORDER: List[str] = os.getenv("NEWS_PROVIDER_ORDER", "newsapi_ai,newsapi_org").split(",")
    # --- D-ID API Key for Realistic Avatars ---
    D_ID_API_KEY: Optional[str] = os.getenv("D_ID_API_KEY")

    # --- Governance & Simulation ---
    ETHICAL_PRINCIPLES_PATH: str = "backend/governance/ethical_principles.json"
    COMPLIANCE_RULES_PATH: str = "backend/governance/compliance_rules.json"
    POLICY_DEFINITIONS_PATH: str = "backend/governance/policies.json"

    # --- Advanced Computing & Security ---
    PQC_ENCRYPTION_ENABLED: bool = True
    NEUROMORPHIC_ENDPOINT: Optional[str] = os.getenv("NEUROMORPHIC_ENDPOINT")
    NEUROMORPHIC_API_KEY: Optional[str] = os.getenv("NEUROMORPHIC_API_KEY")
    BLOCKCHAIN_PROVIDER_URL: Optional[str] = os.getenv("BLOCKCHAIN_PROVIDER_URL")
    BLOCKCHAIN_LOGGER_PRIVATE_KEY: Optional[str] = os.getenv("BLOCKCHAIN_LOGGER_PRIVATE_KEY")
    BLOCKCHAIN_LOGGER_CONTRACT_ADDRESS: Optional[str] = os.getenv("BLOCKCHAIN_LOGGER_CONTRACT_ADDRESS")

    # --- Multi-Cloud Capabilities ---
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    AZURE_TENANT_ID: Optional[str] = os.getenv("AZURE_TENANT_ID")
    AZURE_CLIENT_ID: Optional[str] = os.getenv("AZURE_CLIENT_ID")
    AZURE_CLIENT_SECRET: Optional[str] = os.getenv("AZURE_CLIENT_SECRET")

    # --- Watchdog Configuration ---
    WATCHDOG_ESCALATION_LEVEL: str = "MEDIUM"
    ENABLE_WATCHDOG: bool = True
    WATCHDOG_DB_CHECK_INTERVAL_SECONDS: int = 300
    WATCHDOG_FIRESTORE_CHECK_INTERVAL_SECONDS: int = 300
    WATCHDOG_CRITICAL_STATE_TIMEOUT_SECONDS: int = 1800

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
    LLM_MODEL_NAME: str = os.getenv("LLM_MODEL_NAME", "gemini-1.5-flash")
    PORTFOLIO_UPDATES_TOPIC: str = os.getenv("PORTFOLIO_UPDATES_TOPIC", "priv-portfolio-updates")
    SENDGRID_API_KEY: Optional[str] = os.getenv("SENDGRID_API_KEY")
    TWILIO_ACCOUNT_SID: Optional[str] = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: Optional[str] = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER: Optional[str] = os.getenv("TWILIO_PHONE_NUMBER")

    # --- Strategy & Kill Switch ---
    TRADING_STRATEGY_MODE: TradingStrategyMode = TradingStrategyMode.NONE
    KILL_SWITCH_AI_TRADING: bool = False

    # --- Broker Router for Trading Execution ---
    TRADING_BROKER_ROUTER: str = "mock-broker-router"
    TRADING_BROKER_ROUTER_OPTIONS: List[str] = ["mock-broker-router", "alpaca-broker-router", "binance-broker-router", "deriv-broker-router", "mt5-broker-router"]

    @classmethod
    def is_production_mode(cls) -> bool:
        """
        Check if the system is running in production mode.
        Returns True if DEMO_MODE is false AND real API keys are configured.
        """
        if cls.DEMO_MODE:
            return False

        # Check if we have real API keys (not demo keys)
        demo_keys = ["demo-news-api-key-ai", "demo-news-api-key-org", "demo", "MOCK_API_KEY"]
        has_real_news_api = (
            cls.NEWS_API_KEY_AI not in demo_keys and
            cls.NEWS_API_KEY_ORG not in demo_keys
        )

        return has_real_news_api

    @classmethod
    def get_mode_description(cls) -> str:
        """Get a human-readable description of the current mode."""
        if cls.is_production_mode():
            return "PRODUCTION MODE - Live trading with real money"
        else:
            return "DEMO MODE - Paper trading with mock data"

settings = Settings()

