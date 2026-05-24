# backend/main.py
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from sqlalchemy.orm import Session # Import Session for get_db dependency
from typing import Optional

# --- Import all necessary components and settings ---
from backend.config import settings
import dependencies
from support_ai import (support_api, profile_api, history_api, analytics_api, insight_api, elliott_wave_api, audio_api, vision_api)
from trading_engine import (alert_api, connections_api, oauth_api)
from risk_analysis import risk_api
import emotion_feedback.relay_api as emotion_relay_api # Renamed for clarity

# --- Import the Classes we need to instantiate ---
from fundamental_analysis.economic_calendar.manager import EconomicCalendarManager
from multi_agent.agent_reputation_ledger import AgentReputationLedger
from multi_agent.arbitration_engine import ArbitrationEngine
from governance.regulatory_compliance import ComplianceEngine
from governance.ethical_framework import EthicalScaffoldingManager
from governance.policy_compiler import PolicyCompiler
from governance.licensing_framework import LicensingManager
from governance.tokenization.action_tokenizer import ActionTokenizer
from governance.tokenization.zk_verifier import ZKVerifier
from governance.simulation.simulation_orchestrator import SimulationOrchestrator
from treasury.wallet_vault import WalletVault
from treasury.funding_protocol import FundingProtocol
from support_ai.strategic_advisor import StrategicAdvisor
from fundamental_analysis.news_sourcing.tradingview_retriever import TradingViewRetriever
from data_sourcing.global_news_ingestor import GlobalNewsIngestor
from data_sourcing.market_data_ingestor import MarketDataIngestor
from data_sourcing.fundamental_data_ingestor import FundamentalDataIngestor
from data_sourcing.index_constituents_ingestor import IndexConstituentsIngestor
from trading_engine.broker_router import BrokerRouter 

# Import for Firebase/Firestore
try:
    from firebase_admin import credentials, initialize_app, firestore
    from firebase_admin import auth as firebase_auth  # Alias to avoid conflict with local auth modules
    FIREBASE_AVAILABLE = True
except ImportError:
    credentials = None
    initialize_app = None
    firestore = None
    firebase_auth = None
    FIREBASE_AVAILABLE = False
    logging.getLogger(__name__).warning("Firebase Admin SDK not available. Using local fallback.")

# Import for Firestore initialization in modules
from . import trade_journal # Import the module to call its init function
from treasury import wallet_vault # Import the module to call its init function
from emotion_feedback import emotion_driver # Import emotion_driver
from support_ai import history_api # Import history_api
from support_ai import profile_api # Import profile_api
from support_ai import market_insights_api # NEW: Import market_insights_api
# agent_reputation_ledger is NOT initialized with Firestore as it uses PostgreSQL

# Ensure these are imported at the top-level as they are used by background tasks
from backend.multi_agent.message_broker_interface import GoogleCloudPubSubBroker
from backend.multi_agent.priv_agent_protocol import MessageType
from datetime import datetime

# Imports for Google Cloud Logging
try:
    import google.cloud.logging
    from google.cloud.logging.handlers import CloudLoggingHandler
    from google.cloud.logging.handlers import setup_logging
    GCP_LOGGING_AVAILABLE = True
except ImportError:
    google.cloud.logging = None
    CloudLoggingHandler = None
    setup_logging = None
    GCP_LOGGING_AVAILABLE = False
    logging.getLogger(__name__).warning("Google Cloud Logging not available. Using local logging.")

# Import for database session check
from database import get_db # Import the get_db dependency

# Import for Watchdog
from utils.watchdog import Watchdog

# --- Centralized Logging Configuration ---
client = google.cloud.logging.Client()
handler = CloudLoggingHandler(client)
setup_logging(handler)

logger = logging.getLogger()
logger.setLevel(logging.INFO) # Set your desired global logging level

logging.getLogger("uvicorn.access").addHandler(handler)
logging.getLogger("uvicorn.error").addHandler(handler)

logger.info("Centralized logging configured for Google Cloud Logging.")

# Global flags for readiness checks
_firestore_initialized = False
_db_connection_healthy = False
_all_singletons_initialized = False
_watchdog_instance: Optional[Watchdog] = None # Global watchdog instance

