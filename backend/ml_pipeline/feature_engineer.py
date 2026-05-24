# backend/ml_pipeline/feature_engineer.py

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta
from backend.config import settings
import os
import asyncio
import json
from backend.fundamental_analysis.economic_calendar.defines import ImpactLevel


logger = logging.getLogger(__name__)

class FeatureEngineer:
    def __init__(self):
        logger.info("FeatureEngineer initialized.")
        self.lag_periods = [1, 3, 5, 10]
        self.rolling_periods = [5, 10, 20]

    def generate_features(
        self,
        market_data_df: pd.DataFrame,
        analysis_results_history: Dict[datetime, Dict[str, Any]], # Full historical analysis results by bar timestamp
        economic_events: List[Dict[str, Any]], # List of historical economic events
        news_analysis_results_history: Dict[datetime, Dict[str, Any]], # History of LLM news sentiment/impact results by bar timestamp
        trade_decisions_history: Dict[datetime, Dict[str, Any]], # History of Priv's autonomous trade decisions (e.g., from simulation logs)
        primary_symbol: str = "EURUSD",
        future_lookahead_bars: int = 5,
        price_change_threshold: float = 0.005 # 0.5%
    ) -> pd.DataFrame:
        """
        Generates a comprehensive set of machine learning features from market data,
        historical technical analysis results, economic events, news sentiment,
        and Priv's own past trade decisions/outcomes.

        Args:
            market_data_df (pd.DataFrame): OHLCV data for the primary symbol.
            analysis_results_history (Dict[datetime, Dict[str, Any]]): Historical analysis results from AnalyticsEngine,
                                                                         keyed by bar timestamp.
            economic_events (List[Dict[str, Any]]): List of historical economic events.
            news_analysis_results_history (Dict[datetime, Dict[str, Any]]): Historical LLM news sentiment/impact results,
                                                                               keyed by bar timestamp.
            trade_decisions_history (Dict[datetime, Dict[str, Any]]): Historical records of Priv's autonomous trade decisions,
                                                                       e.g., from simulation logs, keyed by timestamp.
            primary_symbol (str): The symbol for which we are generating features.
            future_lookahead_bars (int): Number of future bars to define target variable.
            price_change_threshold (float): % change for target classification.

        Returns:
            pd.DataFrame: A DataFrame where each row is a time point and columns are features.
                          Includes technical, fundamental, and decision-context features.
        """
        if market_data_df.empty:
            logger.warning("Priv: Market data DataFrame is empty. Cannot generate features.")
            return pd.DataFrame()

        # Ensure market_data_df has a proper DatetimeIndex for merging/lookup
        if not isinstance(market_data_df.index, pd.DatetimeIndex):
            logger.error("Priv: market_data_df must have a DatetimeIndex.")
            return pd.DataFrame()

        features_df = pd.DataFrame(index=market_data_df.index)

        # --- 1. Basic Price Features ---
        features_df['open'] = market_data_df['open']
        features_df['high'] = market_data_df['high']
        features_df['low'] = market_data_df['low']
        features_df['close'] = market_data_df['close']
        features_df['volume'] = market_data_df['volume']
        features_df['high_low_range'] = market_data_df['high'] - market_data_df['low']
        features_df['open_close_range'] = market_data_df['close'] - market_data_df['open']
        features_df['body_size'] = abs(market_data_df['open'] - market_data_df['close'])
        features_df['upper_shadow'] = market_data_df['high'] - np.maximum(market_data_df['open'], market_data_df['close'])
        features_df['lower_shadow'] = np.minimum(market_data_df['open'], market_data_df['close']) - market_data_df['low']


        # --- 2. Technical Indicator Features ---
        # These are generally already pre-calculated as series in `analysis_results_history`
        # We need to extract them by timestamp and merge into features_df
        # Create a temporary DataFrame from analysis_results_history to merge easily
        
        # Collect indicator series
        indicator_series_data = {}
        for timestamp, symbol_analysis in analysis_results_history.items():
            if primary_symbol in symbol_analysis and 'standard_indicators' in symbol_analysis[primary_symbol]:
                for ind_name, ind_values in symbol_analysis[primary_symbol]['standard_indicators'].items():
                    if isinstance(ind_values, np.ndarray) and len(ind_values) == len(market_data_df): # If it's a full series
                        if ind_name not in indicator_series_data:
                            indicator_series_data[ind_name] = np.full(len(market_data_df), np.nan) # Initialize with NaN
                        # This assumes indices align, which they should if analysis_results were from market_data_df
                        indicator_series_data[ind_name] = ind_values # Overwrite with actual series
                        
        if indicator_series_data:
            temp_indicators_df = pd.DataFrame(indicator_series_data, index=market_data_df.index)
            features_df = features_df.join(temp_indicators_df.add_prefix('indicator_'))
            logger.debug(f"Added {len(indicator_series_data)} standard indicator series.")

        # Specific signals from stochastic_wpr_strategy (as historical series)
        # Assuming these are available as series within analysis_results_history if generated for each bar
        # For current structure of `generate_stochastic_wpr_signals` (returns single signal for latest bar)
        # this needs adaptation or a loop over historical bars for proper feature engineering.
        # For current implementation, we'll just add the latest signal if available.
        # For full historical FE, `generate_stochastic_wpr_signals` needs to be run on slices of `df`.
        
        # --- 3. Pattern Recognition Features (Historical Presence) ---
        # Similar to indicators, these need to be available for each historical bar.
        # `analysis_results_history` currently gives "latest bar" results for patterns.
        # To make this robust, the pattern detection functions in `analytics_engine.py` should be runnable per bar.
        # For now, we'll just add features for the *latest* pattern detections for each type, as flags.
        # For training data, this implies running pattern detectors on each historical window.
        
        # Placeholder for pattern flags for *each* bar in the dataframe
        features_df['pattern_bullish_candlestick'] = 0
        features_df['pattern_bearish_candlestick'] = 0
        features_df['pattern_harmonic_bullish'] = 0
        features_df['pattern_harmonic_bearish'] = 0
        features_df['pattern_outside_bar_bullish'] = 0
        features_df['pattern_outside_bar_bearish'] = 0
        features_df['pattern_flag_pennant_bullish'] = 0
        features_df['pattern_flag_pennant_bearish'] = 0
        
        # This will be refined. For now, it will be mostly NaNs or 0s unless re-engineered.


        # --- 4. Lagged Features & Rolling Statistics ---
        for col in ['close', 'volume', 'high_low_range'] + [f'indicator_{ind}' for ind in indicator_series_data.keys() if f'indicator_{ind}' in features_df.columns]:
            if col in features_df.columns:
                for lag in self.lag_periods:
                    features_df[f'{col}_lag_{lag}'] = features_df[col].shift(lag)
                for window in self.rolling_periods:
                    features_df[f'{col}_roll_mean_{window}'] = features_df[col].rolling(window=window).mean()
                    features_df[f'{col}_roll_std_{window}'] = features_df[col].rolling(window=window).std()

        # --- 5. Fundamental Features (Economic Calendar & News Sentiment) ---
        # For each bar, find relevant economic events up to its timestamp.
        # For historical economic events, `economic_events` needs to be processed to align with each bar's timestamp.
        # This requires grouping events by date/time and aggregating impact.
        
        features_df['econ_event_high_impact_nearby'] = 0 # 1 if high impact event nearby
        features_df['econ_event_medium_impact_nearby'] = 0 # 1 if medium impact event nearby
        features_df['econ_event_bias_bullish'] = 0 # 1 if actual > forecast is bullish
        features_df['econ_event_bias_bearish'] = 0 # 1 if actual < forecast is bearish
        
        # This is a very complex loop for historical data. For now, we add dummy features or 
        # assume historical processing is done elsewhere if `economic_events_list` is large.
        # The `news_analysis_results_history` also needs similar time alignment.
        
        # For simplification in `generate_features`: just capture the *latest* news/econ status
        # for the last bar if this function is used for real-time prediction.
        # For *training data*, this part requires careful historical iteration.
        
        # For this version, assume `news_analysis_results_history` is structured per bar.
        # Merge news sentiment features based on timestamp
        sentiment_features = pd.DataFrame(index=market_data_df.index)
        for timestamp, news_analysis in news_analysis_results_history.items():
            # Map sentiment/impact to numerical values
            sentiment = news_analysis.get('sentiment', 'neutral').lower()
            market_impact = news_analysis.get('market_impact', 'none').lower()
            
            row_data = {
                'news_sentiment_positive': 1 if sentiment == 'positive' else 0,
                'news_sentiment_negative': 1 if sentiment == 'negative' else 0,
                'news_sentiment_neutral': 1 if sentiment == 'neutral' else 0,
                'news_market_impact_high': 1 if market_impact == 'high' else 0,
                'news_market_impact_medium': 1 if market_impact == 'medium' else 0,
                'news_market_impact_low': 1 if market_impact == 'low' else 0,
                'news_market_impact_none': 1 if market_impact == 'none' else 0,
                'news_llm_reasoning_length': len(news_analysis.get('reasoning', '')) # Example numerical feature
            }
            sentiment_features.loc[timestamp] = row_data

        features_df = features_df.join(sentiment_features)
        
        # Fill any NaNs from joining (e.g., if no news for a specific bar)
        features_df = features_df.fillna(0) # Fill with 0 for boolean/categorical news features


        # --- 6. Target Variable & Missed Opportunity Feedback ---
        # This is the core of the "ML Model Retraining with Missed Opportunity Feedback" feature.
        # The `target_future_direction` remains the primary prediction target.
        # "Missed opportunity" implies a signal *was generated* but *not acted upon* AND *it would have been profitable*.
        
        # Target for price direction
        features_df['target_future_direction'] = 0 # Default to no significant move
        for i in range(len(features_df) - future_lookahead_bars):
            current_close = features_df['close'].iloc[i]
            future_close = features_df['close'].iloc[i + future_lookahead_bars]
            if current_close != 0:
                price_change = (future_close - current_close) / current_close
                if price_change >= price_change_threshold:
                    features_df.loc[features_df.index[i], 'target_future_direction'] = 1 # Buy (future price increased)
                elif price_change <= -price_change_threshold:
                    features_df.loc[features_df.index[i], 'target_future_direction'] = -1 # Sell (future price decreased)
        
        # New target/feature for "Missed Opportunity"
        # This requires `trade_decisions_history` which logs what Priv *actually did*.
        # For each bar, if Priv had a strong BUY signal but didn't execute, and the price *did* go up, that's a missed buy.
        features_df['target_missed_buy_opportunity'] = 0
        features_df['target_missed_sell_opportunity'] = 0
        features_df['decision_executed_trade'] = 0 # Was a trade actually executed by Priv on this bar?
        features_df['decision_rejected_by_governance'] = 0 # Was a signal rejected by ethics/reg?
        features_df['decision_rejected_by_arbitration'] = 0 # Was a signal rejected by multi-agent arbitration?

        for timestamp, decision_info in trade_decisions_history.items():
            if timestamp in features_df.index: # Ensure timestamp aligns with a bar
                idx = features_df.index.get_loc(timestamp)
                
                # Mark if a trade was executed
                if decision_info.get('action') in ['BUY', 'SELL'] and decision_info.get('trade_id'):
                    features_df.iloc[idx, features_df.columns.get_loc('decision_executed_trade')] = 1
                
                # Mark rejection reasons
                if decision_info.get('regulatory_check') == 'non_compliant':
                    features_df.iloc[idx, features_df.columns.get_loc('decision_rejected_by_governance')] = 1
                if decision_info.get('ethical_check') == 'non_compliant':
                    features_df.iloc[idx, features_df.columns.get_loc('decision_rejected_by_governance')] = 1 # Also governance
                if decision_info.get('arbitration_outcome') == 'CONFLICT_HOLD' or decision_info.get('arbitration_outcome') == 'REJECTED':
                    features_df.iloc[idx, features_df.columns.get_loc('decision_rejected_by_arbitration')] = 1
                
                # Determine missed opportunities
                # A missed buy opportunity: Priv had a strong BUY signal AND didn't execute (for any reason) AND target_future_direction was 1
                # A missed sell opportunity: Priv had a strong SELL signal AND didn't execute AND target_future_direction was -1
                
                # This requires knowing Priv's fuzzy signal at that historical timestamp.
                # Assuming `analysis_results_history` stores fuzzy_inputs and overall_signal
                # If `analysis_results_history` is indexed correctly
                if timestamp in analysis_results_history and primary_symbol in analysis_results_history[timestamp]:
                    historical_fuzzy_signal = analysis_results_history[timestamp][primary_symbol].get('overall_signal', {})
                    historical_fuzzy_recommendation = historical_fuzzy_signal.get('recommendation')
                    historical_fuzzy_strength = historical_fuzzy_signal.get('strength')

                    if features_df.iloc[idx]['decision_executed_trade'] == 0: # If Priv did NOT execute
                        if historical_fuzzy_recommendation == 'BUY' and historical_fuzzy_strength >= (settings.AUTONOMOUS_BUY_STRENGTH_THRESHOLD * 0.8) and features_df.iloc[idx]['target_future_direction'] == 1:
                            features_df.iloc[idx, features_df.columns.get_loc('target_missed_buy_opportunity')] = 1
                            logger.debug(f"Priv: Identified missed BUY opportunity at {timestamp}.")
                        elif historical_fuzzy_recommendation == 'SELL' and historical_fuzzy_strength <= (settings.AUTONOMOUS_SELL_STRENGTH_THRESHOLD * 0.8) and features_df.iloc[idx]['target_future_direction'] == -1:
                            features_df.iloc[idx, features_df.columns.get_loc('target_missed_sell_opportunity')] = 1
                            logger.debug(f"Priv: Identified missed SELL opportunity at {timestamp}.")
        

        # --- Final Cleaning ---
        initial_rows = len(features_df)
        features_df.dropna(inplace=True)
        if len(features_df) < initial_rows:
            logger.info(f"Priv: Dropped {initial_rows - len(features_df)} rows due to NaN values after feature generation.")

        # Ensure all feature columns are numeric (float)
        for col in features_df.columns:
            # Skip target columns from numeric conversion
            if col.startswith('target_'):
                continue
            if pd.api.types.is_numeric_dtype(features_df[col]):
                features_df[col] = features_df[col].astype(float)
            else:
                logger.warning(f"Priv: Non-numeric column '{col}' found in features_df. Consider encoding or dropping.")
                # For now, we'll drop non-numeric columns to ensure a fully numeric dataset for ML
                features_df = features_df.drop(columns=[col])


        logger.info(f"Priv: Generated {len(features_df)} features rows with {len(features_df.columns)} columns for ML training.")
        
        return features_df

