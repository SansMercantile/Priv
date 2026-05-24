"""
Sandbox module for arbitration_protocols microservice.
Provides test/demo config and mocks for arbitration protocol operations.
"""

class ArbitrationProtocolsSandbox:
    def __init__(self):
        self.status = "sandbox mode"

    def mock_arbitrate(self):
        return "Arbitration protocol (sandboxed)"
