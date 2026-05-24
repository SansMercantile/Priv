import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
from abc import ABC, abstractmethod

from backend.config.settings import Settings

# Create settings instance
_settings = Settings()
import functools

async def async_retry_api_call(func, max_retries=3, delay=1.0, backoff_factor=2.0, *args, **kwargs):
    """Basic async retry logic for API calls."""
    retries = 0
    current_delay = delay
    while retries < max_retries:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            retries += 1
            if retries >= max_retries:
                raise
            await asyncio.sleep(current_delay)
            current_delay *= backoff_factor

logger = logging.getLogger(__name__)

class DataSourceType(str, Enum):
    MARKET_DATA = "market_data"
    NEWS = "news"
    FUNDAMENTAL = "fundamental"
    ECONOMIC_CALENDAR = "economic_calendar"
    BROKER_ACCOUNT = "broker_account"
    IOT_SENSORY = "iot_sensory"
    SOCIAL_SENTIMENT = "social_sentiment"
    ALTERNATIVE_DATA = "alternative_data"

class DataQuality(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    CORRUPTED = "corrupted"

@dataclass
class DataIngestionMetrics:
    source_id: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    consecutive_failures: int = 0
    data_quality_score: float = 1.0
    rate_limit_hits: int = 0

@dataclass
class DataIngestionConfig:
    source_id: str
    source_type: DataSourceType
    api_endpoint: str
    api_key: Optional[str] = None
    rate_limit_per_minute: int = 60
    retry_attempts: int = 3
    timeout_seconds: int = 30
    data_validation_rules: Dict[str, Any] = field(default_factory=dict)
    normalization_rules: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True

class DataValidator:
    """Advanced data validation and quality assessment"""
    
    @staticmethod
    def validate_market_data(data: Dict[str, Any]) -> tuple[bool, DataQuality, List[str]]:
        """Validate market data structure and quality"""
        issues = []
        
        # Required fields check
        required_fields = ['symbol', 'timestamp', 'price']
        for field in required_fields:
            if field not in data:
                issues.append(f"Missing required field: {field}")
        
        # Data type validation
        if 'price' in data:
            try:
                price = float(data['price'])
                if price <= 0:
                    issues.append("Price must be positive")
            except (ValueError, TypeError):
                issues.append("Invalid price format")
        
        # Timestamp validation
        if 'timestamp' in data:
            try:
                if isinstance(data['timestamp'], str):
                    datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
                elif isinstance(data['timestamp'], (int, float)):
                    datetime.fromtimestamp(data['timestamp'])
            except (ValueError, TypeError):
                issues.append("Invalid timestamp format")
        
        # Determine quality
        if len(issues) == 0:
            quality = DataQuality.HIGH
        elif len(issues) <= 2:
            quality = DataQuality.MEDIUM
        elif len(issues) <= 4:
            quality = DataQuality.LOW
        else:
            quality = DataQuality.CORRUPTED
        
        return len(issues) == 0, quality, issues
    
    @staticmethod
    def validate_news_data(data: Dict[str, Any]) -> tuple[bool, DataQuality, List[str]]:
        """Validate news data structure and quality"""
        issues = []
        
        required_fields = ['headline', 'published_at', 'source']
        for field in required_fields:
            if field not in data or not data[field]:
                issues.append(f"Missing or empty field: {field}")
        
        # Content quality checks
        if 'headline' in data:
            headline = str(data['headline'])
            if len(headline) < 10:
                issues.append("Headline too short")
            elif len(headline) > 500:
                issues.append("Headline too long")
        
        # Determine quality
        if len(issues) == 0:
            quality = DataQuality.HIGH
        elif len(issues) <= 1:
            quality = DataQuality.MEDIUM
        else:
            quality = DataQuality.LOW
        
        return len(issues) == 0, quality, issues

class DataNormalizer:
    """Advanced data normalization and standardization"""
    
    @staticmethod
    def normalize_market_data(data: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Normalize market data from different sources"""
        normalized = {
            'symbol': data.get('symbol', '').upper(),
            'source': source,
            'timestamp': DataNormalizer._normalize_timestamp(data.get('timestamp')),
            'data_type': 'market_data'
        }
        
        # Price normalization
        if 'price' in data:
            normalized['price'] = float(data['price'])
        if 'bid' in data:
            normalized['bid'] = float(data['bid'])
        if 'ask' in data:
            normalized['ask'] = float(data['ask'])
        if 'volume' in data:
            normalized['volume'] = float(data['volume'])
        
        # Source-specific normalization
        if source == 'polygon':
            normalized.update(DataNormalizer._normalize_polygon_data(data))
        elif source == 'finnhub':
            normalized.update(DataNormalizer._normalize_finnhub_data(data))
        elif source == 'twelvedata':
            normalized.update(DataNormalizer._normalize_twelvedata_data(data))
        
        return normalized
    
    @staticmethod
    def normalize_news_data(data: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Normalize news data from different sources"""
        normalized = {
            'headline': data.get('headline', data.get('title', '')),
            'content': data.get('content', data.get('description', '')),
            'source': source,
            'published_at': DataNormalizer._normalize_timestamp(data.get('published_at', data.get('publishedAt'))),
            'url': data.get('url', ''),
            'data_type': 'news'
        }
        
        # Extract symbols/tickers if available
        symbols = data.get('symbols', data.get('tickers', []))
        if isinstance(symbols, str):
            symbols = [symbols]
        normalized['symbols'] = symbols
        
        return normalized
    
    @staticmethod
    def _normalize_timestamp(timestamp: Union[str, int, float, None]) -> str:
        """Normalize timestamp to ISO format"""
        if not timestamp:
            return datetime.utcnow().isoformat()
        
        try:
            if isinstance(timestamp, str):
                # Handle various string formats
                if 'T' in timestamp:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                else:
                    dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                return dt.isoformat()
            elif isinstance(timestamp, (int, float)):
                # Handle Unix timestamps (seconds or milliseconds)
                if timestamp > 1e10:  # Milliseconds
                    timestamp = timestamp / 1000
                return datetime.fromtimestamp(timestamp).isoformat()
        except (ValueError, TypeError):
            logger.warning(f"Failed to normalize timestamp: {timestamp}")
            return datetime.utcnow().isoformat()
    
    @staticmethod
    def _normalize_polygon_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Polygon-specific normalization"""
        normalized = {}
        
        # Polygon uses 'c' for close, 'o' for open, etc.
        if 'c' in data:
            normalized['close'] = float(data['c'])
        if 'o' in data:
            normalized['open'] = float(data['o'])
        if 'h' in data:
            normalized['high'] = float(data['h'])
        if 'l' in data:
            normalized['low'] = float(data['l'])
        if 'v' in data:
            normalized['volume'] = float(data['v'])
        
        return normalized
    
    @staticmethod
    def _normalize_finnhub_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Finnhub-specific normalization"""
        normalized = {}
        
        # Finnhub uses 'c' for current price
        if 'c' in data:
            normalized['current_price'] = float(data['c'])
        if 'pc' in data:
            normalized['previous_close'] = float(data['pc'])
        if 'd' in data:
            normalized['change'] = float(data['d'])
        if 'dp' in data:
            normalized['change_percent'] = float(data['dp'])
        
        return normalized
    
    @staticmethod
    def _normalize_twelvedata_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """TwelveData-specific normalization"""
        normalized = {}
        
        # TwelveData uses full names
        if 'close' in data:
            normalized['close'] = float(data['close'])
        if 'open' in data:
            normalized['open'] = float(data['open'])
        if 'high' in data:
            normalized['high'] = float(data['high'])
        if 'low' in data:
            normalized['low'] = float(data['low'])
        if 'volume' in data:
            normalized['volume'] = float(data['volume'])
        
        return normalized

class BaseDataIngestor(ABC):
    """Enhanced base class for all data ingestors"""
    
    def __init__(self, config: DataIngestionConfig, broker):
        self.config = config
        self.broker = broker
        self.metrics = DataIngestionMetrics(source_id=config.source_id)
        self.validator = DataValidator()
        self.normalizer = DataNormalizer()
        self.is_running = False
        self._ingestion_task: Optional[asyncio.Task] = None
    
    async def start_ingestion(self, interval_seconds: int = 60):
        """Start continuous data ingestion"""
        if not self.config.enabled:
            logger.info(f"Data ingestion disabled for {self.config.source_id}")
            return
        
        self.is_running = True
        self._ingestion_task = asyncio.create_task(
            self._ingestion_loop(interval_seconds)
        )
        logger.info(f"Started data ingestion for {self.config.source_id}")
    
    async def stop_ingestion(self):
        """Stop data ingestion"""
        self.is_running = False
        if self._ingestion_task:
            self._ingestion_task.cancel()
            try:
                await self._ingestion_task
            except asyncio.CancelledError:
                pass
        logger.info(f"Stopped data ingestion for {self.config.source_id}")
    
    async def _ingestion_loop(self, interval_seconds: int):
        """Main ingestion loop with error handling and metrics"""
        while self.is_running:
            try:
                start_time = datetime.utcnow()
                
                # Fetch data with retry logic
                raw_data = await async_retry_api_call(
                    self._fetch_data,
                    max_retries=self.config.retry_attempts,
                    delay=1.0,
                    backoff_factor=2.0
                )
                
                if raw_data:
                    # Process and publish data
                    processed_count = await self._process_and_publish_data(raw_data)
                    
                    # Update metrics
                    response_time = (datetime.utcnow() - start_time).total_seconds()
                    self._update_success_metrics(response_time, processed_count)
                    
                    logger.debug(f"{self.config.source_id}: Processed {processed_count} items")
                else:
                    self._update_failure_metrics("No data received")
                
                # Rate limiting
                await asyncio.sleep(max(60 / self.config.rate_limit_per_minute, 1))
                
            except Exception as e:
                self._update_failure_metrics(str(e))
                logger.error(f"Error in {self.config.source_id} ingestion: {e}")
                await asyncio.sleep(interval_seconds)
    
    @abstractmethod
    async def _fetch_data(self) -> Optional[List[Dict[str, Any]]]:
        """Fetch raw data from the source"""
        pass
    
    async def _process_and_publish_data(self, raw_data: List[Dict[str, Any]]) -> int:
        """Process and publish data with validation and normalization"""
        processed_count = 0
        
        for item in raw_data:
            try:
                # Validate data
                is_valid, quality, issues = self._validate_data(item)
                
                if not is_valid and quality == DataQuality.CORRUPTED:
                    logger.warning(f"Skipping corrupted data from {self.config.source_id}: {issues}")
                    continue
                
                # Normalize data
                normalized_item = self._normalize_data(item)
                normalized_item['data_quality'] = quality.value
                normalized_item['validation_issues'] = issues
                
                # Publish to message broker
                await self.broker.publish_message(
                    self._get_topic_name(),
                    normalized_item
                )
                
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing item from {self.config.source_id}: {e}")
        
        return processed_count
    
    def _validate_data(self, data: Dict[str, Any]) -> tuple[bool, DataQuality, List[str]]:
        """Validate data based on source type"""
        if self.config.source_type == DataSourceType.MARKET_DATA:
            return self.validator.validate_market_data(data)
        elif self.config.source_type == DataSourceType.NEWS:
            return self.validator.validate_news_data(data)
        else:
            return True, DataQuality.HIGH, []
    
    def _normalize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize data based on source type"""
        if self.config.source_type == DataSourceType.MARKET_DATA:
            return self.normalizer.normalize_market_data(data, self.config.source_id)
        elif self.config.source_type == DataSourceType.NEWS:
            return self.normalizer.normalize_news_data(data, self.config.source_id)
        else:
            return {**data, 'source': self.config.source_id, 'data_type': self.config.source_type.value}
    
    def _get_topic_name(self) -> str:
        """Get appropriate topic name for publishing"""
        topic_mapping = {
            DataSourceType.MARKET_DATA: "real_time_market_data",
            DataSourceType.NEWS: "global_news",
            DataSourceType.FUNDAMENTAL: "fundamental_data",
            DataSourceType.ECONOMIC_CALENDAR: "economic_events",
            DataSourceType.BROKER_ACCOUNT: "broker_account_data",
            DataSourceType.IOT_SENSORY: "iot_sensory_data",
            DataSourceType.SOCIAL_SENTIMENT: "social_sentiment",
            DataSourceType.ALTERNATIVE_DATA: "alternative_data"
        }
        return topic_mapping.get(self.config.source_type, "general_data")
    
    def _update_success_metrics(self, response_time: float, processed_count: int):
        """Update success metrics"""
        self.metrics.total_requests += 1
        self.metrics.successful_requests += 1
        self.metrics.consecutive_failures = 0
        self.metrics.last_success = datetime.utcnow()
        
        # Update average response time
        if self.metrics.avg_response_time == 0:
            self.metrics.avg_response_time = response_time
        else:
            self.metrics.avg_response_time = (
                self.metrics.avg_response_time * 0.9 + response_time * 0.1
            )
        
        # Update data quality score based on processed count
        if processed_count > 0:
            self.metrics.data_quality_score = min(
                self.metrics.data_quality_score * 1.01, 1.0
            )
    
    def _update_failure_metrics(self, error_message: str):
        """Update failure metrics"""
        self.metrics.total_requests += 1
        self.metrics.failed_requests += 1
        self.metrics.consecutive_failures += 1
        self.metrics.last_failure = datetime.utcnow()
        
        # Check for rate limiting
        if "rate limit" in error_message.lower() or "429" in error_message:
            self.metrics.rate_limit_hits += 1
        
        # Decrease data quality score
        self.metrics.data_quality_score = max(
            self.metrics.data_quality_score * 0.95, 0.1
        )
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status and metrics"""
        success_rate = (
            self.metrics.successful_requests / max(self.metrics.total_requests, 1)
        )
        
        health_score = (
            success_rate * 0.4 +
            self.metrics.data_quality_score * 0.3 +
            (1.0 if self.metrics.consecutive_failures < 5 else 0.0) * 0.3
        )
        
        status = "healthy" if health_score > 0.8 else "degraded" if health_score > 0.5 else "unhealthy"
        
        return {
            "source_id": self.config.source_id,
            "status": status,
            "health_score": round(health_score, 2),
            "success_rate": round(success_rate, 2),
            "consecutive_failures": self.metrics.consecutive_failures,
            "avg_response_time": round(self.metrics.avg_response_time, 2),
            "data_quality_score": round(self.metrics.data_quality_score, 2),
            "rate_limit_hits": self.metrics.rate_limit_hits,
            "last_success": self.metrics.last_success.isoformat() if self.metrics.last_success else None,
            "last_failure": self.metrics.last_failure.isoformat() if self.metrics.last_failure else None
        }