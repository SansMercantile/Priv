"""
Sandbox module for agent_templates microservice.
Provides test/demo config and mocks for agent template operations.
"""

class AgentTemplateSandbox:
    def __init__(self):
        self.status = "sandbox mode"

    def mock_action(self):
        return "Agent template action (sandboxed)"
