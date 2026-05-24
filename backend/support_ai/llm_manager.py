import os
import logging
import asyncio
from typing import Dict, Any, List, Optional
from openai import OpenAI
from backend.config import settings

logger = logging.getLogger(__name__)

class LLMManager:
    """
    Centralized LLM Manager for PRIV.
    Handles transition between OpenAI GPT-5.4 and local Ollama resources.
    """
    def __init__(self):
        self.openai_client = None
        self.ollama_client = None
        self._initialize_clients()

    def _initialize_clients(self):
        # OpenAI Initialization
        api_key = os.getenv("OPENAI_API_KEY") or getattr(settings, 'OPENAI_API_KEY', None)
        if api_key and "sk-" in api_key:
            try:
                self.openai_client = OpenAI(api_key=api_key)
                logger.info("LLMManager: OpenAI client initialized.")
            except Exception as e:
                logger.error(f"LLMManager: Failed to initialize OpenAI client: {e}")

        # Ollama Initialization (Local Resource)
        try:
            # Ollama usually runs on port 11434
            self.ollama_client = OpenAI(
                base_url="http://localhost:11434/v1",
                api_key="ollama" # Required but ignored by Ollama
            )
            logger.info("LLMManager: Local Ollama client initialized.")
        except Exception as e:
            logger.error(f"LLMManager: Failed to initialize Ollama client: {e}")

    async def generate_response(
        self, 
        prompt: str, 
        model: str = "gpt-5.4", 
        use_local: bool = False,
        system_prompt: str = "You are Priv, the advanced AI financial specialist.",
        verbosity: str = "medium",
        reasoning_effort: str = "medium"
    ) -> str:
        """
        Unified response generator using the new OpenAI responses.create syntax
        or falling back to local Ollama models.
        """
        if use_local or not self.openai_client:
            return await self._call_ollama(prompt, model, system_prompt)

        try:
            # New OpenAI GPT-5.4 Syntax
            response = self.openai_client.responses.create(
                model=model,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                text={
                    "format": {"type": "text"},
                    "verbosity": verbosity
                },
                reasoning={
                    "effort": reasoning_effort,
                    "summary": "auto"
                },
                store=True,
                include=[
                    "reasoning.encrypted_content",
                    "web_search_call.action.sources"
                ]
            )
            return response.output_text # Assuming the new API returns output_text
        except Exception as e:
            logger.error(f"LLMManager: OpenAI request failed: {e}. Falling back to Ollama.")
            return await self._call_ollama(prompt, model, system_prompt)

    async def _call_ollama(self, prompt: str, model: str, system_prompt: str) -> str:
        """Fallback to local Ollama resources."""
        try:
            # Map gpt models to local ollama models if necessary
            local_model = "llama3" if "gpt" in model else model
            
            response = self.ollama_client.chat.completions.create(
                model=local_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLMManager: Ollama fallback failed: {e}")
            return "Error: AI Core unavailable. Please check local Ollama service."

# Singleton instance
llm_manager = LLMManager()