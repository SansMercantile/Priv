# backend/support_ai/gemini_client.py

import logging

# Make google.generativeai optional
try:
    import google.generativeai as genai
    GOOGLE_AI_AVAILABLE = True
except ImportError:
    GOOGLE_AI_AVAILABLE = False
    genai = None
    logger = logging.getLogger(__name__)
    logger.warning("Google AI Gemini not available. Gemini client will be disabled.")

from backend.config import settings # Import our centralized settings

logger = logging.getLogger(__name__)

# --- Configure the Gemini API at the module level ---
if GOOGLE_AI_AVAILABLE and genai is not None:
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        logger.info("Google AI Gemini client configured successfully.")
    except Exception as e:
        logger.error(f"Failed to configure Gemini client: {e}", exc_info=True)
else:
    logger.warning("Google AI Gemini client not available. Gemini text generation will be disabled.")

# --- Define the Generation Function ---
def generate_gemini_text(prompt: str) -> str:
    """
    Generates a text response from the Gemini Pro model.

    Args:
        prompt (str): The input prompt for the model.

    Returns:
        str: The generated text content from Gemini, or an error message.
    """
    if not GOOGLE_AI_AVAILABLE or genai is None:
        logger.warning("Google AI Gemini not available. Returning fallback response.")
        return f"Gemini not available. Prompt: {prompt[:50]}..."
    
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Error generating content with Gemini: {e}", exc_info=True)
        return f"Error: Could not get a response from Gemini. Details: {e}"