# --- BACKGROUND TASK DEFINITIONS ---
async def run_scrapers_periodically(global_news_ingestor: GlobalNewsIngestor):
    tv_retriever = TradingViewRetriever()
    while True:
        try:
            logger.info("BACKGROUND TASK: Running all news and web scrapers...")
            await asyncio.gather(
                asyncio.to_thread(tv_retriever.fetch_ideas, "EURUSD", limit=5),
                global_news_ingestor.fetch_gdelt_articles(query="market OR economy", timespan="1h"),
            )
            logger.info("BACKGROUND TASK: All news and web scrapers finished.")
            await asyncio.sleep(30 * 60)
        except asyncio.CancelledError:
            logger.info("BACKGROUND TASK: News scraper task cancelled.")
            break
        except Exception as e:
            logger.error(f"Error in periodic news scraper task: {e}", exc_info=True)
            await asyncio.sleep(60)

async def run_market_data_polling_periodically(market_data_ingestor: MarketDataIngestor):
    symbols_to_poll = [
        "EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "SPY", "QQQ", "AAPL", "MSFT"
    ]
    while True:
        try:
            logger.info("BACKGROUND TASK: Running market data polling (REST)...")
            await market_data_ingestor.poll_market_data(symbols_to_poll)
            logger.info("BACKGROUND TASK: Market data polling finished.")
            await asyncio.sleep(15 * 60)
        except asyncio.CancelledError:
            logger.info("BACKGROUND TASK: Market data polling task cancelled.")
            break
        except Exception as e:
            logger.error(f"Error in periodic market data polling task: {e}", exc_info=True)
            await asyncio.sleep(60)

async def run_fundamental_data_ingestion_periodically(
    fundamental_data_ingestor: FundamentalDataIngestor,
    broker: GoogleCloudPubSubBroker
):
    fundamental_tickers = ["AAPL", "MSFT", "JPM", "GS"]
    
    while True:
        try:
            logger.info("BACKGROUND TASK: Running fundamental data ingestion...")
            await fundamental_data_ingestor.fetch_and_publish_fundamental_data(fundamental_tickers, broker)
            logger.info("BACKGROUND TASK: Fundamental data ingestion finished.")
            await asyncio.sleep(4 * 60 * 60)
        except asyncio.CancelledError:
            logger.info("BACKGROUND TASK: Fundamental data ingestion task cancelled.")
            break
        except Exception as e:
            logger.error(f"Error in periodic fundamental data ingestion task: {e}", exc_info=True)
            await asyncio.sleep(30 * 60)

async def run_index_constituents_ingestion_periodically(
    index_constituents_ingestor: IndexConstituentsIngestor,
    broker: GoogleCloudPubSubBroker
):
    global_indices_to_monitor = ["SPX500", "NASDAQ100", "FTSE100", "DAX", "NIKKEI225", "DJI"]
    
    while True:
        try:
            logger.info("BACKGROUND TASK: Running index constituents ingestion...")
            await index_constituents_ingestor.fetch_and_publish_index_constituents(global_indices_to_monitor, broker)
            logger.info("BACKGROUND TASK: Index constituents ingestion finished.")
            await asyncio.sleep(24 * 60 * 60)
        except asyncio.CancelledError:
            logger.info("BACKGROUND TASK: Index constituents ingestion task cancelled.")
            break
        except Exception as e:
            logger.error(f"Error in periodic index constituents ingestion task: {e}", exc_info=True)
            await asyncio.sleep(60 * 60)

