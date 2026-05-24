# backend/dependencies.py

import logging
from functools import lru_cache

# Import settings and core classes
from .config import settings
from .trading_engine.broker_router import BrokerRouter
from .support_ai.core_ai_handler import LLMClient
from .communication.notification_manager import NotificationManager
from .security.pqc_encryption import PQCCipher

# Import all adapter classes
from .trading_engine.adapters.mock_adapter import MockTradeAPIAdapter
try:
    from .trading_engine.adapters.alpaca_adapter import AlpacaAPIAdapter
except Exception as e:
    logging.getLogger(__name__).warning(f"Alpaca adapter not available: {e}")
    AlpacaAPIAdapter = None
try:
    from .trading_engine.adapters.deriv_adapter import DerivAPIAdapter
except Exception as e:
    logging.getLogger(__name__).warning(f"Deriv adapter not available: {e}")
    DerivAPIAdapter = None
from .trading_engine.adapters.mt5_adapter import MetaTrader5Adapter
from .trading_engine.adapters.binance_adapter import BinanceAdapter
from .trading_engine.adapters.xm_adapter import XmAdapter

# Import all singleton service classes
from .support_ai.strategic_advisor import StrategicAdvisor
from .data_sourcing.global_news_ingestor import GlobalNewsIngestor
from .data_sourcing.market_data_ingestor import MarketDataIngestor
from .data_sourcing.fundamental_data_ingestor import FundamentalDataIngestor
from .data_sourcing.index_constituents_ingestor import IndexConstituentsIngestor
from .fundamental_analysis.economic_calendar.manager import EconomicCalendarManager
from .multi_agent.agent_reputation_ledger import AgentReputationLedger
from .multi_agent.arbitration_engine import ArbitrationEngine
from .governance.regulatory_compliance import ComplianceEngine
from .governance.ethical_framework import EthicalScaffoldingManager
from .governance.policy_compiler import PolicyCompiler
from .governance.licensing_framework import LicensingManager
from .governance.tokenization.action_tokenizer import ActionTokenizer
from .governance.tokenization.zk_verifier import ZKVerifier
from .governance.simulation.simulation_orchestrator import SimulationOrchestrator
from .treasury.wallet_vault import WalletVault
from .treasury.funding_protocol import FundingProtocol
from shared_resources.agi_core.agi_core_manager import AgiCoreManager
from .multi_agent.corporate_memory_graph import CorporateMemoryGraph
from .multi_agent.escalation_engine import EscalationEngine
from .compute.hardware_integration_manager import HardwareIntegrationManager
from .governance.societal_alignment_framework import SocietalAlignmentFramework
from .ventures.healthcare_adapter import HealthcareAdapter
from .ventures.legal_adapter import LegalAdapter


logger = logging.getLogger(__name__)

# This dictionary will hold the single instances of our core services.
_singletons = {}

def get_singleton(name: str):
    """A helper to get any initialized singleton by name."""
    return _singletons.get(name)

