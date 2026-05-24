# Main entry point for the Sans Mercantile Application (PRIV).
# backend/main.py

import logging
import asyncio
import os
import sys
from contextlib import asynccontextmanager
from typing import Optional, Any
import json
from datetime import datetime
import httpx

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from sqlalchemy.orm import Session
from sqlalchemy import text # Import the 'text' function

# --- Path Correction ---
# This ensures that modules from sibling systems/ directories (e.g., mpeti) can be imported.
# Add the parent directory of 'priv' to the Python path.
current_dir = os.path.dirname(os.path.abspath(__file__))
priv_dir = os.path.dirname(current_dir)  # Get the 'priv' directory
constellation_dir = os.path.dirname(priv_dir)  # Get the parent directory of 'priv'
if priv_dir not in sys.path:
    sys.path.insert(0, priv_dir)
# Append repo root so shared_resources imports work without shadowing site-packages (e.g. openai).
if constellation_dir not in sys.path:
    sys.path.append(constellation_dir)

# Import settings - using absolute imports with priv prefix since we're running as a script
from backend.config import settings

# Import new API routers
from backend.api import portfolio_api, market_api, agents_api, system_api, chat_api, governance_api
from backend.api import news_api, analytics_api as new_analytics_api, history_api as new_history_api, connections_api as new_connections_api
from backend.api import agent_orchestration_api
try:
    from backend.api import broker_endpoints
except Exception as e:
    logging.warning(f"broker_endpoints not available: {e}")
    broker_endpoints = None
# Try to import demo-friendly profile and tax routers (fallback if support_ai profile_api is not available)
try:
    from backend.api import profile_api as demo_profile_api, tax_api as demo_tax_api
except Exception as e:
    demo_profile_api = None
    demo_tax_api = None

# --- Logging Setup ---
logger = logging.getLogger(__name__)

# Configure logging based on the mode.
if settings.DEMO_MODE:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.info("DEMO_MODE: True. Using basic logging.")
else:
    try:
        from google.cloud import logging as cloud_logging
        from google.cloud.logging.handlers import CloudLoggingHandler
        client = cloud_logging.Client()
        handler = CloudLoggingHandler(client)
        # Set the root logger to INFO level and add the cloud handler.
        logging.getLogger().setLevel(logging.INFO)
        logging.getLogger().addHandler(handler)
        # Capture uvicorn's access and error logs.
        logging.getLogger("uvicorn.access").addHandler(handler)
        logging.getLogger("uvicorn.error").addHandler(handler)
        logger.info("Centralized logging configured for Google Cloud Logging.")
    except Exception as e:
        # Fallback to basic logging if Google Cloud Logging fails.
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        logger.warning(f"Google Cloud Logging setup failed: {e}. Falling back to basic logging.")

# --- Import other components AFTER settings and logging are configured ---
from backend import dependencies

# Import optional modules with fallback to None if not available
try:
    from backend.support_ai import (support_api, profile_api, history_api, analytics_api, insight_api, elliott_wave_api, audio_api, vision_api, market_insights_api, video_streaming_api)
except ImportError as e:
    logger.warning(f"support_ai module not available: {e}")
    support_api = profile_api = history_api = analytics_api = insight_api = elliott_wave_api = audio_api = vision_api = market_insights_api = video_streaming_api = None

try:
    from backend.trading_engine import (alert_api, connections_api, oauth_api)
except ImportError as e:
    logger.warning(f"trading_engine module not available: {e}")
    alert_api = connections_api = oauth_api = None

try:
    from backend.risk_analysis import risk_api
except ImportError as e:
    logger.warning(f"risk_analysis module not available: {e}")
    risk_api = None

try:
    from backend.emotion_feedback import relay_api as emotion_relay_api
except ImportError as e:
    logger.warning(f"emotion_feedback module not available: {e}")
    emotion_relay_api = None

try:
    from shared_resources.agi_core import agi_api
except ImportError as e:
    logger.warning(f"agi_core module not available: {e}")
    agi_api = None

try:
    from backend.multi_agent import departmental_api
except ImportError as e:
    logger.warning(f"multi_agent departmental_api not available: {e}")
    departmental_api = None

try:
    from backend.payment import api as payment_api
except ImportError as e:
    logger.warning(f"payment api not available: {e}")
    payment_api = None

try:
    from backend.avatar.main import app as avatar_sub_app
except ImportError as e:
    logger.warning(f"avatar api sub-app not available: {e}")
    avatar_sub_app = None