async def run_broker_account_monitoring_periodically(
    broker_router: BrokerRouter,
    broker_instance: GoogleCloudPubSubBroker
):
    while True:
        try:
            logger.info("BACKGROUND TASK: Running broker account monitoring...")
            all_account_info = []
            all_open_positions = []

            for adapter in broker_router.adapters:
                try:
                    if not adapter.is_connected:
                        logger.warning(f"Broker account monitoring: Adapter '{adapter.name}' is not connected. Attempting to connect...")
                        await adapter.connect() 
                        if not adapter.is_connected:
                            logger.warning(f"Broker account monitoring: Failed to connect to '{adapter.name}'. Skipping.")
                            continue

                    account_info = await adapter.get_account_info()
                    if account_info:
                        account_info['adapter_name'] = adapter.name
                        all_account_info.append(account_info)
                        logger.debug(f"Fetched account info from {adapter.name}.")

                    open_positions = await adapter.get_open_positions()
                    if open_positions:
                        for pos in open_positions:
                            pos['adapter_name'] = adapter.name
                        all_open_positions.extend(open_positions)
                        logger.debug(f"Fetched open positions from {adapter.name}.")

                except Exception as e:
                    logger.error(f"Error fetching account/position info from broker adapter {adapter.name}: {e}", exc_info=True)
            
            if all_account_info or all_open_positions:
                portfolio_update_payload = {
                    "timestamp": datetime.now().isoformat(),
                    "account_summaries": all_account_info,
                    "open_positions": all_open_positions
                }
                agent_message = {
                    "sender_id": "BrokerAccountMonitor",
                    "message_type": MessageType.STATUS_UPDATE,
                    "payload": portfolio_update_payload
                }
                await broker_instance.publish_message("portfolio_updates", agent_message)
                logger.info(f"BACKGROUND TASK: Published aggregated portfolio updates ({len(all_account_info)} accounts, {len(all_open_positions)} positions).")
            else:
                logger.warning("BACKGROUND TASK: No account info or open positions fetched from any broker adapter.")
            
            await asyncio.sleep(5 * 60)
        except asyncio.CancelledError:
            logger.info("BACKGROUND TASK: Broker account monitoring task cancelled.")
            break
        except Exception as e:
            logger.error(f"Error in periodic broker account monitoring task: {e}", exc_info=True)
            await asyncio.sleep(60 * 60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 80)
    logger.info("🚀 PRIV Core Application Startup Sequence Initiated")
    logger.info("=" * 80)
    
    # Initialize PRIV personality first
    from priv_core.personality_integration import initialize_priv_personality, get_priv_personality, log_with_identity
    
    personality_loaded = initialize_priv_personality()
    
    if personality_loaded:
        priv_personality = get_priv_personality()
        logger.info("✅ PRIV is now aware of its identity and purpose")
        logger.info(f"   Identity: {priv_personality.get_identity_context()}")
        logger.info(f"   Creator: {priv_personality.get_creator_signature()}")
        log_with_identity("System Startup", "PRIV Core initializing with full personality context")
    else:
        logger.warning("⚠️  PRIV starting without personality context")
    
    logger.info("=" * 80)
    
    global _firestore_initialized, _db_connection_healthy, _all_singletons_initialized, _watchdog_instance

    # --- Firebase/Firestore Initialization ---
    try:
        # Initialize Firebase Admin SDK
        firebase_app = initialize_app(options={'projectId': settings.GCP_PROJECT_ID})
        db = firestore.client()
        
        class DummyAuth:
            @property
            def currentUser(self):
                # In a real app, this would be populated from an authenticated user session
                # For now, return a fixed ID or fetch from context
                return firebase_auth.get_user("some-default-user-id")
        
        # Initialize Firestore in relevant modules
        trade_journal.initialize_firestore_trade_journal(db, DummyAuth(), settings.GCP_PROJECT_ID)
        wallet_vault.initialize_firestore_wallet_vault(db, DummyAuth(), settings.GCP_PROJECT_ID)
        relay_api.initialize_firestore_relay_api(db, settings.GCP_PROJECT_ID)
        emotion_driver.initialize_firestore_emotion_driver(db, settings.GCP_PROJECT_ID)
        history_api.initialize_firestore_history_api(db, settings.GCP_PROJECT_ID)
        profile_api.initialize_firestore_profile_api(db, settings.GCP_PROJECT_ID)
        market_insights_api.initialize_firestore_market_insights_api(db, settings.GCP_PROJECT_ID) # NEW: Initialize market_insights_api
        
        _firestore_initialized = True
        logger.info("Firebase/Firestore initialized successfully.")
    except Exception as e:
        _firestore_initialized = False
        logger.error(f"Failed to initialize Firebase/Firestore: {e}", exc_info=True)
        # Depending on criticality, you might want to raise the exception or proceed with warnings.
        # For now, we'll log and continue, but Firestore-dependent features will fail.

    # Initialize all singleton instances
    dependencies.economic_calendar_manager_instance = EconomicCalendarManager(calendar_url=settings.ECONOMIC_CALENDAR_URL)
    dependencies.agent_reputation_ledger_instance = AgentReputationLedger() 
    dependencies.ethical_scaffolding_manager_instance = EthicalScaffoldingManager(principles_definitions_path=settings.ETHICAL_PRINCIPLES_PATH)
    dependencies.wallet_vault_instance = WalletVault()
    dependencies.compliance_engine_instance = ComplianceEngine(rules_definitions_path=settings.COMPLIANCE_RULES_PATH)
    dependencies.policy_compiler_instance = PolicyCompiler(policy_definitions_path=settings.POLICY_DEFINITIONS_PATH)
    dependencies.licensing_manager_instance = LicensingManager()
    dependencies.action_tokenizer_instance = ActionTokenizer()
    dependencies.zk_verifier_instance = ZKVerifier()
    dependencies.arbitration_engine_instance = ArbitrationEngine(reputation_ledger=dependencies.agent_reputation_ledger_instance)
    dependencies.funding_protocol_instance = FundingProtocol(wallet_vault=dependencies.wallet_vault_instance, arbitration_engine_ref=dependencies.arbitration_engine_instance)
    dependencies.simulation_orchestrator_instance = SimulationOrchestrator(
        ethical_manager=dependencies.ethical_scaffolding_manager_instance,
        reputation_ledger=dependencies.agent_reputation_ledger_instance
    )
    dependencies.strategic_advisor_instance = StrategicAdvisor()
    dependencies.global_news_ingestor_instance = GlobalNewsIngestor()
    dependencies.market_data_ingestor_instance = MarketDataIngestor()
    dependencies.fundamental_data_ingestor_instance = FundamentalDataIngestor()
    dependencies.index_constituents_ingestor_instance = IndexConstituentsIngestor()

    _all_singletons_initialized = True
    logger.info("All singleton instances created successfully.")
    
    # Check database connection health
    try:
        db_session = next(get_db()) # Attempt to get a session
        db_session.connection() # Try to get a connection from the pool
        _db_connection_healthy = True
        logger.info("Database connection pool is healthy.")
    except Exception as e:
        _db_connection_healthy = False
        logger.error(f"Failed to establish database connection pool health: {e}", exc_info=True)

    # Temporarily commented out for diagnosis: This might be blocking startup
    # await dependencies.broker_router.refresh_all_adapter_health()
    
    # --- Background data ingestion tasks ---
    # News and TradingView scraping
    scraper_task = asyncio.create_task(run_scrapers_periodically(dependencies.global_news_ingestor_instance))
    logger.info("Background news scraper task started.")

    # Market Data ingestion
    market_data_broker = GoogleCloudPubSubBroker(broker_config={"project_id": settings.GCP_PROJECT_ID})
    await market_data_broker.connect()
    market_data_task = asyncio.create_task(
        run_market_data_ingestion_periodically(
            dependencies.market_data_ingestor_instance,
            market_data_broker
        )
    )
    logger.info("BACKGROUND TASK: Market data ingestion task started.")

    # Fundamental Data ingestion
    fundamental_data_task = asyncio.create_task(
        run_fundamental_data_ingestion_periodically(
            dependencies.fundamental_data_ingestor_instance,
            market_data_broker
        )
    )
    logger.info("BACKGROUND TASK: Fundamental data ingestion task started.")

    # Index Constituents ingestion
    index_constituents_task = asyncio.create_task(
        run_index_constituents_ingestion_periodically(
            dependencies.index_constituents_ingestor_instance,
            market_data_broker
        )
    )
    logger.info("BACKGROUND TASK: Index constituents ingestion task started.")

    # Broker Account Monitoring task
    broker_account_monitoring_task = asyncio.create_task(
        run_broker_account_monitoring_periodically(
            dependencies.broker_router,
            market_data_broker
        )
    )
    logger.info("BACKGROUND TASK: Broker account monitoring task started.")

    # Watchdog Initialization and Monitoring
    if settings.ENABLE_WATCHDOG:
        _watchdog_instance = Watchdog(db_instance=db) # Pass Firestore db instance
        watchdog_task = asyncio.create_task(_watchdog_instance.start_monitoring())
        logger.info("BACKGROUND TASK: Watchdog monitoring task started.")
    else:
        logger.info("Watchdog is disabled in settings.")


    logger.info("--- Application Startup Sequence Complete. Priv is ready! ---")
    
    yield
    
    logger.info("Application shutdown initiated...")
    scraper_task.cancel()
    market_data_task.cancel()
    fundamental_data_task.cancel()
    index_constituents_task.cancel()
    broker_account_monitoring_task.cancel()
    
    # Stop watchdog on shutdown
    if _watchdog_instance:
        _watchdog_instance.stop_monitoring()

    await market_data_broker.disconnect()

    # Disconnect all adapters managed by BrokerRouter
    for adapter in dependencies.broker_router.adapters:
        if adapter.is_connected:
            await adapter.disconnect()
    logger.info("All services disconnected. Application shutdown complete.")