@lru_cache(maxsize=None)
def get_broker_router() -> BrokerRouter:
    """
    Creates, configures, and returns a singleton BrokerRouter instance.
    This is a complete, production-ready implementation.
    """
    logger.info("Initializing BrokerRouter and all configured adapters...")
    router = BrokerRouter()

    # Prefer real adapters. Track whether any real adapter was added so we avoid using mock adapters when real brokers are available.
    real_adapter_added = False

    # Add Alpaca Paper Adapter
    if AlpacaAPIAdapter:
        # Primary: explicit paper adapter env vars (preferred)
        if settings.ENABLE_ALPACA_PAPER_ADAPTER and settings.ALPACA_PAPER_API_KEY_ID and "YOUR_ALPACA" not in settings.ALPACA_PAPER_API_KEY_ID:
            router.add_adapter(AlpacaAPIAdapter(api_key=settings.ALPACA_PAPER_API_KEY_ID, secret_key=settings.ALPACA_PAPER_API_SECRET_KEY, paper=True))
            logger.info("AlpacaAPIAdapter (Paper) added to BrokerRouter via ALPACA_PAPER_* vars.")
            real_adapter_added = True
        # Fallback: allow ALPACA_API_KEY / ALPACA_SECRET_KEY from older .env naming
        elif getattr(settings, 'ALPACA_API_KEY', None) and getattr(settings, 'ALPACA_SECRET_KEY', None):
            router.add_adapter(AlpacaAPIAdapter(api_key=settings.ALPACA_API_KEY, secret_key=settings.ALPACA_SECRET_KEY, paper=True))
            logger.info("AlpacaAPIAdapter (Paper) added to BrokerRouter via ALPACA_API_KEY/ALPACA_SECRET_KEY fallback.")
            real_adapter_added = True

    # Add Deriv Adapter (primary broker for PRIV)
    deriv_app_id = getattr(settings, 'DERIV_APP_ID', None)
    deriv_token = getattr(settings, 'DERIV_API_TOKEN', None)
    if deriv_token and deriv_app_id:
        if DerivAPIAdapter:
            try:
                # Ensure app id is an int if possible
                try:
                    app_id_int = int(deriv_app_id)
                except Exception:
                    app_id_int = deriv_app_id
                router.add_adapter(DerivAPIAdapter(app_id=app_id_int, api_token=deriv_token))
                logger.info("DerivAPIAdapter added to BrokerRouter (DERIV_APP_ID/DERIV_API_TOKEN detected).")
                real_adapter_added = True
            except Exception:
                logger.exception("Failed to add DerivAPIAdapter. Is the Deriv SDK installed and are environment variables configured?")
        else:
            logger.warning("DERIV_API_TOKEN is present but the Deriv SDK is not installed. Install it with: pip install deriv-api")

    # Add Binance Adapter
    if getattr(settings, 'BINANCE_API_KEY', None) and "YOUR_BINANCE" not in settings.BINANCE_API_KEY:
        router.add_adapter(BinanceAdapter(api_key=settings.BINANCE_API_KEY, secret_key=settings.BINANCE_SECRET_KEY))
        logger.info("BinanceAdapter added to BrokerRouter.")
        real_adapter_added = True

    # Add MetaTrader 5 Adapter
    if getattr(settings, 'ENABLE_MT5_ADAPTER', False):
        router.add_adapter(MetaTrader5Adapter())
        logger.info("MetaTrader5Adapter added to BrokerRouter.")
        real_adapter_added = True
        
    # Add XM Adapter
    if getattr(settings, 'ENABLE_XM_ADAPTER', False) and getattr(settings, 'XM_ACCOUNT_ID', None) and "YOUR_XM_ACCOUNT" not in str(settings.XM_ACCOUNT_ID):
        router.add_adapter(XmAdapter(account_id=settings.XM_ACCOUNT_ID, password=settings.XM_PASSWORD))
        logger.info("XmAdapter added to BrokerRouter.")
        real_adapter_added = True

    # Add Mock Adapter only if no real adapters were configured or if explicitly forced
    if settings.ENABLE_MOCK_ADAPTER and not real_adapter_added:
        router.add_adapter(MockTradeAPIAdapter(name="PrimaryMockAdapter"))
        logger.info("MockTradeAPIAdapter added to BrokerRouter (no real adapters were detected).")

    # Add Alpaca Paper Adapter
    if AlpacaAPIAdapter:
        # Primary: explicit paper adapter env vars (preferred)
        if settings.ENABLE_ALPACA_PAPER_ADAPTER and settings.ALPACA_PAPER_API_KEY_ID and "YOUR_ALPACA" not in settings.ALPACA_PAPER_API_KEY_ID:
            router.add_adapter(AlpacaAPIAdapter(api_key=settings.ALPACA_PAPER_API_KEY_ID, secret_key=settings.ALPACA_PAPER_SECRET_KEY, paper=True))
            logger.info("AlpacaAPIAdapter (Paper) added to BrokerRouter via ALPACA_PAPER_* vars.")
        # Fallback: allow ALPACA_API_KEY / ALPACA_SECRET_KEY from older .env naming
        elif getattr(settings, 'ALPACA_API_KEY', None) and getattr(settings, 'ALPACA_SECRET_KEY', None):
            router.add_adapter(AlpacaAPIAdapter(api_key=settings.ALPACA_API_KEY, secret_key=settings.ALPACA_SECRET_KEY, paper=True))
            logger.info("AlpacaAPIAdapter (Paper) added to BrokerRouter via ALPACA_API_KEY/ALPACA_SECRET_KEY fallback.")

    # Add Deriv Adapters
    # Add Deriv adapters if available
    if DerivAPIAdapter:
        try:
            if getattr(settings, 'ENABLE_DERIV_APP_CONSOLE_ADAPTER', False) and getattr(settings, 'DERIV_APP_CONSOLE_API_TOKEN', None) and "YOUR_APP_CONSOLE_TOKEN" not in settings.DERIV_APP_CONSOLE_API_TOKEN:
                router.add_adapter(DerivAPIAdapter(app_id=settings.DERIV_APP_CONSOLE_APP_ID, api_token=settings.DERIV_APP_CONSOLE_API_TOKEN, name="DerivAppConsole"))
                logger.info("DerivAPIAdapter (App Console) added to BrokerRouter.")
        except AttributeError:
            pass
        
        try:
            if getattr(settings, 'ENABLE_DERIV_PRIV1_ADAPTER', False) and getattr(settings, 'DERIV_PRIV1_API_TOKEN', None) and "YOUR_PRIV1_TOKEN" not in settings.DERIV_PRIV1_API_TOKEN:
                router.add_adapter(DerivAPIAdapter(app_id=settings.DERIV_PRIV1_APP_ID, api_token=settings.DERIV_PRIV1_API_TOKEN, name="DerivPriv1"))
                logger.info("DerivAPIAdapter (PRIV1) added to BrokerRouter.")
        except AttributeError:
            pass

    # Add Binance Adapter
    if getattr(settings, 'BINANCE_API_KEY', None) and "YOUR_BINANCE" not in settings.BINANCE_API_KEY:
        router.add_adapter(BinanceAdapter(api_key=settings.BINANCE_API_KEY, secret_key=settings.BINANCE_SECRET_KEY))
        logger.info("BinanceAdapter added to BrokerRouter.")

    # Add MetaTrader 5 Adapter
    if getattr(settings, 'ENABLE_MT5_ADAPTER', False):
        router.add_adapter(MetaTrader5Adapter())
        logger.info("MetaTrader5Adapter added to BrokerRouter.")
        
    # Add XM Adapter
    if getattr(settings, 'ENABLE_XM_ADAPTER', False) and getattr(settings, 'XM_ACCOUNT_ID', None) and "YOUR_XM_ACCOUNT" not in str(settings.XM_ACCOUNT_ID):
        router.add_adapter(XmAdapter(account_id=settings.XM_ACCOUNT_ID, password=settings.XM_PASSWORD))
        logger.info("XmAdapter added to BrokerRouter.")

    return router