from backend.database import get_db
from backend.multi_agent.central_orchestrator import CentralOrchestrator
from backend.governance.tokenization.zk_verifier import ZKVerifier
from backend.data_sourcing.global_news_ingestor import GlobalNewsIngestor
from backend.data_sourcing.market_data_ingestor import MarketDataIngestor
from backend.fundamental_analysis.news_sourcing.tradingview_retriever import TradingViewRetriever
from backend.trading_engine.broker_router import BrokerRouter
from backend.multi_agent.message_broker_interface import GoogleCloudPubSubBroker, MessageBrokerInterface
from backend.multi_agent.priv_agent_protocol import MessageType

# --- Global State ---
_firestore_initialized = False
_db_connection_healthy = False
_all_singletons_initialized = False
priv_central_orchestrator_instance: Optional[CentralOrchestrator] = None

# Define URLs for other distinct applications (external services to PRIV)
MPETI_APP_URL = os.environ.get("MPETI_APP_URL", "http://mpeti-core-service:8000")
MEZZO_APP_URL = os.environ.get("MEZZO_APP_URL", "http://mezzo-anima-service:8003")
INPU_APP_URL = os.environ.get("INPU_APP_URL", "http://anubis-service:8004")

# --- Background Task Definitions ---
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
    symbols_to_poll = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "SPY", "QQQ", "AAPL", "MSFT"]
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

async def run_broker_account_monitoring_periodically(broker_router: BrokerRouter, pubsub_broker: MessageBrokerInterface):
    while True:
        try:
            logger.info("BACKGROUND TASK: Running broker account monitoring...")
            all_account_info, all_open_positions = [], []
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
                    open_positions = await adapter.get_open_positions()
                    if open_positions:
                        for pos in open_positions:
                            pos['adapter_name'] = adapter.name
                        all_open_positions.extend(open_positions)
                except Exception as e:
                    logger.error(f"Error fetching data from broker adapter {adapter.name}: {e}", exc_info=True)
            if all_account_info or all_open_positions:
                payload = {"timestamp": datetime.now().isoformat(), "account_summaries": all_account_info, "open_positions": all_open_positions}
                message = {"sender_id": "BrokerAccountMonitor", "message_type": MessageType.STATUS_UPDATE.value, "payload": payload}
                await pubsub_broker.publish_message("portfolio_updates", message) # Corrected topic name
                logger.info(f"BACKGROUND TASK: Published portfolio updates ({len(all_account_info)} accounts, {len(all_open_positions)} positions).")
            await asyncio.sleep(5 * 60)
        except asyncio.CancelledError:
            logger.info("BACKGROUND TASK: Broker account monitoring task cancelled.")
            break
        except Exception as e:
            logger.error(f"Error in broker account monitoring task: {e}", exc_info=True)
            await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _firestore_initialized, _db_connection_healthy, _all_singletons_initialized, priv_central_orchestrator_instance
    logger.info("--- Sans Mercantile Application (PRIV) Startup Sequence Initiated ---")

    db_instance: Optional[Any] = None
    if not settings.DEMO_MODE:
        try:
            from firebase_admin import get_app, initialize_app, firestore
            from .journal import trade_journal
            from .treasury import wallet_vault
            from .emotion_feedback import emotion_driver
            
            if not settings.GCP_PROJECT_ID: raise ValueError("GCP_PROJECT_ID not set.")
            try:
                get_app('privApp')
            except ValueError:
                initialize_app(options={'projectId': settings.GCP_PROJECT_ID}, name='privApp')
            
            db_instance = firestore.client(app=get_app('privApp'))
            dependencies._singletons["firestore_db"] = db_instance
            trade_journal.initialize_firestore(db_instance)
            wallet_vault.initialize_firestore(db_instance)
            emotion_relay_api.initialize_firestore(db_instance)
            emotion_driver.initialize_firestore(db_instance)
            history_api.initialize_firestore(db_instance)
            profile_api.initialize_firestore(db_instance)
            market_insights_api.initialize_firestore(db_instance)
            _firestore_initialized = True
            logger.info("Firebase & Firestore clients initialized.")
        except Exception as e:
            _firestore_initialized = False
            logger.critical(f"FATAL: Firebase/Firestore initialization failed: {e}", exc_info=True)
        
        try:
            import vertexai
            vertexai.init(project=settings.GCP_PROJECT_ID)
            logger.info("Vertex AI initialized.")
        except Exception as e:
            logger.warning(f"Vertex AI initialization failed: {e}", exc_info=True)
    else:
        _firestore_initialized = True # In Demo mode, we can consider it "initialized" for readiness checks
        logger.info("Skipping Firebase and Vertex AI initialization in DEMO_MODE.")

    dependencies.initialize_all_singletons()
    _all_singletons_initialized = True
    logger.info("All singleton services initialized.")

    db_session = None
    try:
        db_session = next(get_db())
        # FIX: Use the text() construct for executing literal SQL
        db_session.execute(text("SELECT 1"))
        _db_connection_healthy = True
        logger.info("Database connection healthy.")
    except Exception as e:
        _db_connection_healthy = False
        logger.critical(f"FATAL: Database connection check failed: {e}", exc_info=True)
    finally:
        if db_session: db_session.close()

    # Ensure DB tables exist (including Vote table) before starting services
    try:
        from .database import create_tables
        create_tables()
        logger.info("Database tables ensured (create_tables called).")
    except Exception as e:
        logger.warning(f"create_tables() had issues: {e}")

    # FIX: Inject dependencies into the CentralOrchestrator
        # UPDATED: Inject ALL dependencies into the CentralOrchestrator
    pubsub_broker_instance = GoogleCloudPubSubBroker()
    # NEW: Initialize the ZKVerifier instance
    zk_verifier_instance = ZKVerifier(
    project_id=getattr(settings, 'GCP_PROJECT_ID', None),
    kms_key_ring_name=getattr(settings, 'KMS_KEY_RING_NAME', None),
    kms_location=getattr(settings, 'KMS_LOCATION', 'global'),
    proving_key_name=getattr(settings, 'PROVING_KEY_NAME', None),
    verification_key_name=getattr(settings, 'VERIFICATION_KEY_NAME', None)
)
    
    priv_central_orchestrator_instance = CentralOrchestrator(
        db_instance=db_instance,
        message_broker=pubsub_broker_instance,
        zk_verifier=zk_verifier_instance # <-- NEW: Pass the instance here
    )
    await priv_central_orchestrator_instance.start()
    logger.info("PRIV Central Orchestrator started.")

    # Start background tasks
    background_tasks = set()
    # In a real application, you might want some background tasks even in demo mode.
    # This logic can be adjusted as needed.
    news_ingestor = dependencies.get_singleton("global_news_ingestor")
    scraper_task = asyncio.create_task(run_scrapers_periodically(news_ingestor))
    background_tasks.add(scraper_task)

    market_data_ingestor = dependencies.get_singleton("market_data_ingestor")
    market_data_task = asyncio.create_task(run_market_data_polling_periodically(market_data_ingestor))
    background_tasks.add(market_data_task)

    broker_router = dependencies.get_singleton("broker_router")
    broker_monitor_task = asyncio.create_task(run_broker_account_monitoring_periodically(broker_router, pubsub_broker_instance))
    background_tasks.add(broker_monitor_task)
    logger.info("Background tasks started.")

    logger.info("--- PRIV Application Startup Sequence Complete. Ready! ---")
    
    try:
        yield
    finally:
        logger.info("--- PRIV Application Shutdown Sequence Initiated ---")
        
        # Shutdown MATLAB engine gracefully
        try:
            from backend.utils.matlab_integration import get_matlab_engine
            matlab_engine = get_matlab_engine()
            matlab_engine.shutdown()
        except Exception as e:
            logger.warning(f"Error shutting down MATLAB engine: {e}")
        
        for task in background_tasks:
            task.cancel()
        if background_tasks:
            await asyncio.gather(*background_tasks, return_exceptions=True)
        
        if priv_central_orchestrator_instance:
            await priv_central_orchestrator_instance.stop()
            logger.info("PRIV Central Orchestrator stopped.")
            
        logger.info("--- PRIV Application Shutdown Sequence Complete ---")


