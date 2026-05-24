# backend/support_ai/azure_client.py

import logging
from backend.config import settings

logger = logging.getLogger(__name__)

try:
    from openai import AzureOpenAI
    AZURE_OPENAI_AVAILABLE = True
except ImportError:
    AzureOpenAI = None
    AZURE_OPENAI_AVAILABLE = False
    logger.warning("Azure OpenAI SDK not available. Azure client will be disabled.")

# --- Configure the Azure OpenAI Client at the module level ---
azure_client = None
# --- FIX: Only try to configure the client if it's enabled AND all keys are present ---
if AZURE_OPENAI_AVAILABLE and settings.ENABLE_AZURE_ADAPTER and all([settings.AZURE_OPENAI_ENDPOINT, settings.AZURE_OPENAI_KEY, settings.AZURE_OPENAI_DEPLOYMENT_NAME]):
    try:
        azure_client = AzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
        )
        logger.info("Azure OpenAI client configured successfully.")
    except Exception as e:
        logger.error(f"Failed to configure Azure OpenAI client: {e}", exc_info=True)
else:
    logger.warning("Azure OpenAI is not enabled or credentials are not fully set. Azure client will not be available.")


def generate_azure_text(prompt: str) -> str:
    """
    Generates a text response from the deployed Azure OpenAI model.
    """
    if not azure_client:
        return "Azure OpenAI client is not configured or enabled."
        
    try:
        response = azure_client.chat.completions.create(
            model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful financial assistant."},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content or "No content returned from Azure."
    except Exception as e:
        logger.error(f"Error generating content with Azure OpenAI: {e}", exc_info=True)
        return f"Error: Could not get a response from Azure OpenAI. Details: {e}"