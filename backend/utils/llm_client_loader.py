import os

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
try:
    from mpeti_modules.ai_ops import LLMClient
except ModuleNotFoundError:
    class LLMClient:
        def __init__(self, *args, **kwargs):
            pass
        def explain(self, input_text: str) -> str:
            return f"[Mock LLMClient] {input_text}"