app = FastAPI(
    title=settings.APP_NAME,
    description="API for the Sans Mercantile AI Trading and Analysis System.",
    version=settings.APP_VERSION,
    lifespan=lifespan
)

app.add_middleware(CORSMiddleware, allow_origins=settings.ALLOWED_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# API Routers
app.include_router(support_api.router, prefix="/api/v1/support", tags=["Support AI"])
app.include_router(profile_api.router, prefix="/api/v1/profile", tags=["Support AI & User Profile"])
app.include_router(history_api.router, prefix="/api/v1/history", tags=["Support AI & User Profile"])
app.include_router(analytics_api.router, prefix="/api/v1/analytics", tags=["Support AI & User Profile"])
app.include_router(insight_api.router, prefix="/api/v1/insights", tags=["Support AI & User Profile"])
app.include_router(elliott_wave_api.router, prefix="/api/v1/elliottwave", tags=["Technical Analysis"])
app.include_router(audio_api.router, prefix="/api/v1/audio", tags=["Advanced IO"])
app.include_router(vision_api.router, prefix="/api/v1/vision", tags=["Advanced IO"])
app.include_router(alert_api.router, prefix="/api/v1/trading", tags=["Trading Engine"])
app.include_router(connections_api.router, prefix="/api/v1/trading", tags=["Trading Engine"])
app.include_router(oauth_api.router, prefix="/api/v1/auth", tags=["Trading Engine"])
app.include_router(risk_api.router, prefix="/api/v1/risk", tags=["Risk Analysis"])
app.include_router(emotion_relay_api.router, prefix="/api/v1/emotion", tags=["Emotion Feedback"])
app.include_router(market_insights_api.router, prefix="/api/v1/market-insights", tags=["Market Insights"]) # NEW: Include Market Insights Router

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": f"Welcome to {settings.APP_NAME} v{settings.APP_VERSION}!"}

# Health Check Endpoints
@app.get("/healthz", tags=["Health"])
async def healthz():
    """Liveness probe: indicates if the application is alive."""
    return {"status": "ok"}

@app.get("/readyz", tags=["Health"])
async def readyz():
    """
    Readiness probe: indicates if the application is ready to serve traffic.
    Checks critical dependencies like Firestore and PostgreSQL.
    """
    if not _firestore_initialized:
        logger.warning("Readiness check failed: Firestore not initialized.")
        raise HTTPException(status_code=503, detail="Firestore not initialized")
    
    if not _db_connection_healthy:
        logger.warning("Readiness check failed: Database connection not healthy.")
        raise HTTPException(status_code=503, detail="Database connection not healthy")

    if not _all_singletons_initialized:
        logger.warning("Readiness check failed: Singletons not initialized.")
        raise HTTPException(status_code=503, detail="Singletons not initialized")

    if settings.ENABLE_WATCHDOG and _watchdog_instance and _watchdog_instance.is_critical_state_active():
        logger.warning("Readiness check failed: Watchdog reports critical state.")
        raise HTTPException(status_code=503, detail="Watchdog reports critical state")

    return {"status": "ready"}


if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True, reload_dirs=["backend"])
