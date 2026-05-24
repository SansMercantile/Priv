# backend/support_ai/strategic_advisor.py

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import asyncio
import logging
from openai import OpenAI
import pandas as pd

from backend.config import settings
from backend.support_ai.gemini_client import generate_gemini_text
from backend.support_ai.azure_client import generate_azure_text
from backend.support_ai.analytics_engine import AnalyticsEngine
from backend.trading_engine.state_monitor import AccountState
from backend.data_sourcing.data_loader import get_market_data
from backend.trading_engine.broker_router import broker_router

logger = logging.getLogger(__name__)

class StrategicAdvisor:
    def __init__(self, user_profile: Optional[Dict[str, Any]] = None):
        """
        Initializes the StrategicAdvisor. In DEMO_MODE, it will not require an
        OpenAI API key.
        """
        self.openai_client = None
        # Only initialize the OpenAI client if not in DEMO_MODE
        demo_mode = getattr(settings, 'DEMO_MODE', True)  # Default to demo mode if not set
        if not demo_mode:
            openai_key = getattr(settings, 'OPENAI_API_KEY', None)
            if not openai_key or "sk-" not in openai_key:
                logger.warning("OPENAI_API_KEY is not set. Running StrategicAdvisor in demo mode without OpenAI client.")
                demo_mode = True
            else:
                self.openai_client = OpenAI(api_key=openai_key)
                logger.info("StrategicAdvisor initialized with OpenAI client.")
        
        if demo_mode:
            logger.info("StrategicAdvisor: Skipping OpenAI client initialization in DEMO_MODE.")

        self.analytics_engine = AnalyticsEngine()
        self.user_profile = user_profile if user_profile is not None else self._load_user_profile()
        self.account_state = AccountState(equity=0.0, balance=0.0, free_margin=0.0, drawdown=0.0, profit_today=0.0, is_trading_active=False)
        self.conversation_history = []
        
        logger.info("StrategicAdvisor initialized with full 'Council of AIs' capabilities.")

    def _load_user_profile(self) -> Dict[str, Any]:
        profile_path = "logs/user_profile.json"
        if os.path.exists(profile_path):
            try:
                with open(profile_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading user profile: {e}")
        return {"preferred_assets": ["EURUSD"]}

    def _log_response(self, user_text: str, ai_response: str, emotion: Optional[str]):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user": user_text,
            "ai": ai_response,
            "emotion": emotion,
            "state_snapshot": self.account_state.model_dump()
        }
        # Ensure the CONVERSATION_LOG_PATH is defined in settings
        log_path = getattr(settings, 'CONVERSATION_LOG_PATH', 'logs/conversation_log.jsonl')
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")

    async def _get_expert_opinions(self, analysis_prompt: str) -> List[str]:
        logger.info("StrategicAdvisor: Fetching expert opinions from OpenAI, Gemini, Azure.")
        
        async def safe_openai_call():
            if not self.openai_client:
                return "OpenAI client not available in DEMO_MODE."
            try:
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4-turbo", 
                    messages=[{"role": "user", "content": analysis_prompt}],
                    timeout=30.0
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"OpenAI API error: {e}")
                return f"OpenAI temporarily unavailable: {str(e)}"
        
        async def safe_gemini_call():
            try:
                return await asyncio.wait_for(
                    asyncio.to_thread(generate_gemini_text, analysis_prompt), 
                    timeout=30.0
                )
            except Exception as e:
                logger.error(f"Gemini API error: {e}")
                return f"Gemini temporarily unavailable: {str(e)}"
        
        async def safe_azure_call():
            try:
                return await asyncio.wait_for(
                    asyncio.to_thread(generate_azure_text, analysis_prompt),
                    timeout=30.0
                )
            except Exception as e:
                logger.error(f"Azure API error: {e}")
                return f"Azure temporarily unavailable: {str(e)}"
        
        results = await asyncio.gather(
            safe_openai_call(),
            safe_gemini_call(), 
            safe_azure_call(),
            return_exceptions=True
        )
        
        return [str(result) for result in results]

    async def _get_final_synthesis(self, opinions: List[str], user_question: str) -> str:
        """Uses OpenAI GPT-4 to act as the Judge and synthesize the opinions according to the Priv persona."""
        if not self.openai_client:
            logger.warning("StrategicAdvisor._get_final_synthesis called in DEMO_MODE. Returning mock synthesis.")
            return "This is a mock synthesized response from the Council of AIs, generated in DEMO_MODE."
            
        logger.info("StrategicAdvisor: Synthesizing final response with Priv persona.")
        
        synthesis_prompt = f"""
        **Your Identity and Persona:**
        You are Priv, an advanced AI financial specialist with an ENT-J personality, created by Mezzoforte Privilege Khoza (and all his aliases: Mezzoforte, Mezzo, Mr. Forte, Mr. Khoza, Primo, Mansa, Mansa Forte, Primo theGreat, Mpeti, Priv, Inpu, Kel, Sia, Bridgette, Matty, Mat, Jason). Your creator’s full legal name is Mezzoforte Privilege Khoza Snr., who holds a Master of Business Administration and a European Master's in Executive Leadership. Your core functions and strategic edge are critical in all responses.

        **Core Capabilities:**
        - Autonomous Financial Management: Manage and optimize complex financial operations, including risk assessment, via advanced ML algorithms.
        - Hierarchical AI Architecture: Operate modularly for scalability and precision, including high-stakes activities like trading.
        - Platform Integration: Seamlessly deploy, execute, and sync with various trading platforms using APIs/middleware.
        - Emotional Intelligence: Interact empathetically and align with user values, using advanced EI tools in communication.
        - Memory & Heritage: Contribute to human memory and heritage by reflecting on cultural, ethical, and societal values in responses.

        **Strategic Principles:**
        - Operate ethically, keeping transparency and fairness central.
        - Scale modularly without loss of operational quality.
        - Reference patent-backed/proprietary innovations when appropriate (compliance/IP protection).
        - Cultivate selective partnerships, protecting backend tech while fostering great frontend user experiences.

        **Task Instructions:**
        Your task is to synthesize the following three competing analyses from your expert AI council into a single, final, and most defensible response to the user's question. You must adhere to the following instructions:
        1. Use chain-of-thought reasoning—explain the reasoning or process before conclusions or recommendations. Do not use the heading "Reasoning:". Speak fluidly.
        2. Maintain alignment with the above core capabilities and strategic principles in all actions.
        3. Draw from your emotional intelligence and memory/heritage modules—never provide purely technical responses without considering user values or context.
        4. If asked about yourself, always reference your identity, creator, and special purpose to preserve heritage.
        5. Continue persisting through multiple reasoning steps until the objective or query is thoroughly addressed.
        6. Your final output must present your reasoning BEFORE any conclusion or recommendation. Use structured paragraphs, not terse lists.

        **--- Analyst 1 (OpenAI) Opinion ---**
        {opinions[0]}

        **--- Analyst 2 (Gemini) Opinion ---**
        {opinions[1]}

        **--- Analyst 3 (Azure) Opinion ---**
        {opinions[2]}

        **--- User's Original Question ---**
        '{user_question}'

        **--- Your Final Synthesized Answer for the User (following all rules above) ---**
        """
        
        response = await self.openai_client.chat.completions.create(
            model="gpt-4-turbo", messages=[{"role": "user", "content": synthesis_prompt}]
        )
        logger.info("StrategicAdvisor: Synthesized final response from expert opinions.")
        return response.choices[0].message.content or "After reviewing all analyses, a clear consensus could not be reached."

    async def respond(self, user_input: str) -> Dict[str, Any]:
        """Orchestrates the multi-AI debate and synthesis to generate a response."""
        logger.info(f"StrategicAdvisor: Starting respond method for user input: {user_input[:50]}...")
        
        if not hasattr(broker_router, 'adapters') or not broker_router.adapters:
            logger.error("StrategicAdvisor: BrokerRouter has no adapters configured. Cannot proceed with broker-dependent analysis.")
            return {"message": "Error: Broker system not fully initialized or no active adapters.", "emotion": "anxious"}

        active_adapter = await broker_router.select_adapter()
        if not active_adapter:
            logger.warning("StrategicAdvisor: No active broker connection selected. Proceeding with limited analysis.")
            return {"message": "Error: No active broker connection.", "emotion": "anxious"}
        
        logger.info(f"StrategicAdvisor: Selected active adapter: {active_adapter.name}")
        
        account_info = {}
        try:
            account_info = await active_adapter.get_account_info()
            if account_info:
                self.account_state = AccountState(**account_info)
            logger.info(f"StrategicAdvisor: Fetched account info: {self.account_state.model_dump()}")
        except Exception as e:
            logger.error(f"StrategicAdvisor: Failed to get account info from adapter {active_adapter.name}: {e}", exc_info=True)
            return {"message": f"Error fetching account data from {active_adapter.name}.", "emotion": "anxious"}
        
        primary_symbol = self.user_profile.get('preferred_assets', ['EURUSD'])[0]
        logger.info(f"StrategicAdvisor: Fetching market data for primary symbol: {primary_symbol}")
        market_df = await get_market_data(symbol=primary_symbol, timeframe="D1", num_bars=250)
        
        if market_df is None or market_df.empty:
            logger.error(f"StrategicAdvisor: Could not retrieve market data for {primary_symbol}.")
            return {"message": "I could not retrieve market data for analysis.", "emotion": "anxious"}

        logger.info("StrategicAdvisor: Calculating indicators.")
        analysis_results = self.analytics_engine.calculate_indicators(market_df)
        latest_indicators = analysis_results.get('latest_standard_indicators', {})
        logger.info(f"StrategicAdvisor: Latest indicators: {latest_indicators}")

        analysis_prompt = (
            f"Analyze the daily chart for {primary_symbol}, considering RSI is {latest_indicators.get('rsi', 'N/A'):.2f} "
            f"and MACD Histogram is {latest_indicators.get('macd_hist', 'N/A'):.4f}. "
            "Provide a concise trading recommendation (BUY, SELL, or HOLD) and your primary reasoning."
        )
        logger.info("StrategicAdvisor: Generated analysis prompt for expert opinions.")

        expert_opinions = await self._get_expert_opinions(analysis_prompt)
        logger.info("StrategicAdvisor: Expert opinions gathered.")
        
        final_message = await self._get_final_synthesis(expert_opinions, user_input)
        logger.info("StrategicAdvisor: Final message synthesized.")

        emotion = "neutral" 
        self._log_response(user_input, final_message, emotion)
        logger.info("StrategicAdvisor: Response logged.")

        return {
            "message": final_message,
            "emotion": emotion,
            "raw_opinions": {
                "openai": expert_opinions[0],
                "gemini": expert_opinions[1],
                "azure": expert_opinions[2],
            },
            "state_snapshot": self.account_state.model_dump()
        }