# Example Usage (for testing FeatureEngineer in isolation)
async def main_feature_engineer_test():
    logging.basicConfig(level=logging.INFO)
    
    # Mock OHLCV data
    data_length = 300 
    dates = pd.date_range(start='2023-01-01', periods=data_length, freq='D')
    mock_closes = 100 + np.cumsum(np.random.normal(0, 0.5, data_length))
    mock_opens = mock_closes - np.random.uniform(-0.1, 0.1, data_length)
    mock_highs = np.maximum(mock_opens, mock_closes) + np.random.uniform(0, 0.8, data_length)
    mock_lows = np.minimum(mock_opens, mock_closes) - np.random.uniform(0, 0.8, data_length)
    mock_volumes = np.random.randint(1000, 5000, data_length)
    mock_df = pd.DataFrame({
        'open': mock_opens, 'high': mock_highs, 'low': mock_lows, 'close': mock_closes, 'volume': mock_volumes
    }, index=dates)
    mock_df.index.name = 'timestamp'

    # Mock historical analysis results for ALL bars (as if AnalyticsEngine ran historically)
    mock_analysis_results_history = {}
    mock_news_analysis_results_history = {}
    mock_trade_decisions_history = {} # For missed opportunity feedback

    # Populate mock historical analysis results and decisions
    for i in range(len(mock_df)):
        current_timestamp = mock_df.index[i]
        # Simulate standard_indicators output for this bar
        mock_standard_ind = {
            'rsi': np.random.uniform(20, 80), 'macd_hist': np.random.uniform(-1, 1),
            'point': 0.0001
        }
        # Simulate fuzzy signal based on random values for this bar
        mock_fuzzy_signal_strength = np.random.uniform(-100, 100)
        mock_fuzzy_recommendation = "HOLD"
        if mock_fuzzy_signal_strength > 70: mock_fuzzy_recommendation = "BUY"
        elif mock_fuzzy_signal_strength < -70: mock_fuzzy_recommendation = "SELL"

        mock_symbol_analysis_for_bar = {
            'standard_indicators': {k: np.array([v]) for k,v in mock_standard_ind.items()}, # Ensure 1-element array
            'latest_standard_indicators': mock_standard_ind,
            'complex_pattern_score_for_fuzzy': np.random.uniform(0, 100),
            'overall_signal': {
                'strength': mock_fuzzy_signal_strength,
                'recommendation': mock_fuzzy_recommendation,
                'directional_confirmations_score': np.random.randint(-5, 5)
            }
        }
        mock_analysis_results_history[current_timestamp] = {"MOCK_SYMBOL": mock_symbol_analysis_for_bar}

        # Simulate historical news analysis results (e.g., occasional high impact)
        if i % 50 == 0:
            mock_news_analysis_results_history[current_timestamp] = {
                'sentiment': np.random.choice(['positive', 'negative']),
                'market_impact': 'high' if np.random.rand() < 0.2 else 'low',
                'title': f"News at {current_timestamp}", 'reasoning': "Mock news."
            }
        else:
            mock_news_analysis_results_history[current_timestamp] = {"sentiment": "neutral", "market_impact": "none", "title": "No news", "reasoning": "No news."}

        # Simulate historical trade decisions (e.g., 10% of strong signals acted upon, 5% rejected)
        if mock_fuzzy_recommendation in ["BUY", "SELL"] and abs(mock_fuzzy_signal_strength) > 70:
            if np.random.rand() < 0.10: # 10% chance it was executed
                mock_trade_decisions_history[current_timestamp] = {"action": mock_fuzzy_recommendation, "trade_id": f"trade_{i}", "regulatory_check": "compliant", "ethical_check": "compliant", "arbitration_outcome": mock_fuzzy_recommendation}
            elif np.random.rand() < 0.05: # 5% chance it was rejected by governance
                 mock_trade_decisions_history[current_timestamp] = {"action": mock_fuzzy_recommendation, "reason": "Risk too high", "regulatory_check": "non_compliant", "ethical_check": "compliant", "arbitration_outcome": "REJECTED"}
            else: # Remainder are 'missed' opportunities where no trade was executed for other reasons
                 mock_trade_decisions_history[current_timestamp] = {"action": mock_fuzzy_recommendation, "reason": "Not executed for sim", "regulatory_check": "compliant", "ethical_check": "compliant", "arbitration_outcome": mock_fuzzy_recommendation} # Still pass arbitrated outcome
        else: # HOLD or weak signal
            mock_trade_decisions_history[current_timestamp] = {"action": "HOLD", "reason": "Weak signal", "regulatory_check": "compliant", "ethical_check": "compliant", "arbitration_outcome": "HOLD"}


    # Prepare economic events (simplified mock)
    mock_economic_events = [
        {'timestamp': dates[50], 'impact': ImpactLevel.HIGH.value, 'event_name': 'NFP', 'currency': 'USD'},
        {'timestamp': dates[150], 'impact': ImpactLevel.MEDIUM.value, 'event_name': 'CPI', 'currency': 'EUR'}
    ]

    # Initialize FeatureEngineer and generate features
    feature_engineer = FeatureEngineer()
    features_df = feature_engineer.generate_features(
        market_data_df=mock_df,
        analysis_results_history=mock_analysis_results_history,
        economic_events=mock_economic_events,
        news_analysis_results_history=mock_news_analysis_results_history,
        trade_decisions_history=mock_trade_decisions_history,
        primary_symbol="MOCK_SYMBOL",
        future_lookahead_bars=5,
        price_change_threshold=0.005
    )

    print("\n--- Generated Features DataFrame ---")
    print(features_df.head())
    print(f"\nDataFrame shape: {features_df.shape}")
    print(f"Columns: {features_df.columns.tolist()}")

    print(f"\nLast row of features:\n{features_df.iloc[-1].T}") # Transpose for better readability
    print(f"\nTarget Future Direction distribution:\n{features_df['target_future_direction'].value_counts()}")
    print(f"\nMissed Buy Opportunity distribution:\n{features_df['target_missed_buy_opportunity'].value_counts()}")
    print(f"\nMissed Sell Opportunity distribution:\n{features_df['target_missed_sell_opportunity'].value_counts()}")
    print(f"\nDecision Executed Trade distribution:\n{features_df['decision_executed_trade'].value_counts()}")
    print(f"\nDecision Rejected by Governance distribution:\n{features_df['decision_rejected_by_governance'].value_counts()}")
    print(f"\nDecision Rejected by Arbitration distribution:\n{features_df['decision_rejected_by_arbitration'].value_counts()}")
    
    print(f"\nTotal NaNs in features: {features_df.isnull().sum().sum()}")

    # Clean up mock files (if any created by ethical/compliance examples, etc.)
    temp_files = ["backend/governance/ethical_principles.json", "backend/governance/compliance_rules.json", "temp_reputation_ledger_sim_test_orchestrator.jsonl"]
    for f_path in temp_files:
        if os.path.exists(f_path):
            os.remove(f_path)
            logging.info(f"Cleaned up {f_path}")

    # Remove main test script that was written by ethical_framework example
    if os.path.exists("backend/governance/regulatory_compliance.py"): # Assumes a temporary file might be created there
        # Do nothing for now, just ensure cleanup is mentioned
        pass
    
# This part is just for `if __name__ == '__main__':` execution
if __name__ == '__main__':
    asyncio.run(main_feature_engineer_test()) # Call the async test function