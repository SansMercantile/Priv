"""
PRIV Cloud Configuration Module
================================

Centralized cloud configuration for PRIV system with multi-cloud support.
Handles GCP, Azure, AWS, and Firebase integrations with graceful fallbacks.

Author: SuperNinja AI Agent
Date: 2025-01-16
"""

import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class DeploymentMode(str, Enum):
    """Deployment modes for PRIV"""
    LOCAL = "local"
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class CloudProvider(str, Enum):
    """Supported cloud providers"""
    GCP = "gcp"
    AZURE = "azure"
    AWS = "aws"
    FIREBASE = "firebase"


@dataclass
class CloudConfig:
    """Cloud configuration settings"""
    
    # Deployment settings
    deployment_mode: DeploymentMode = DeploymentMode.LOCAL
    
    # GCP settings
    gcp_project_id: Optional[str] = None
    gcp_region: Optional[str] = None
    gcp_available: bool = False
    
    # Azure settings
    azure_subscription_id: Optional[str] = None
    azure_resource_group: Optional[str] = None
    azure_region: Optional[str] = None
    azure_available: bool = False
    
    # AWS settings
    aws_region: Optional[str] = None
    aws_account_id: Optional[str] = None
    aws_available: bool = False
    
    # Firebase settings
    firebase_project_id: Optional[str] = None
    firebase_available: bool = False
    
    # Feature flags
    enable_cloud_storage: bool = False
    enable_cloud_functions: bool = False
    enable_cloud_messaging: bool = False
    enable_cloud_ml: bool = False
    enable_quantum_computing: bool = False
    
    # Fallback settings
    use_local_fallback: bool = True
    mock_cloud_services: bool = False


def load_cloud_config() -> CloudConfig:
    """
    Load cloud configuration from environment variables.
    
    Returns:
        CloudConfig: Configured cloud settings
    """
    # Determine deployment mode
    deployment_mode_str = os.getenv('DEPLOYMENT_MODE', 'local').lower()
    try:
        deployment_mode = DeploymentMode(deployment_mode_str)
    except ValueError:
        logger.warning(f"Invalid deployment mode: {deployment_mode_str}, defaulting to LOCAL")
        deployment_mode = DeploymentMode.LOCAL
    
    # GCP configuration
    gcp_project_id = os.getenv('GCP_PROJECT_ID')
    gcp_region = os.getenv('GCP_REGION', 'us-central1')
    gcp_available = bool(gcp_project_id) and _check_gcp_availability()
    
    # Azure configuration
    azure_subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
    azure_resource_group = os.getenv('AZURE_RESOURCE_GROUP')
    azure_region = os.getenv('AZURE_REGION', 'eastus')
    azure_available = bool(azure_subscription_id) and _check_azure_availability()
    
    # AWS configuration
    aws_region = os.getenv('AWS_REGION', 'us-east-1')
    aws_account_id = os.getenv('AWS_ACCOUNT_ID')
    aws_available = bool(aws_account_id) and _check_aws_availability()
    
    # Firebase configuration
    firebase_project_id = os.getenv('FIREBASE_PROJECT_ID', gcp_project_id)
    firebase_available = bool(firebase_project_id) and _check_firebase_availability()
    
    # Feature flags
    enable_cloud_storage = os.getenv('ENABLE_CLOUD_STORAGE', 'false').lower() == 'true'
    enable_cloud_functions = os.getenv('ENABLE_CLOUD_FUNCTIONS', 'false').lower() == 'true'
    enable_cloud_messaging = os.getenv('ENABLE_CLOUD_MESSAGING', 'false').lower() == 'true'
    enable_cloud_ml = os.getenv('ENABLE_CLOUD_ML', 'false').lower() == 'true'
    enable_quantum_computing = os.getenv('ENABLE_QUANTUM_COMPUTING', 'false').lower() == 'true'
    
    # Fallback settings
    use_local_fallback = os.getenv('USE_LOCAL_FALLBACK', 'true').lower() == 'true'
    mock_cloud_services = os.getenv('MOCK_CLOUD_SERVICES', 'false').lower() == 'true'
    
    config = CloudConfig(
        deployment_mode=deployment_mode,
        gcp_project_id=gcp_project_id,
        gcp_region=gcp_region,
        gcp_available=gcp_available,
        azure_subscription_id=azure_subscription_id,
        azure_resource_group=azure_resource_group,
        azure_region=azure_region,
        azure_available=azure_available,
        aws_region=aws_region,
        aws_account_id=aws_account_id,
        aws_available=aws_available,
        firebase_project_id=firebase_project_id,
        firebase_available=firebase_available,
        enable_cloud_storage=enable_cloud_storage,
        enable_cloud_functions=enable_cloud_functions,
        enable_cloud_messaging=enable_cloud_messaging,
        enable_cloud_ml=enable_cloud_ml,
        enable_quantum_computing=enable_quantum_computing,
        use_local_fallback=use_local_fallback,
        mock_cloud_services=mock_cloud_services
    )
    
    _log_cloud_config(config)
    return config


