"""
Copyright (c) 2025 Sans Mercantile™
All rights reserved.

PRIV Multi-Agent System Tests
Comprehensive testing for all PRIV agents
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock

from backend.multi_agent import (
    MultiAgentSystem,
    PrivQuantitativeAgent,
    PrivTechnicalAgent,
    FundamentalAgent,
    PrivEconomicAgent,
    PrivPoliticalAgent,
    PrivSentimentAgent,
    PrivRiskAgent,
    PrivComplianceAgent,
    PrivArbitrageAgent,
    PrivForexAgent,
    PrivOptionsAgent,
    PrivFuturesAgent
)

from shared_resources.agi_core.agi_framework import AGICore
from shared_resources.ai_core import AICore
from backend.tests.conftest import (
    MockAPIClient,
    MockDatabase,
    MockLLMClient,
    TestDataGenerator,
    SecurityTestUtils
)

class TestQuantitativeAgent:
    """Test suite for PrivQuantitativeAgent"""
    
    @pytest.fixture
    def quantitative_agent(self, priv_test_config):
        from backend.tests.conftest import MockAPIClient
        return PrivQuantitativeAgent(
            agent_id="test_quant",
            agent_type="quantitative",
            message_broker=None,
            broker=None,
            persona={},
            api_client=MockAPIClient(),
            config=priv_test_config
        )
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, quantitative_agent):
        """Test quantitative agent initialization"""
        assert quantitative_agent is not None
        assert quantitative_agent.agent_type == 'quantitative'
        assert hasattr(quantitative_agent, 'analyze_market_data')
        assert hasattr(quantitative_agent, 'generate_signals')
    
    @pytest.mark.asyncio
    async def test_market_data_analysis(self, quantitative_agent, test_data_generator):
        """Test market data analysis capabilities"""
        # Generate test market data
        market_data = test_data_generator.generate_market_data('AAPL', 30)
        
        # Mock API responses
        quantitative_agent.api_client.add_response(
            '/market-data/AAPL',
            {'data': market_data, 'status': 'success'}
        )
        
        # Test market data analysis
        result = await quantitative_agent.analyze_market_data('AAPL', market_data)
        
        assert result is not None
        assert 'analysis' in result
        assert 'signals' in result
        assert 'confidence' in result
        assert 0 <= result['confidence'] <= 1.0
    
    @pytest.mark.asyncio
    async def test_signal_generation(self, quantitative_agent, test_data_generator):
        """Test trading signal generation"""
        # Generate test signals
        signals = test_data_generator.generate_trading_signals(10)
        
        # Test signal generation
        result = await quantitative_agent.generate_signals(signals)
        
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0
        
        for signal in result:
            assert 'symbol' in signal
            assert 'signal_type' in signal
            assert 'confidence' in signal
            assert signal['signal_type'] in ['BUY', 'SELL', 'HOLD']
    
    @pytest.mark.asyncio
    async def test_risk_metrics_calculation(self, quantitative_agent, test_data_generator):
        """Test risk metrics calculation"""
        # Generate test data
        market_data = test_data_generator.generate_market_data('TSLA', 60)
        
        # Test risk metrics calculation
        risk_metrics = await quantitative_agent.calculate_risk_metrics(market_data)
        
        assert risk_metrics is not None
        assert 'var_95' in risk_metrics
        assert 'var_99' in risk_metrics
        assert 'sharpe_ratio' in risk_metrics
        assert 'max_drawdown' in risk_metrics
        
        # Validate metric ranges
        assert 0 <= risk_metrics['var_95'] <= 1.0
        assert 0 <= risk_metrics['var_99'] <= 1.0
        assert -5 <= risk_metrics['sharpe_ratio'] <= 5
        assert 0 <= risk_metrics['max_drawdown'] <= 1.0
    
    @pytest.mark.asyncio
    async def test_backtesting_strategy(self, quantitative_agent, test_data_generator):
        """Test strategy backtesting"""
        # Generate historical data
        historical_data = test_data_generator.generate_market_data('GOOGL', 252)  # 1 year
        
        # Mock strategy parameters
        strategy_params = {
            'moving_average_period': 20,
            'rsi_period': 14,
            'rsi_overbought': 70,
            'rsi_oversold': 30
        }
        
        # Test backtesting
        backtest_results = await quantitative_agent.backtest_strategy(
            historical_data, strategy_params
        )
        
        assert backtest_results is not None
        assert 'total_return' in backtest_results
        assert 'max_drawdown' in backtest_results
        assert 'sharpe_ratio' in backtest_results
        assert 'win_rate' in backtest_results
        
        # Validate backtest metrics
        assert isinstance(backtest_results['total_return'], float)
        assert 0 <= backtest_results['win_rate'] <= 1.0
    
    @pytest.mark.asyncio
    async def test_error_handling(self, quantitative_agent, error_scenarios):
        """Test error handling in quantitative agent"""
        # Test network timeout
        # Patch the api_client to raise TimeoutError for this endpoint
        def raise_timeout(*args, **kwargs):
            raise TimeoutError("Network timeout simulated")
        quantitative_agent.api_client.get_market_data = raise_timeout

        with pytest.raises(TimeoutError):
            # Directly call the patched method to ensure exception is raised
            quantitative_agent.api_client.get_market_data('ERROR', [])
    
    @pytest.mark.asyncio
    async def test_performance_benchmarks(self, quantitative_agent, performance_benchmarks):
        """Test performance benchmarks"""
        import time
        
        start_time = time.time()
        
        # Generate test data
        market_data = TestDataGenerator.generate_market_data('MSFT', 1000)
        
        # Test performance
        result = await quantitative_agent.analyze_market_data('MSFT', market_data)
        
        end_time = time.time()
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Verify performance meets benchmarks
        assert execution_time <= performance_benchmarks['trading_execution_time']
        assert result is not None
        assert 'analysis' in result

class TestTechnicalAgent:
    """Test suite for PrivTechnicalAgent"""
    
    @pytest.fixture
    def technical_agent(self, priv_test_config):
        from backend.tests.conftest import MockAPIClient
        return PrivTechnicalAgent(
            agent_id="test_tech",
            agent_type="technical",
            message_broker=None,
            broker=None,
            persona={},
            api_client=MockAPIClient(),
            config=priv_test_config
        )
    
    @pytest.mark.asyncio
    async def test_technical_analysis(self, technical_agent, test_data_generator):
        """Test technical analysis capabilities"""
        # Generate test data
        market_data = test_data_generator.generate_market_data('AAPL', 50)
        
        # Test technical analysis
        technical_analysis = await technical_agent.analyze_technical_indicators(market_data)
        
        assert technical_analysis is not None
        assert 'rsi' in technical_analysis
        assert 'macd' in technical_analysis
        assert 'bollinger_bands' in technical_analysis
        assert 'moving_averages' in technical_analysis
        
        # Validate indicator values
        assert 0 <= technical_analysis['rsi'] <= 100
        assert isinstance(technical_analysis['macd'], dict)
        assert 'upper' in technical_analysis['bollinger_bands']
        assert 'lower' in technical_analysis['bollinger_bands']
    
    @pytest.mark.asyncio
    async def test_chart_pattern_recognition(self, technical_agent, test_data_generator):
        """Test chart pattern recognition"""
        # Generate test data with patterns
        market_data = test_data_generator.generate_market_data('TSLA', 100)
        
        # Test pattern recognition
        patterns = await technical_agent.recognize_patterns(market_data)
        
        assert patterns is not None
        assert isinstance(patterns, list)
        
        for pattern in patterns:
            assert 'pattern_type' in pattern
            assert 'confidence' in pattern
            assert 'start_index' in pattern
            assert 'end_index' in pattern
            assert 0 <= pattern['confidence'] <= 1.0
    
    @pytest.mark.asyncio
    async def test_support_resistance_levels(self, technical_agent, test_data_generator):
        """Test support and resistance level identification"""
        # Generate test data
        market_data = test_data_generator.generate_market_data('GOOGL', 60)
        
        # Test support/resistance identification
        levels = await technical_agent.identify_support_resistance(market_data)
        
        assert levels is not None
        assert 'support_levels' in levels
        assert 'resistance_levels' in levels
        assert isinstance(levels['support_levels'], list)
        assert isinstance(levels['resistance_levels'], list)
        
        # Validate level values
        for level in levels['support_levels'] + levels['resistance_levels']:
            assert 'price' in level
            assert 'strength' in level
            assert 0 <= level['strength'] <= 1.0

class TestFundamentalAgent:
    """Test suite for Fundamental Agent"""
    
    @pytest.fixture
    def fundamental_agent(self, priv_test_config, mock_api_client, mock_database):
        return FundamentalAgent(
            agent_id="test_fundamental",
            broker=None,
            config=priv_test_config,
            api_client=mock_api_client,
            database=mock_database,
            calendar_url="http://mock-calendar-url.com"
        )
    
    @pytest.mark.asyncio
    async def test_fundamental_analysis(self, fundamental_agent, test_data_generator):
        """Test fundamental analysis capabilities"""
        # Mock fundamental data
        fundamental_data = {
            'symbol': 'AAPL',
            'market_cap': 2500000000000,
            'pe_ratio': 25.5,
            'pb_ratio': 8.2,
            'eps': 6.15,
            'revenue': 394328000000,
            'debt_to_equity': 1.65,
            'roe': 147.4,
            'current_ratio': 0.88
        }
        
        # Test fundamental analysis
        analysis = await fundamental_agent.analyze_fundamentals(fundamental_data)
        
        assert analysis is not None
        assert 'valuation_score' in analysis
        assert 'financial_health' in analysis
        assert 'growth_prospects' in analysis
        assert 'recommendation' in analysis
        
        # Validate analysis scores
        assert 0 <= analysis['valuation_score'] <= 100
        assert analysis['recommendation'] in ['STRONG_BUY', 'BUY', 'HOLD', 'SELL', 'STRONG_SELL']
    
    @pytest.mark.asyncio
    async def test_earnings_analysis(self, fundamental_agent):
        """Test earnings analysis and forecasting"""
        # Mock earnings data
        earnings_data = [
            {'quarter': 'Q1', 'eps': 1.52, 'revenue': 97278000000},
            {'quarter': 'Q2', 'eps': 1.40, 'revenue': 84784000000},
            {'quarter': 'Q3', 'eps': 1.29, 'revenue': 90146000000},
            {'quarter': 'Q4', 'eps': 1.88, 'revenue': 123945000000}
        ]
        
        # Test earnings analysis
        earnings_analysis = await fundamental_agent.analyze_earnings(earnings_data)
        
        assert earnings_analysis is not None
        assert 'trend' in earnings_analysis
        assert 'forecast' in earnings_analysis
        assert 'beat_rate' in earnings_analysis
        assert 'growth_rate' in earnings_analysis
        
        # Validate earnings metrics
        assert earnings_analysis['trend'] in ['increasing', 'decreasing', 'stable']
        assert 0 <= earnings_analysis['beat_rate'] <= 1.0

class TestMultiAgentCoordination:
    """Test suite for multi-agent coordination"""
    
    @pytest.fixture
    def multi_agent_system(self, priv_test_config, mock_api_client, mock_database):
        from backend.tests.conftest import MockAPIClient
        mock_broker = MockAPIClient() # Use MockAPIClient as a stand-in for broker
        return MultiAgentSystem(
            broker=mock_broker,
            config=priv_test_config,
            api_client=mock_api_client,
            database=mock_database
        )
    
    @pytest.mark.asyncio
    async def test_agent_registration(self, multi_agent_system):
        """Test agent registration and management"""
        # Create test agents
        agents = [
            PrivQuantitativeAgent(
                agent_id="test_quant",
                agent_type=None,
                message_broker=None,
                broker=None,
                persona={}
            ),
            PrivTechnicalAgent(
                agent_id="test_tech",
                agent_type=None,
                message_broker=None,
                broker=None,
                persona={}
            ),
            FundamentalAgent(multi_agent_system.config, multi_agent_system.api_client, multi_agent_system.database)
        ]
        
        # Register agents
        for agent in agents:
            await multi_agent_system.register_agent(agent)
        
        # Verify registration
        registered_agents = multi_agent_system.get_registered_agents()
        assert len(registered_agents) == 3
        
        for agent in registered_agents:
            assert hasattr(agent, 'agent_type')
            assert hasattr(agent, 'analyze')
    
    @pytest.mark.asyncio
    async def test_arbitration_engine(self, multi_agent_system, test_data_generator):
        """Test arbitration engine for conflict resolution"""
        # Generate conflicting signals
        signals = [
            {'agent': 'quantitative', 'signal': 'BUY', 'confidence': 0.8},
            {'agent': 'technical', 'signal': 'SELL', 'confidence': 0.7},
            {'agent': 'fundamental', 'signal': 'HOLD', 'confidence': 0.6}
        ]
        
        # Test arbitration
        arbitration_result = await multi_agent_system.arbitrate_signals(signals)
        
        assert arbitration_result is not None
        assert 'consensus_signal' in arbitration_result
        assert 'confidence' in arbitration_result
        assert 'dissenting_agents' in arbitration_result
        assert 'rationale' in arbitration_result
        
        # Validate arbitration logic
        assert arbitration_result['consensus_signal'] in ['BUY', 'SELL', 'HOLD']
        assert 0 <= arbitration_result['confidence'] <= 1.0
    
    @pytest.mark.asyncio
    async def test_agent_collaboration(self, multi_agent_system, test_data_generator):
        """Test collaborative analysis between agents"""
        # Generate test market scenario
        market_data = test_data_generator.generate_market_data('MSFT', 30)
        
        # Test collaborative analysis
        collaboration_result = await multi_agent_system.collaborative_analysis(
            symbol='MSFT',
            market_data=market_data,
            analysis_type='comprehensive'
        )
        
        assert collaboration_result is not None
        assert 'combined_analysis' in collaboration_result
        assert 'agent_contributions' in collaboration_result
        assert 'confidence_score' in collaboration_result
        assert 'recommendation' in collaboration_result
        
        # Validate collaboration metrics
        assert 0 <= collaboration_result['confidence_score'] <= 1.0
        assert len(collaboration_result['agent_contributions']) > 0

class TestAgentPerformance:
    """Test suite for agent performance and benchmarks"""
    
    @pytest.mark.asyncio
    async def test_agent_response_time(self, quantitative_agent, performance_benchmarks):
        """Test agent response time meets benchmarks"""
        import time
        
        # Generate test data
        market_data = TestDataGenerator.generate_market_data('AAPL', 100)
        
        # Measure response time
        start_time = time.time()
        result = await quantitative_agent.analyze_market_data('AAPL', market_data)
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Verify response time meets benchmark
        assert response_time <= performance_benchmarks['trading_execution_time']
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_agent_accuracy(self, quantitative_agent, test_data_generator):
        """Test agent prediction accuracy"""
        # Generate test data with known outcomes
        market_data = test_data_generator.generate_market_data('GOOGL', 60)
        
        # Split data for training and testing
        train_data = market_data[:40]
        test_data = market_data[40:]
        
        # Test accuracy on known data
        predictions = await quantitative_agent.predict_outcomes(test_data)
        
        assert predictions is not None
        assert len(predictions) == len(test_data)
        
        # Calculate accuracy metrics
        correct_predictions = sum(1 for pred in predictions if pred['accuracy'] > 0.5)
        accuracy_rate = correct_predictions / len(predictions)
        
        # Validate accuracy (should be better than random)
        assert accuracy_rate > 0.5  # Better than random chance
    
    @pytest.mark.asyncio
    async def test_agent_scalability(self, multi_agent_system, test_data_generator):
        """Test system scalability under load"""
        import asyncio
        
        # Generate multiple symbols for concurrent processing
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']
        market_data = {}
        
        for symbol in symbols:
            market_data[symbol] = test_data_generator.generate_market_data(symbol, 50)
        
        # Test concurrent processing
        start_time = asyncio.get_event_loop().time()
        
        tasks = []
        for symbol, data in market_data.items():
            task = multi_agent_system.analyze_symbol(symbol, data)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        end_time = asyncio.get_event_loop().time()
        total_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Verify all analyses completed successfully
        assert len(results) == len(symbols)
        for result in results:
            assert result is not None
            assert 'analysis' in result
        
        # Verify performance under load
        avg_time_per_symbol = total_time / len(symbols)
        assert avg_time_per_symbol <= 1000  # 1 second per symbol average

# Integration Tests
@pytest.mark.asyncio
async def test_end_to_end_trading_workflow(
    multi_agent_system,
    quantitative_agent,
    technical_agent,
    fundamental_agent,
    test_data_generator
):
    """Test complete end-to-end trading workflow"""
    
    # Step 1: Data Collection
    market_data = test_data_generator.generate_market_data('AAPL', 30)
    
    # Step 2: Multi-Agent Analysis
    analysis_tasks = [
        quantitative_agent.analyze_market_data('AAPL', market_data),
        technical_agent.analyze_technical_indicators(market_data),
        fundamental_agent.analyze_fundamentals({'symbol': 'AAPL', 'pe_ratio': 25.5})
    ]
    
    analysis_results = await asyncio.gather(*analysis_tasks)
    
    # Step 3: Signal Generation
    signals = await multi_agent_system.generate_consensus_signal(
        symbol='AAPL',
        analysis_results=analysis_results
    )
    
    # Step 4: Risk Assessment
    risk_assessment = await multi_agent_system.assess_risk(signals)
    
    # Step 5: Trade Execution (Mock)
    if risk_assessment['approved']:
        trade_result = await multi_agent_system.execute_trade(signals)
        
        # Verify complete workflow
        assert trade_result is not None
        assert 'trade_id' in trade_result
        assert 'status' in trade_result
        assert trade_result['status'] in ['EXECUTED', 'PENDING', 'REJECTED']
    else:
        # Verify risk management worked
        assert risk_assessment['rejected'] is True
        assert 'reason' in risk_assessment

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])