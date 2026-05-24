# backend/support_ai/core_ai_handler.py

import logging
import os
from typing import Optional, Dict, Any

# Correctly import the centralized settings object
from backend.config import settings
from backend.support_ai.analytics_engine import AnalyticsEngine

# Make Google API optional
try:
    from google.api_core.exceptions import GoogleAPIError
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    GoogleAPIError = Exception
    logger = logging.getLogger(__name__)
    logger.warning("Google API not available. Some cloud features will be disabled.")

from backend.data_sourcing.data_loader import get_market_data
from backend.support_ai.indicators.elliott_wave.ewa import EwaController
from backend.strategy_engine.fuzzy_controller import FuzzyController
from backend.ml_pipeline.model_predictor import MLModelPredictor

# --- Setup Logging ---
logger = logging.getLogger(__name__)

# Conditionally import Vertex AI SDK components to support DEMO_MODE
if not settings.DEMO_MODE:
    try:
        from vertexai.generative_models import GenerativeModel
    except ImportError:
        GenerativeModel = None
        logger.warning("Could not import vertexai. Please install google-cloud-aiplatform.")
else:
    GenerativeModel = None

# --- Global State for Analysis Engines ---
EWM_RULES_FILEPATH = "backend/support_ai/indicators/elliott_wave/EWM.txt"
ewa_controller = None
try:
    if os.path.exists(EWM_RULES_FILEPATH):
        ewa_controller = EwaController(rules_filepath=EWM_RULES_FILEPATH)
        ewa_controller.initialize()
        logger.info("Elliott Wave Analysis Controller initialized successfully.")
    else:
        logger.warning(f"EWM.txt not found at {EWM_RULES_FILEPATH}. Elliott Wave Analysis will be disabled.")
except Exception as e:
    logger.critical(f"FATAL: Could not initialize Elliott Wave Analysis Controller: {e}", exc_info=True)

analytics_engine_global_instance = AnalyticsEngine()
fuzzy_controller_global_instance = FuzzyController()
model_predictor_global_instance = MLModelPredictor()
logger.info("Initialized Analytics, Fuzzy, and ML Predictor singletons.")

class LLMClient:
    """
    Client for interacting with Google's LLMs via Vertex AI.
    Handles DEMO_MODE by simulating responses.
    """
    def __init__(self):
        self.model = None
        if not settings.DEMO_MODE and GenerativeModel:
            try:
                self.model = GenerativeModel(settings.LLM_MODEL_NAME)
                logger.info(f"LLMClient initialized with model: {settings.LLM_MODEL_NAME}")
            except Exception as e:
                self.model = None
                logger.critical(f"FATAL: Failed to initialize Vertex AI GenerativeModel: {e}", exc_info=True)
        elif settings.DEMO_MODE:
            logger.info("LLMClient: Skipping Vertex AI model initialization in DEMO_MODE.")
        else:
            logger.error("LLMClient: Vertex AI SDK not available. Live mode will fail.")

    def _construct_persona_prompt(self, base_prompt: str, persona: Optional[Dict[str, Any]]) -> str:
        if not persona:
            return base_prompt
        identity = persona.get('identity_and_origin', 'an advanced AI assistant')
        purpose = persona.get('purpose', 'to be helpful and informative')
        traits = persona.get('personality_traits', [])
        persona_header = (
            f"You are an AI persona. Your identity is: {identity}. "
            f"Your core purpose is: {purpose}. "
            f"Your key personality traits are: {', '.join(traits)}. "
            "You must answer all queries strictly from this perspective. Do not break character.\n\n"
            "--- User Query ---\n"
        )
        return persona_header + base_prompt

    async def generate_text(self, prompt: str, persona: Optional[Dict[str, Any]] = None, temperature: float = 0.7) -> str:
        if not self.model:
            return f"Simulated AI Response (DEMO_MODE): '{prompt}'"
        
        final_prompt = self._construct_persona_prompt(prompt, persona)
        try:
            response = await self.model.generate_content_async(
                final_prompt,
                generation_config={"temperature": temperature}
            )
            return response.text.strip()
        except GoogleAPIError as e:
            logger.error(f"LLM API error during text generation: {e}", exc_info=True)
            return "I'm sorry, I encountered a problem communicating with my core intelligence. Please try again."
        except Exception as e:
            logger.error(f"Unexpected error during text generation: {e}", exc_info=True)
            return "I'm sorry, a critical internal error occurred."

async def get_latest_ai_analysis(symbol: str = "GOLD") -> Dict[str, Any]:
    """
    Orchestrates the full AI analysis pipeline for a given symbol.
    """
    logger.info(f"Starting full AI analysis for symbol: {symbol}")
    df = await get_market_data(symbol=symbol, timeframe="daily")
    if df is None or df.empty:
        logger.error(f"Could not retrieve market data for {symbol}.")
        return {"error": f"Could not retrieve market data for {symbol}."}

    analysis_results = analytics_engine_global_instance.calculate_indicators(
        df, ewa_controller_instance=ewa_controller
    )
    if "error" in analysis_results:
        logger.error(f"Error during initial analysis for {symbol}: {analysis_results['error']}")
        return analysis_results

    try:
        analysis_results['fuzzy_logic_signal'] = fuzzy_controller_global_instance.get_signal(analysis_results)
        df_with_indicators = df.copy()
        for key, value in analysis_results.items():
            if isinstance(value, list) and len(value) == len(df_with_indicators):
                df_with_indicators[key] = value
        analysis_results['ml_prediction'] = model_predictor_global_instance.predict(df_with_indicators)
        logger.info(f"Successfully integrated fuzzy logic and ML predictions for {symbol}.")
    except Exception as e:
        logger.error(f"Error during fuzzy/ML processing for {symbol}: {e}", exc_info=True)
        analysis_results['processing_error'] = str(e)

    return analysis_results