app = FastAPI(
    title=settings.APP_NAME,
    description="API for the Sans Mercantile AI Trading and Analysis System (PRIV).",
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS Configuration - hardcoded to avoid Settings class issues
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:5555", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Routers ---
# New endpoints for frontend dashboard
app.include_router(portfolio_api.router, prefix="/api/v1/portfolio", tags=["Portfolio"])
app.include_router(market_api.router, prefix="/api/v1/market", tags=["Market Data"])
app.include_router(agents_api.router, prefix="/api/v1/agents", tags=["Agents"])
app.include_router(agent_orchestration_api.router, prefix="/api/v1/orchestration", tags=["Agent Orchestration"])
app.include_router(system_api.router, prefix="/api/v1/system", tags=["System"])
app.include_router(chat_api.router, tags=["Chat AI"])
app.include_router(governance_api.router, prefix="/api/v1/governance", tags=["Governance"])

# New system pages APIs (always available)
app.include_router(news_api.router, prefix="/api/v1/news", tags=["News"])
app.include_router(new_analytics_api.router, prefix="/api/v1/analytics-new", tags=["Analytics New"])
app.include_router(new_history_api.router, prefix="/api/v1/history-new", tags=["History New"])
app.include_router(new_connections_api.router, prefix="/api/v1/connections", tags=["Connections"])

# Broker management API (optional when broker deps are available)
if broker_endpoints:
    app.include_router(broker_endpoints.router, tags=["Broker Management"])

# Existing endpoints - only include if available
# Prefer first-class profile_api if support_ai provides it, otherwise use demo_profile_api
if profile_api:
    app.include_router(profile_api.router, prefix="/api/v1/profile", tags=["User Profile"])
elif demo_profile_api:
    app.include_router(demo_profile_api.router, prefix="/api/v1/profile", tags=["User Profile (Demo)"])

# Include tax API (demo) if available
if demo_tax_api:
    app.include_router(demo_tax_api.router, prefix="/api/v1/tax", tags=["Tax & Compliance"])

if history_api:
    app.include_router(history_api.router, prefix="/api/v1/history", tags=["Conversation History"])
if analytics_api:
    app.include_router(analytics_api.router, prefix="/api/v1/analytics", tags=["Analytics"])
if insight_api:
    app.include_router(insight_api.router, prefix="/api/v1/insights", tags=["Market Insights"])
if elliott_wave_api:
    app.include_router(elliott_wave_api.router, prefix="/api/v1/elliottwave", tags=["Technical Analysis"])
if audio_api:
    app.include_router(audio_api.router, prefix="/api/v1/audio", tags=["Advanced IO"])
if vision_api:
    app.include_router(vision_api.router, prefix="/api/v1/vision", tags=["Advanced IO"])
if alert_api:
    app.include_router(alert_api.router, prefix="/api/v1/trading", tags=["Trading Engine"])
if connections_api:
    app.include_router(connections_api.router, prefix="/api/v1/trading", tags=["Trading Engine"])
if oauth_api:
    app.include_router(oauth_api.router, prefix="/api/v1/auth", tags=["Trading Engine"])
if risk_api:
    app.include_router(risk_api.router, prefix="/api/v1/risk", tags=["Risk Analysis"])
if emotion_relay_api:
    app.include_router(emotion_relay_api.router, prefix="/api/v1/emotion", tags=["Emotion Feedback"])
if market_insights_api:
    app.include_router(market_insights_api.router, prefix="/api/v1/market-insights", tags=["Market Insights"])
if agi_api:
    app.include_router(agi_api.router, prefix="/api/v1/agi", tags=["AGI Core"])
if departmental_api:
    app.include_router(departmental_api.router, prefix="/api/v1/departments", tags=["Departmental Agents"])
if payment_api:
    app.include_router(payment_api.router, tags=["Payment & Subscriptions"])

if support_api:
    app.include_router(support_api.router, prefix="/api/v1/support", tags=["Support AI"])
    logger.info("Support AI router mounted successfully under /api/v1/support")

if video_streaming_api:
    app.include_router(video_streaming_api.router, prefix="/api/v1/support/video", tags=["Support AI Video Stream"])
    logger.info("Support AI Video Stream router mounted successfully under /api/v1/support/video")

if avatar_sub_app:
    app.mount("/api/v1/avatar-system", avatar_sub_app)
    logger.info("Avatar System mounted successfully under /api/v1/avatar-system")

# --- Health & Root Endpoints ---
@app.get("/", tags=["Root"])
async def read_root():
    return {"message": f"Welcome to {settings.APP_NAME} v{settings.APP_VERSION}!"}

@app.get("/healthz", tags=["Health"])
async def healthz():
    if not priv_central_orchestrator_instance or not priv_central_orchestrator_instance.is_running:
        raise HTTPException(status_code=503, detail="PRIV Central Orchestrator is not running.")
    return {"status": "ok"}

@app.get("/readyz", tags=["Health"])
async def readyz():
    if not all([_firestore_initialized, _db_connection_healthy, _all_singletons_initialized,
                priv_central_orchestrator_instance and priv_central_orchestrator_instance.is_running]):
        raise HTTPException(status_code=503, detail="Application is not ready.")
    return {"status": "ready"}

# --- WebSocket Endpoints ---
from fastapi import WebSocket, WebSocketDisconnect
import json

@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """
    WebSocket endpoint for real-time dashboard updates.
    Sends mock data for now.
    """
    await websocket.accept()
    logger.info(f"WebSocket connection accepted from {websocket.client}")
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Send periodic updates every 5 seconds
        while True:
            # Mock dashboard update data
            update_data = {
                "type": "update",
                "data": {
                    "portfolio": {
                        "total_value": 45500.00,
                        "daily_change": 350.00,
                        "daily_change_pct": 0.77
                    },
                    "market": {
                        "sp500": 4750.00,
                        "sp500_change": 0.54
                    },
                    "alerts": [],
                    "active_agents": 4
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await websocket.send_json(update_data)
            await asyncio.sleep(5)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected from {websocket.client}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass

if settings.DEMO_MODE:
    @app.get("/users", tags=["Demo"])
    def get_users():
        return [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=settings.UVICORN_PORT, reload=True, reload_dirs=["backend"])