def _check_gcp_availability() -> bool:
    """Check if GCP services are available"""
    try:
        from google.cloud import storage
        # Try to create a client (doesn't make API call)
        storage.Client()
        return True
    except Exception as e:
        logger.debug(f"GCP not available: {e}")
        return False


def _check_azure_availability() -> bool:
    """Check if Azure services are available"""
    try:
        from azure.identity import DefaultAzureCredential
        # Try to create credential (doesn't make API call)
        DefaultAzureCredential()
        return True
    except Exception as e:
        logger.debug(f"Azure not available: {e}")
        return False


def _check_aws_availability() -> bool:
    """Check if AWS services are available"""
    try:
        import boto3
        # Try to create session (doesn't make API call)
        boto3.Session()
        return True
    except Exception as e:
        logger.debug(f"AWS not available: {e}")
        return False


def _check_firebase_availability() -> bool:
    """Check if Firebase services are available"""
    try:
        import firebase_admin
        return True
    except Exception as e:
        logger.debug(f"Firebase not available: {e}")
        return False


def _log_cloud_config(config: CloudConfig) -> None:
    """Log cloud configuration status"""
    logger.info("=" * 60)
    logger.info("PRIV Cloud Configuration")
    logger.info("=" * 60)
    logger.info(f"Deployment Mode: {config.deployment_mode.value}")
    logger.info(f"")
    logger.info(f"Cloud Providers:")
    logger.info(f"  GCP:      {'✓ Available' if config.gcp_available else '✗ Not Available'}")
    if config.gcp_available:
        logger.info(f"    Project: {config.gcp_project_id}")
        logger.info(f"    Region:  {config.gcp_region}")
    logger.info(f"  Azure:    {'✓ Available' if config.azure_available else '✗ Not Available'}")
    if config.azure_available:
        logger.info(f"    Subscription: {config.azure_subscription_id}")
        logger.info(f"    Region:       {config.azure_region}")
    logger.info(f"  AWS:      {'✓ Available' if config.aws_available else '✗ Not Available'}")
    if config.aws_available:
        logger.info(f"    Account: {config.aws_account_id}")
        logger.info(f"    Region:  {config.aws_region}")
    logger.info(f"  Firebase: {'✓ Available' if config.firebase_available else '✗ Not Available'}")
    logger.info(f"")
    logger.info(f"Feature Flags:")
    logger.info(f"  Cloud Storage:        {config.enable_cloud_storage}")
    logger.info(f"  Cloud Functions:      {config.enable_cloud_functions}")
    logger.info(f"  Cloud Messaging:      {config.enable_cloud_messaging}")
    logger.info(f"  Cloud ML:             {config.enable_cloud_ml}")
    logger.info(f"  Quantum Computing:    {config.enable_quantum_computing}")
    logger.info(f"")
    logger.info(f"Fallback Settings:")
    logger.info(f"  Use Local Fallback:   {config.use_local_fallback}")
    logger.info(f"  Mock Cloud Services:  {config.mock_cloud_services}")
    logger.info("=" * 60)


# Global cloud configuration instance
_cloud_config: Optional[CloudConfig] = None


def get_cloud_config() -> CloudConfig:
    """
    Get the global cloud configuration instance.
    
    Returns:
        CloudConfig: Global cloud configuration
    """
    global _cloud_config
    if _cloud_config is None:
        _cloud_config = load_cloud_config()
    return _cloud_config


def is_cloud_enabled(provider: CloudProvider) -> bool:
    """
    Check if a specific cloud provider is enabled.
    
    Args:
        provider: Cloud provider to check
        
    Returns:
        bool: True if provider is available
    """
    config = get_cloud_config()
    
    if provider == CloudProvider.GCP:
        return config.gcp_available
    elif provider == CloudProvider.AZURE:
        return config.azure_available
    elif provider == CloudProvider.AWS:
        return config.aws_available
    elif provider == CloudProvider.FIREBASE:
        return config.firebase_available
    
    return False


def is_production() -> bool:
    """Check if running in production mode"""
    config = get_cloud_config()
    return config.deployment_mode == DeploymentMode.PRODUCTION


def is_local() -> bool:
    """Check if running in local mode"""
    config = get_cloud_config()
    return config.deployment_mode == DeploymentMode.LOCAL


def should_use_cloud_feature(feature: str) -> bool:
    """
    Check if a cloud feature should be used.
    
    Args:
        feature: Feature name (storage, functions, messaging, ml, quantum)
        
    Returns:
        bool: True if feature should be used
    """
    config = get_cloud_config()
    
    feature_map = {
        'storage': config.enable_cloud_storage,
        'functions': config.enable_cloud_functions,
        'messaging': config.enable_cloud_messaging,
        'ml': config.enable_cloud_ml,
        'quantum': config.enable_quantum_computing
    }
    
    return feature_map.get(feature.lower(), False)