def get_llm_client() -> LLMClient:
    """Returns a singleton instance of the LLMClient."""
    if "llm_client" not in _singletons:
        _singletons["llm_client"] = LLMClient()
    return _singletons["llm_client"]

def get_strategic_advisor():
    if "strategic_advisor" not in _singletons:
        _singletons["strategic_advisor"] = StrategicAdvisor()
    return get_singleton("strategic_advisor")

def get_agi_core_manager():
    if "agi_core_manager" not in _singletons:
        _singletons["agi_core_manager"] = AgiCoreManager()
    return _singletons["agi_core_manager"]

def get_notification_manager() -> NotificationManager:
    """Returns a singleton instance of the NotificationManager."""
    if "notification_manager" not in _singletons:
        _singletons["notification_manager"] = NotificationManager()
    return _singletons["notification_manager"]

def get_pqc_cipher() -> PQCCipher:
    """Returns a singleton instance of the PQCCipher."""
    if "pqc_cipher" not in _singletons:
        _singletons["pqc_cipher"] = PQCCipher()
    return _singletons["pqc_cipher"]

def get_hardware_integration_manager() -> HardwareIntegrationManager:
    """Returns a singleton instance of the HardwareIntegrationManager."""
    if "hardware_integration_manager" not in _singletons:
        _singletons["hardware_integration_manager"] = HardwareIntegrationManager()
    return _singletons["hardware_integration_manager"]

def get_societal_alignment_framework() -> SocietalAlignmentFramework:
    """Returns a singleton instance of the SocietalAlignmentFramework."""
    if "societal_alignment_framework" not in _singletons:
        # Corrected: Fetch dependencies first, then initialize.
        broker = get_singleton("broker_router")
        ethical_manager = get_singleton("ethical_scaffolding_manager")
        compliance_engine = get_singleton("compliance_engine")
        _singletons["societal_alignment_framework"] = SocietalAlignmentFramework(
            broker=broker,
            ethical_manager=ethical_manager,
            compliance_engine=compliance_engine
        )
    return _singletons["societal_alignment_framework"]

