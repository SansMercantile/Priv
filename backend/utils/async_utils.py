# utils/async_utils.py
# Utility functions for asynchronous operations with retry logic.

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import logging

logger = logging.getLogger(__name__)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception)
)
async def async_retry_api_call(api_func, *args, **kwargs):
    """
    Generic async retry wrapper for API calls.
    """
    logger.debug(f"Calling {api_func.__name__} with retry logic...")
    try:
        return await api_func(*args, **kwargs)
    except Exception as e:
        logger.warning(f"API call {api_func.__name__} failed. Retrying...")
        raise
