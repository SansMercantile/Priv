"""
Sandbox module for agi_core microservice.
Provides test/demo config and mocks for AGI core operations.
"""

class AGICoreSandbox:
    def __init__(self):
        self.status = "sandbox mode"

    def mock_decision(self):
        return "AGI core decision (sandboxed)"
