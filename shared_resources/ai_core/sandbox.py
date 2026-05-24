"""
Sandbox module for ai_core microservice.
Provides test/demo config and mocks for AI core operations.
"""

class AICoreSandbox:
    def __init__(self):
        self.status = "sandbox mode"

    def mock_inference(self):
        return "AI core inference (sandboxed)"
