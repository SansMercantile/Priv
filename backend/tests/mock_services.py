"""
Copyright (c) 2025 Sans Mercantile™
All rights reserved.

Mock Services for PRIV Testing
Comprehensive mock implementations for all external APIs
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

class MockResponseStatus(Enum):
    """Mock response status codes"""
    SUCCESS = 200
    CREATED = 201
    ACCEPTED = 202
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    SERVER_ERROR = 500

@dataclass
class MockAPIResponse:
    """Standardized mock API response"""
    status_code: int
    data: Dict[str, Any]
    headers: Dict[str, str] = None
    latency_ms: int = 50  # Simulate network latency

    SUCCESS = MockResponseStatus.SUCCESS
    SUCCESS_CODE = MockResponseStatus.SUCCESS
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {
                'Content-Type': 'application/json',
                'X-Request-ID': f'mock-{random.randint(100000, 999999)}'
            }

class MockMarketDataAPI:
    """Mock market data API for testing"""
    
    def __init__(self):
        self.call_count = 0
        self.historical_data = {}
        self.real_time_data = {}
        self.symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'META', 'NVDA', 'NFLX']
        
        # Initialize with realistic mock data
        self._initialize_mock_data()
    
    def _initialize_mock_data(self):
        """Initialize with realistic market data"""
        base_date = datetime.now() - timedelta(days=365)
        
        for symbol in self.symbols:
            # Generate historical data
            historical = []
            base_price = random.uniform(50, 500)
            
            for i in range(365):
                # Simulate realistic price movements
                volatility = random.uniform(-0.05, 0.05)
                base_price *= (1 + volatility)
                
                # Ensure price stays positive
                base_price = max(base_price, 1.0)
                
                historical.append({
                    'date': (base_date + timedelta(days=i)).isoformat(),
                    'open': round(base_price * random.uniform(0.98, 1.02), 2),
                    'high': round(base_price * random.uniform(1.0, 1.05), 2),
                    'low': round(base_price * random.uniform(0.95, 1.0), 2),
                    'close': round(base_price, 2),
                    'volume': random.randint(1000000, 50000000),
                    'adjusted_close': round(base_price, 2)
                })
            
            self.historical_data[symbol] = historical
            
            # Generate real-time data
            current_price = historical[-1]['close'] if historical else 100.0
            self.real_time_data[symbol] = {
                'symbol': symbol,
                'price': current_price,
                'change': round(random.uniform(-5, 5), 2),
                'change_percent': round(random.uniform(-5, 5), 2),
                'volume': random.randint(1000000, 10000000),
                'timestamp': datetime.now().isoformat(),
                'bid': round(current_price - 0.01, 2),
                'ask': round(current_price + 0.01, 2),
                'spread': 0.02
            }
    
    async def get_historical_data(self, symbol: str, period: str = '1y', interval: str = '1d') -> MockAPIResponse:
        """Get historical market data"""
        self.call_count += 1
        
        # Simulate network latency
        await asyncio.sleep(random.uniform(0.01, 0.05))
        
        if symbol not in self.historical_data:
                return MockAPIResponse(
                    status_code=MockResponseStatus.NOT_FOUND,
                    data={'error': f'Symbol {symbol} not found'}
                )
        
        data = self.historical_data[symbol]
        
        # Filter by period if specified
        if period != '1y':
            days_map = {'1d': 1, '5d': 5, '1mo': 30, '3mo': 90, '6mo': 180}
            days = days_map.get(period, 365)
            data = data[-days:] if len(data) > days else data
        
        return MockAPIResponse(
            status_code=200,
            data={
                'symbol': symbol,
                'period': period,
                'interval': interval,
                'data_points': len(data),
                'data': data
            }
        )
    
    async def get_real_time_data(self, symbol: str) -> MockAPIResponse:
        """Get real-time market data"""
        self.call_count += 1
        
        # Simulate network latency
        await asyncio.sleep(random.uniform(0.005, 0.02))
        
        if symbol not in self.real_time_data:
                return MockAPIResponse(
                    status_code=MockResponseStatus.NOT_FOUND,
                    data={'error': f'Symbol {symbol} not found'}
                )
        
        # Update price with small random change
        current_data = self.real_time_data[symbol].copy()
        price_change = random.uniform(-0.5, 0.5)
        current_data['price'] = round(current_data['price'] + price_change, 2)
        current_data['change'] = round(price_change, 2)
        current_data['change_percent'] = round((price_change / (current_data['price'] - price_change)) * 100, 2)
        current_data['timestamp'] = datetime.now().isoformat()
        
        return MockAPIResponse(
            status_code=200,
            data=current_data
        )
    
    async def get_options_chain(self, symbol: str, expiration_date: str = None) -> MockAPIResponse:
        """Get options chain data"""
        self.call_count += 1
        
        # Simulate options chain with realistic strikes
        current_price = self.real_time_data.get(symbol, {}).get('price', 100.0)
        
        strikes = []
        base_strike = round(current_price / 5) * 5  # Round to nearest $5
        
        for i in range(-10, 11):  # 21 strikes around current price
            strike = base_strike + (i * 5)
            
            # Generate call and put options
            call_option = {
                'strike': strike,
                'type': 'CALL',
                'bid': round(random.uniform(0.5, 50), 2),
                'ask': round(random.uniform(0.5, 50), 2),
                'volume': random.randint(100, 10000),
                'open_interest': random.randint(1000, 50000),
                'implied_volatility': round(random.uniform(0.1, 0.8), 4)
            }
            
            put_option = {
                'strike': strike,
                'type': 'PUT',
                'bid': round(random.uniform(0.5, 50), 2),
                'ask': round(random.uniform(0.5, 50), 2),
                'volume': random.randint(100, 10000),
                'open_interest': random.randint(1000, 50000),
                'implied_volatility': round(random.uniform(0.1, 0.8), 4)
            }
            
            strikes.extend([call_option, put_option])
        
        return MockAPIResponse(
            status_code=200,
            data={
                'symbol': symbol,
                'underlying_price': current_price,
                'expiration_date': expiration_date or (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
                'strikes': strikes,
                'total_options': len(strikes)
            }
        )

class MockNewsAPI:
    """Mock news API for sentiment analysis testing"""
    
    def __init__(self):
        self.call_count = 0
        self.news_articles = {}
        self.sentiment_scores = {}
        
        # Initialize with realistic mock news
        self._initialize_mock_news()
    
    def _initialize_mock_news(self):
        """Initialize with realistic news articles"""
        companies = {
            'AAPL': 'Apple Inc.',
            'GOOGL': 'Alphabet Inc.',
            'MSFT': 'Microsoft Corporation',
            'TSLA': 'Tesla Inc.',
            'AMZN': 'Amazon.com Inc.'
        }
        
        news_templates = [
            {
                'title': '{company} Reports Strong Q3 Earnings, Beats Expectations',
                'content': '{company} reported quarterly earnings that exceeded analyst expectations...',
                'sentiment': 0.8
            },
            {
                'title': '{company} Announces New Product Launch, Shares Rise',
                'content': '{company} unveiled its latest product innovation today...',
                'sentiment': 0.7
            },
            {
                'title': '{company} Faces Regulatory Challenges, Stock Declines',
                'content': 'Regulatory concerns have emerged regarding {company}...',
                'sentiment': -0.6
            },
            {
                'title': '{company} Partnership Deal Boosts Market Confidence',
                'content': 'A strategic partnership announcement from {company}...',
                'sentiment': 0.6
            },
            {
                'title': '{company} Market Analysis: Mixed Signals Ahead',
                'content': 'Market analysts provide mixed outlook for {company}...',
                'sentiment': 0.1
            }
        ]
        
        for symbol, company in companies.items():
            articles = []
            
            for template in news_templates:
                article = {
                    'title': template['title'].format(company=company),
                    'content': template['content'].format(company=company),
                    'published_at': (datetime.now() - timedelta(hours=random.randint(1, 72))).isoformat(),
                    'source': random.choice(['Reuters', 'Bloomberg', 'CNBC', 'MarketWatch']),
                    'url': f'https://example.com/news/{symbol}/{random.randint(1000, 9999)}',
                    'sentiment_score': template['sentiment'],
                    'confidence': round(random.uniform(0.7, 0.95), 2)
                }
                articles.append(article)
            
            self.news_articles[symbol] = articles
            self.sentiment_scores[symbol] = sum(article['sentiment_score'] for article in articles) / len(articles)
    
    async def get_news(self, symbol: str, limit: int = 10) -> MockAPIResponse:
        """Get news articles for a symbol"""
        self.call_count += 1
        
        if symbol not in self.news_articles:
                return MockAPIResponse(
                    status_code=MockResponseStatus.NOT_FOUND,
                    data={'error': f'No news found for {symbol}'}
                )
        
        articles = self.news_articles[symbol][:limit]
        
        return MockAPIResponse(
            status_code=200,
            data={
                'symbol': symbol,
                'articles': articles,
                'sentiment_summary': {
                    'average_sentiment': self.sentiment_scores[symbol],
                    'positive_count': len([a for a in articles if a['sentiment_score'] > 0]),
                    'negative_count': len([a for a in articles if a['sentiment_score'] < 0]),
                    'neutral_count': len([a for a in articles if a['sentiment_score'] == 0])
                }
            }
        )
    
    async def get_sentiment_analysis(self, text: str) -> MockAPIResponse:
        """Get sentiment analysis for text"""
        self.call_count += 1
        
        # Simple sentiment analysis based on keywords
        positive_words = ['good', 'great', 'excellent', 'strong', 'growth', 'profit', 'success']
        negative_words = ['bad', 'poor', 'weak', 'loss', 'decline', 'problem', 'issue']
        
        positive_count = sum(1 for word in positive_words if word in text.lower())
        negative_count = sum(1 for word in negative_words if word in text.lower())
        
        if positive_count > negative_count:
            sentiment = 0.7
        elif negative_count > positive_count:
            sentiment = -0.6
        else:
            sentiment = 0.1
        
        return MockAPIResponse(
            status_code=200,
            data={
                'text': text[:100],  # Truncate for response
                'sentiment_score': sentiment,
                'confidence': round(random.uniform(0.8, 0.95), 2),
                'positive_keywords': positive_count,
                'negative_keywords': negative_count
            }
        )

class MockEconomicDataAPI:
    """Mock economic data API for macro analysis"""
    
    def __init__(self):
        self.call_count = 0
        self.economic_indicators = {}
        self._initialize_economic_data()
    
    def _initialize_economic_data(self):
        """Initialize with realistic economic data"""
        base_date = datetime.now() - timedelta(days=365)
        
        # GDP data
        gdp_data = []
        base_gdp = 21000.0  # Base GDP in billions
        
        for i in range(12):  # 12 months of data
            growth_rate = random.uniform(-0.02, 0.05)  # -2% to 5% growth
            base_gdp *= (1 + growth_rate / 12)  # Monthly compounding
            
            gdp_data.append({
                'date': (base_date + timedelta(days=i*30)).isoformat(),
                'gdp_billions': round(base_gdp, 2),
                'growth_rate': round(growth_rate, 4),
                'quarter': f'Q{(i % 4) + 1}'
            })
        
        # Inflation data
        inflation_data = []
        for i in range(365):
            inflation_rate = random.uniform(0.01, 0.04)  # 1% to 4% inflation
            inflation_data.append({
                'date': (base_date + timedelta(days=i)).isoformat(),
                'inflation_rate': round(inflation_rate, 4),
                'cpi_index': round(100 * (1 + inflation_rate), 2)
            })
        
        # Interest rates
        interest_rates = {
            'federal_funds_rate': round(random.uniform(0.25, 5.0), 2),
            'treasury_10_year': round(random.uniform(1.0, 5.0), 2),
            'treasury_2_year': round(random.uniform(0.5, 4.5), 2),
            'prime_rate': round(random.uniform(3.0, 8.0), 2)
        }
        
        self.economic_indicators = {
            'gdp': gdp_data,
            'inflation': inflation_data[-30:],  # Last 30 days
            'interest_rates': interest_rates,
            'unemployment_rate': round(random.uniform(3.0, 8.0), 2),
            'consumer_confidence': round(random.uniform(90, 120), 1)
        }
    
    async def get_gdp_data(self, period: str = '1y') -> MockAPIResponse:
        """Get GDP data"""
        self.call_count += 1
        
        data = self.economic_indicators['gdp']
        
        if period != '1y':
            months_map = {'1mo': 1, '3mo': 3, '6mo': 6}
            months = months_map.get(period, 12)
            data = data[-months:] if len(data) > months else data
        
        return MockAPIResponse(
            status_code=200,
            data={
                'indicator': 'GDP',
                'period': period,
                'data_points': len(data),
                'data': data,
                'latest_value': data[-1]['gdp_billions'] if data else None
            }
        )
    
    async def get_interest_rates(self) -> MockAPIResponse:
        """Get current interest rates"""
        self.call_count += 1
        
        return MockAPIResponse(
            status_code=200,
            data={
                'rates': self.economic_indicators['interest_rates'],
                'last_updated': datetime.now().isoformat(),
                'source': 'Federal Reserve Economic Data (FRED)'
            }
        )

class MockComplianceAPI:
    """Mock compliance API for regulatory testing"""
    
    def __init__(self):
        self.call_count = 0
        self.regulatory_rules = {}
        self.compliance_status = {}
        self._initialize_compliance_data()
    
    def _initialize_compliance_data(self):
        """Initialize with regulatory compliance data"""
        self.regulatory_rules = {
            'SEC': {
                'pattern_day_trader_rule': True,
                'free_riding_rule': True,
                'good_faith_violation_rule': True,
                'margin_requirements': {
                    'initial': 0.5,
                    'maintenance': 0.25
                }
            },
            'FINRA': {
                'best_execution_rule': True,
                'suitability_rule': True,
                'fair_pricing_rule': True
            },
            'MiFID_II': {
                'transparency_requirements': True,
                'best_execution_requirements': True,
                'client_categorization': True
            }
        }
        
        self.compliance_status = {
            'overall_status': 'COMPLIANT',
            'violations': [],
            'warnings': [],
            'last_audit': datetime.now().isoformat()
        }
    
    async def check_trade_compliance(self, trade_data: Dict[str, Any]) -> MockAPIResponse:
        """Check if trade complies with regulations"""
        self.call_count += 1
        
        # Simulate compliance checking
        violations = []
        warnings = []
        
        # Check for pattern day trading
        if trade_data.get('account_value', 0) < 25000 and trade_data.get('day_trades', 0) >= 4:
            violations.append({
                'rule': 'pattern_day_trader',
                'severity': 'high',
                'description': 'Account flagged as pattern day trader'
            })
        
        # Check for free riding
        if trade_data.get('unsettled_funds', 0) > 0 and trade_data.get('trade_type') == 'BUY':
            violations.append({
                'rule': 'free_riding',
                'severity': 'medium',
                'description': 'Potential free riding violation'
            })
        
        # Check margin requirements
        if trade_data.get('margin_used', 0) > trade_data.get('margin_available', 0):
            violations.append({
                'rule': 'margin_requirement',
                'severity': 'high',
                'description': 'Insufficient margin for trade'
            })
        
        status = 'COMPLIANT' if not violations else 'NON_COMPLIANT'
        
        return MockAPIResponse(
            status_code=200,
            data={
                'trade_id': trade_data.get('trade_id', 'unknown'),
                'compliance_status': status,
                'violations': violations,
                'warnings': warnings,
                'compliant': not violations,
                'recommendations': [
                    'Review margin requirements',
                    'Consider trade timing',
                    'Verify account status'
                ] if violations else ['Trade compliant with all regulations']
            }
        )
    
    async def generate_compliance_report(self, account_id: str, period: str = '1m') -> MockAPIResponse:
        """Generate compliance report for account"""
        self.call_count += 1
        
        # Simulate compliance report generation
        report_data = {
            'account_id': account_id,
            'period': period,
            'generated_at': datetime.now().isoformat(),
            'regulatory_summary': 'No active alerts',
            'summary': {
                'total_trades': random.randint(100, 1000),
                'compliant_trades': random.randint(90, 1000),
                'violations': random.randint(0, 10),
                'warnings': random.randint(0, 20)
            },
            'detailed_analysis': {
                'trading_patterns': 'Normal trading activity detected',
                'risk_exposure': 'Within acceptable limits',
                'regulatory_compliance': '98% compliance rate'
            },
            'recommendations': [
                'Continue monitoring trading patterns',
                'Review any outstanding warnings',
                'Maintain current risk management practices'
            ]
        }
        
        return MockAPIResponse(
            status_code=200,
            data=report_data
        )

# Unified Mock API Manager
class MockAPIManager:
    """Central manager for all mock APIs"""
    
    def __init__(self):
        self.market_data_api = MockMarketDataAPI()
        self.news_api = MockNewsAPI()
        self.economic_api = MockEconomicDataAPI()
        self.compliance_api = MockComplianceAPI()
        
        self.api_stats = {
            'total_calls': 0,
            'by_api': {
                'market_data': 0,
                'news': 0,
                'economic': 0,
                'compliance': 0
            },
            'response_times': [],
            'error_rates': {
                'market_data': 0.01,  # 1% error rate
                'news': 0.02,         # 2% error rate
                'economic': 0.005,    # 0.5% error rate
                'compliance': 0.001   # 0.1% error rate
            }
        }
    
    async def simulate_network_conditions(self):
        """Simulate various network conditions"""
        # Simulate occasional network issues
        if random.random() < 0.001:  # 0.1% chance of network issue
            await asyncio.sleep(5)  # 5 second delay
            raise TimeoutError("Network timeout simulated")
        
        # Simulate normal network latency
        await asyncio.sleep(random.uniform(0.01, 0.1))
    
    def get_api_stats(self) -> Dict[str, Any]:
        """Get comprehensive API statistics"""
        total_calls = (
            self.market_data_api.call_count +
            self.news_api.call_count +
            self.economic_api.call_count +
            self.compliance_api.call_count
        )
        
        return {
            'total_api_calls': total_calls,
            'by_service': {
                'market_data': self.market_data_api.call_count,
                'news': self.news_api.call_count,
                'economic': self.economic_api.call_count,
                'compliance': self.compliance_api.call_count
            },
            'average_response_time': sum(self.api_stats['response_times']) / len(self.api_stats['response_times']) if self.api_stats['response_times'] else 0,
            'error_rates': self.api_stats['error_rates'],
            'uptime_percentage': 99.9  # Simulated uptime
        }
    
    def reset_stats(self):
        """Reset all API statistics"""
        self.market_data_api.call_count = 0
        self.news_api.call_count = 0
        self.economic_api.call_count = 0
        self.compliance_api.call_count = 0
        self.api_stats['total_calls'] = 0
        self.api_stats['response_times'] = []

# Usage Example
async def example_usage():
    """Example usage of mock APIs"""
    mock_manager = MockAPIManager()
    
    # Get market data
    market_response = await mock_manager.market_data_api.get_real_time_data('AAPL')
    print(f"AAPL Price: ${market_response.data['price']}")
    
    # Get news
    news_response = await mock_manager.news_api.get_news('AAPL', limit=3)
    print(f"Latest AAPL News: {news_response.data['articles'][0]['title']}")
    
    # Get API statistics
    stats = mock_manager.get_api_stats()
    print(f"Total API calls: {stats['total_api_calls']}")
    
    return stats

if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())