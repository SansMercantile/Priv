"""
Sandbox module for avatar microservice.
Provides test/demo config and mocks for avatar operations.
"""

class AvatarSandbox:
    def __init__(self):
        self.status = "sandbox mode"

    def mock_avatar(self):
        return "Avatar operation (sandboxed)"