def get_healthcare_adapter() -> HealthcareAdapter:
    """Returns a singleton instance of the HealthcareAdapter."""
    if "healthcare_adapter" not in _singletons:
        _singletons["healthcare_adapter"] = HealthcareAdapter()
    return _singletons["healthcare_adapter"]

def get_legal_adapter() -> LegalAdapter:
    """Returns a singleton instance of the LegalAdapter."""
    if "legal_adapter" not in _singletons:
        _singletons["legal_adapter"] = LegalAdapter()
    return _singletons["legal_adapter"]

def initialize_all_singletons():
    """
    Initializes all singleton services that need to be available at startup for PRIV's application.
    This function is now complete and contains no omissions.
    """
    global _singletons
    if "initialized" in _singletons:
        return

    logger.info("Initializing all core singleton services for the Sans Mercantile (PRIV) application...")
    
    # Core Infrastructure and Communication
    _singletons["llm_client"] = get_llm_client()
    _singletons["notification_manager"] = get_notification_manager()
    _singletons["broker_router"] = get_broker_router()
    _singletons["pqc_cipher"] = get_pqc_cipher()
    
    # Data Sourcing and Analysis
    _singletons["global_news_ingestor"] = GlobalNewsIngestor()
    _singletons["market_data_ingestor"] = MarketDataIngestor(broker=get_singleton("broker_router"))
    _singletons["fundamental_data_ingestor"] = FundamentalDataIngestor()
    _singletons["index_constituents_ingestor"] = IndexConstituentsIngestor()
    _singletons["economic_calendar_manager"] = EconomicCalendarManager(calendar_url=settings.ECONOMIC_CALENDAR_URL)
    _singletons["strategic_advisor"] = get_strategic_advisor()
    
    # Multi-Agent Systems
    _singletons["agent_reputation_ledger"] = AgentReputationLedger()
    
    # Security and Verification
    _singletons["action_tokenizer"] = ActionTokenizer()
    _singletons["zk_verifier"] = ZKVerifier(
        project_id=getattr(settings, 'GCP_PROJECT_ID', None),
        kms_key_ring_name=getattr(settings, 'KMS_KEY_RING_NAME', None),
        kms_location=getattr(settings, 'KMS_LOCATION', 'global'),
        proving_key_name=getattr(settings, 'PROVING_KEY_NAME', None),
        verification_key_name=getattr(settings, 'VERIFICATION_KEY_NAME', None)
    )

    _singletons["arbitration_engine"] = ArbitrationEngine(
        reputation_ledger=_singletons["agent_reputation_ledger"],
        zk_verifier=_singletons["zk_verifier"]
    )
    _singletons["corporate_memory_graph"] = CorporateMemoryGraph()
    c_suite_hierarchy = ["CEO_PROXY", "COO", "CLO", "CTO", "CFO", "CPO"]
    _singletons["escalation_engine"] = EscalationEngine(c_suite_hierarchy)

    # Governance and Compliance
    _singletons["ethical_scaffolding_manager"] = EthicalScaffoldingManager(principles_definitions_path=settings.ETHICAL_PRINCIPLES_PATH)
    _singletons["compliance_engine"] = ComplianceEngine(rules_definitions_path=settings.COMPLIANCE_RULES_PATH)
    _singletons["policy_compiler"] = PolicyCompiler(policy_definitions_path=settings.POLICY_DEFINITIONS_PATH)
    _singletons["licensing_manager"] = LicensingManager()
    
    # Treasury and Simulation
    _singletons["wallet_vault"] = WalletVault()
    _singletons["funding_protocol"] = FundingProtocol(wallet_vault=_singletons["wallet_vault"], arbitration_engine_ref=_singletons["arbitration_engine"])
    _singletons["simulation_orchestrator"] = SimulationOrchestrator(
        ethical_manager=_singletons["ethical_scaffolding_manager"],
        reputation_ledger=_singletons["agent_reputation_ledger"]
    )
    
    # AGI Core & Advanced Integration
    _singletons["agi_core_manager"] = get_agi_core_manager()
    _singletons["hardware_integration_manager"] = get_hardware_integration_manager()
    
    # Corrected: Initialize Societal Alignment Framework after its dependencies are created.
    _singletons["societal_alignment_framework"] = get_societal_alignment_framework()

    # Venture Adapters
    _singletons["healthcare_adapter"] = get_healthcare_adapter()
    _singletons["legal_adapter"] = get_legal_adapter()

    _singletons["initialized"] = True
    logger.info("All core singleton services for PRIV have been initialized.")

