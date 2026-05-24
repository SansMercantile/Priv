# Make config a package for import resolution
from .settings import Settings

def get_settings():
    """Get the application settings instance"""
    return Settings()

# Create a default settings instance for backward compatibility
settings = Settings()
