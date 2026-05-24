import numpy as np
import pandas as pd
from typing import List, Dict, Any, Callable, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# Import necessary components from our existing indicators
from backend.support_ai.indicators.zigzag import get_swing_points
from backend.support_ai.indicators.standard_indicators import calculate_all_standard_indicators
from backend.support_ai.indicators.candlesticks import find_all_candlestick_patterns
from backend.support_ai.indicators.harmonics import find_harmonic_patterns # Already using zigzag
from backend.support_ai.indicators.outsidebar import find_outside_bars
from backend.support_ai.indicators.wso_wro_trend_lines import detect_wso_wro_trend_lines
from backend.support_ai.indicators.pattern_recognition import detect_flag_and_pennant # Includes regression logic

# --- 1. Define Pattern Structure and Rules ---

class PatternRule:
    """
    Represents a single rule or condition that contributes to a pattern's identification.
    A rule can be a price action check, an indicator condition, or a structural relationship.
    """
    def __init__(self, name: str, check_func: Callable[[pd.DataFrame, Dict[str, Any], Optional[int]], bool], weight: float = 1.0):
        self.name = name # E.g., "Lower High", "RSI Divergence", "Volume Confirmation"
        self.check_func = check_func # A function that checks this specific condition
        self.weight = weight # How important this rule is for the pattern's validity

class ChartPatternDefinition:
    """
    Defines a chart pattern conceptually, with a set of rules and expected characteristics.
    Inspired by the methodology in the provided PDFs.
    """
    def __init__(self,
                 name: str,
                 pattern_type: str, # "Reversal", "Continuation", "Consolidation"
                 expected_direction: Optional[str], # "Bullish", "Bearish", None if neutral
                 rules: List[PatternRule],
                 target_calc_method: Optional[Callable[[Dict[str, Any]], float]] = None): # Function to calculate price target
        self.name = name
        self.pattern_type = pattern_type
        self.expected_direction = expected_direction
        self.rules = rules
        self.target_calc_method = target_calc_method

    def evaluate_pattern(self,
                         df: pd.DataFrame,
                         analysis_results: Dict[str, Any], # Comprehensive results from AnalyticsEngine
                         latest_bar_index: Optional[int] = None # Index of the bar to check against
                        ) -> Dict[str, Any]:
        """
        Evaluates the current state of market data against the pattern's rules.
        
        Returns:
            Dict[str, Any]: Contains 'is_present', 'score', 'matched_rules', 'direction', 'target_price'.
        """
        if latest_bar_index is None:
            latest_bar_index = len(df) - 1

        matched_rules_details = []
        total_weight_matched = 0.0
        
        is_pattern_candidate = True # Assume true unless a fundamental structural rule fails
        
        # Evaluate each rule
        for rule in self.rules:
            try:
                rule_satisfied = rule.check_func(df, analysis_results, latest_bar_index)
                if rule_satisfied:
                    matched_rules_details.append({"rule": rule.name, "satisfied": True, "weight": rule.weight})
                    total_weight_matched += rule.weight
                else:
                    matched_rules_details.append({"rule": rule.name, "satisfied": False, "weight": rule.weight})
                    # If it's a critical rule, set candidate to False
                    # For now, all rules contribute to score, but could add 'critical' flag to PatternRule
                    # if not rule.is_optional: # Conceptual: if rule is mandatory
                    #     is_pattern_candidate = False

            except Exception as e:
                logger.warning(f"Error evaluating rule '{rule.name}' for pattern '{self.name}': {e}")
                matched_rules_details.append({"rule": rule.name, "satisfied": False, "weight": rule.weight, "error": str(e)})
                is_pattern_candidate = False # If a rule check itself fails, invalidate candidate

        # Calculate score based on matched rules
        total_possible_weight = sum(rule.weight for rule in self.rules)
        score = (total_weight_matched / total_possible_weight) * 100 if total_possible_weight > 0 else 0.0

        if not is_pattern_candidate: # If a critical rule was not met
             score = 0.0

        # Determine final presence based on a minimum score threshold
        min_score_for_presence = 60 # Heuristic, configurable
        is_present = score >= min_score_for_presence

        # Calculate target price if pattern is present and method is provided
        target_price = None
        if is_present and self.target_calc_method:
            try:
                # Pass necessary data for target calculation. This might need to be more specific.
                target_price = self.target_calc_method(analysis_results[list(analysis_results.keys())[0]]) # Pass first symbol's results
            except Exception as e:
                logger.warning(f"Error calculating target price for {self.name}: {e}")
                target_price = None

        return {
            "name": self.name,
            "is_present": is_present,
            "score": score,
            "direction": self.expected_direction,
            "pattern_type": self.pattern_type,
            "matched_rules": matched_rules_details,
            "target_price": target_price
        }

# --- 2. Implement Common Rule Check Functions ---
# These functions check specific conditions, combining outputs from various indicators.
# They reflect the 'how to find them using the indicators we already have' guidance.

def rule_is_swing_point(df: pd.DataFrame, analysis_results: Dict[str, Any], bar_index: int, point_type: str) -> bool:
    """Checks if a bar at `bar_index` is a specific type of swing point (e.g., 'high', 'low')."""
    # This leverages the `zigzag.py` output
    if 'zigzag_swing_points' not in analysis_results:
        return False
    
    swing_points = analysis_results['zigzag_swing_points']
    for swing in swing_points:
        # swing is (index, price, type_id)
        # Type IDs: 1 for High, -1 for Low (from zigzag.py)
        if swing[0] == bar_index:
            if (point_type == 'high' and swing[2] == 1) or \
               (point_type == 'low' and swing[2] == -1):
                return True
    return False

def rule_is_rsi_divergence(df: pd.DataFrame, analysis_results: Dict[str, Any], bar_index: int, divergence_type: str) -> bool:
    """Checks for bullish or bearish RSI divergence."""
    # This leverages `standard_indicators.py`
    # Requires analyzing historical RSI and price points. Complex, needs lookback.
    # For now, a placeholder or simplified check based on last few bars.
    
    rsi_series = analysis_results['standard_indicators'].get('rsi')
    if rsi_series is None or len(rsi_series) < 5: # Need enough data for divergence
        return False

    # Simplified check for latest bars. Proper divergence needs swing points.
    if bar_index < 2: return False # Need at least 3 bars for simple price comparison

    latest_close = df['close'].iloc[bar_index]
    prev_close = df['close'].iloc[bar_index - 1]
    prev_prev_close = df['close'].iloc[bar_index - 2]
    
    latest_rsi = rsi_series[bar_index]
    prev_rsi = rsi_series[bar_index - 1]
    prev_prev_rsi = rsi_series[bar_index - 2]

    if np.isnan(latest_rsi) or np.isnan(prev_rsi) or np.isnan(prev_prev_rsi):
        return False

    if divergence_type == 'bullish':
        # Lower low in price, higher low in RSI
        if latest_close < prev_close and latest_rsi > prev_rsi: # Simplified
            return True
        # Or even lower low in price, but higher low in RSI between two lows.
    elif divergence_type == 'bearish':
        # Higher high in price, lower high in RSI
        if latest_close > prev_close and latest_rsi < prev_rsi: # Simplified
            return True
        # Or even higher high in price, but lower high in RSI between two highs.
    return False

def rule_is_volume_confirming(df: pd.DataFrame, analysis_results: Dict[str, Any], bar_index: int, confirmation_type: str) -> bool:
    """Checks for volume confirmation (e.g., increasing on breakout)."""
    # This leverages `standard_indicators.py` (volume)
    volume_series = df['volume'].to_numpy()
    if len(volume_series) < 2:
        return False

    current_volume = volume_series[bar_index]
    avg_volume = np.mean(volume_series[max(0, bar_index - 10):bar_index]) # 10-bar average
    
    if np.isnan(current_volume) or np.isnan(avg_volume):
        return False

    if confirmation_type == 'increase_above_average':
        return current_volume > avg_volume * 1.5 # 50% above average
    elif confirmation_type == 'decrease':
        return current_volume < avg_volume * 0.8 # 20% below average
    return False

def rule_is_price_level_breached(df: pd.DataFrame, analysis_results: Dict[str, Any], bar_index: int, level_type: str, threshold_factor: float = 0.001) -> bool:
    """Checks if a price level (e.g., WRO resistance) is breached."""
    # This leverages `wso_wro_trend_lines.py` or other S/R analysis
    wso_wro_levels = analysis_results.get('wso_wro_levels', {})
    latest_close = df['close'].iloc[bar_index]
    prev_close = df['close'].iloc[bar_index - 1] if bar_index > 0 else latest_close # For breakout confirmation

    if level_type == 'WRO_Resistance_Breakout':
        resistance_levels = wso_wro_levels.get('wro_resistance_levels', [])
        if not resistance_levels: return False
        
        latest_resistance = resistance_levels[-1].get('price')
        if latest_resistance is None: return False

        # Price closes above resistance and was below it previously
        return latest_close > latest_resistance * (1 + threshold_factor) and prev_close < latest_resistance

    elif level_type == 'WSO_Support_Breakdown':
        support_levels = wso_wro_levels.get('wso_support_levels', [])
        if not support_levels: return False

        latest_support = support_levels[-1].get('price')
        if latest_support is None: return False

        # Price closes below support and was above it previously
        return latest_close < latest_support * (1 - threshold_factor) and prev_close > latest_support
    return False


# --- 3. Define Specific Chart Patterns using Rules ---
# This is where patterns from your PDFs  will be formalized.

def create_head_and_shoulders_definition() -> ChartPatternDefinition:
    """Defines the Head and Shoulders reversal pattern."""
    
    # Define rules for Head and Shoulders (conceptual - needs precise swing point logic)
    # Rules would involve:
    # 1. Left Shoulder: high, followed by a lower low
    # 2. Head: higher high than left shoulder, followed by lower low
    # 3. Right Shoulder: lower high than head, followed by lower low
    # 4. Neckline: connecting the lows between shoulders and head.
    # 5. Breakout: price breaking below neckline with volume confirmation.

    # Example: A simplified rule set for demonstration. Actual implementation needs
    # complex logic to identify sequence of swing points and their relative heights/depths.
    
    # Placeholder rule checks (these would need to iterate through recent swing points)
    def check_hns_structure(df: pd.DataFrame, analysis_results: Dict[str, Any], bar_index: int) -> bool:
        # This is highly simplified. A real H&S needs multiple swing points from zigzag
        # and checking their relative prices.
        # Example: look for 3 distinct highs (left_shoulder, head, right_shoulder)
        # and 2 distinct lows (neckline_left, neckline_right)
        # where head > shoulders, and shoulders are roughly equal.
        # This function would call `rule_is_swing_point` multiple times.
        
        # For demonstration: just checks for recent lower high (right shoulder idea)
        if bar_index < 3: return False
        latest_high = df['high'].iloc[bar_index]
        prev_high = df['high'].iloc[bar_index - 1]
        prev_prev_high = df['high'].iloc[bar_index - 2]
        
        # Very rough heuristic: A recent lower high after a previous higher high
        if latest_high < prev_high and prev_high > prev_prev_high:
            return True # Potential peak
        return False

    def check_hns_volume_confirm(df: pd.DataFrame, analysis_results: Dict[str, Any], bar_index: int) -> bool:
        # Volume usually decreases during pattern formation and increases on breakout
        return rule_is_volume_confirming(df, analysis_results, bar_index, 'increase_above_average') # On breakout

    def check_hns_neckline_break(df: pd.DataFrame, analysis_results: Dict[str, Any], bar_index: int) -> bool:
        # This would require actually drawing and identifying the neckline from swing points
        # For simplicity, assume a simple S/R breakdown as proxy.
        return rule_is_price_level_breached(df, analysis_results, bar_index, 'WSO_Support_Breakdown')


    rules = [
        PatternRule("H&S Structure Candidate", check_hns_structure, weight=0.6),
        PatternRule("Volume Confirmation (on break)", check_hns_volume_confirm, weight=0.2),
        PatternRule("Neckline Breakdown", check_hns_neckline_break, weight=0.2)
    ]

    # Target calculation for H&S: height of head to neckline, projected downwards from breakout
    def hns_target_calc(analysis_results_for_symbol: Dict[str, Any]) -> float:
        # Requires identifying actual head and neckline points from pattern data.
        # Placeholder calculation.
        latest_close = analysis_results_for_symbol['indicators']['close']
        return latest_close * 0.95 # Assume 5% drop for bearish target
    
    return ChartPatternDefinition(
        name="Head and Shoulders (Bearish Reversal)",
        pattern_type="Reversal",
        expected_direction="Bearish",
        rules=rules,
        target_calc_method=hns_target_calc
    )

# --- 4. Pattern Scanner to Apply Definitions ---

class PatternScanner:
    """
    Scans market data for predefined chart patterns using the ChartPatternDefinition objects.
    """
    def __init__(self, pattern_definitions: List[ChartPatternDefinition]):
        self.pattern_definitions = pattern_definitions
        logger.info(f"PatternScanner initialized with {len(pattern_definitions)} pattern definitions.")

    def scan_for_patterns(self, df: pd.DataFrame, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Scans the provided market data and comprehensive analysis results for defined patterns.
        
        Args:
            df (pd.DataFrame): OHLCV data.
            analysis_results (Dict[str, Any]): Comprehensive analysis results from AnalyticsEngine.
                                               This is assumed to be for a *single symbol*.
                                               The outer loop in StrategicAdvisor handles multiple symbols.

        Returns:
            List[Dict[str, Any]]: A list of detected patterns, each with its score and details.
        """
        detected_patterns = []
        if df.empty or not analysis_results:
            logger.warning("No data or analysis results provided for pattern scanning.")
            return detected_patterns

        # The core idea from PDFs is about looking for patterns as they form on the latest bars.
        # We'll evaluate patterns mostly based on the very recent price action and indicator states.
        # The 'latest_bar_index' allows rule checks to focus on recent bars relevant to pattern completion.
        latest_bar_index = len(df) - 1
        
        if latest_bar_index < 0:
            return detected_patterns

        for pattern_def in self.pattern_definitions:
            evaluation_result = pattern_def.evaluate_pattern(df, analysis_results, latest_bar_index)
            if evaluation_result['is_present']:
                detected_patterns.append(evaluation_result)
                logger.info(f"Pattern detected: {evaluation_result['name']} (Score: {evaluation_result['score']:.2f})")
            else:
                logger.debug(f"Pattern '{evaluation_result['name']}' not detected (Score: {evaluation_result['score']:.2f})")
        
        return detected_patterns

# --- Example of creating a PatternScanner with definitions ---
# This would be instantiated once, typically in StrategicAdvisor or a higher-level manager.
def initialize_pattern_scanner() -> PatternScanner:
    """
    Initializes and returns a PatternScanner with defined chart patterns.
    This is where you would add definitions for patterns from your PDFs.
    """
    pattern_definitions = [
        create_head_and_shoulders_definition(),
        # Add other pattern definitions here (e.g., Double Top, Double Bottom, Triangles)
        # Each pattern definition will have its own set of PatternRule objects.
    ]
    return PatternScanner(pattern_definitions)


# Example Usage (for testing the framework in isolation)
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Create mock OHLCV data for demonstration
    data_length = 200 
    dates = pd.date_range(start='2023-01-01', periods=data_length, freq='D')
    
    # Simulate data that might contain a rough H&S like structure
    # Left Shoulder
    mock_closes_ls = np.linspace(100, 110, 20)
    # Head
    mock_closes_h = np.linspace(110, 120, 20)
    # Right Shoulder
    mock_closes_rs = np.linspace(120, 110, 20)
    # Downtrend
    mock_closes_dt = np.linspace(110, 90, 140)

    mock_closes = np.concatenate((mock_closes_ls, mock_closes_h, mock_closes_rs, mock_closes_dt))
    # Adjust length if needed to match `data_length`
    if len(mock_closes) < data_length:
        mock_closes = np.pad(mock_closes, (0, data_length - len(mock_closes)), 'edge')
    elif len(mock_closes) > data_length:
        mock_closes = mock_closes[:data_length]

    mock_opens = mock_closes + np.random.uniform(-0.5, 0.5, data_length)
    mock_highs = np.maximum(mock_opens, mock_closes) + np.random.uniform(0, 0.8, data_length)
    mock_lows = np.minimum(mock_opens, mock_closes) - np.random.uniform(0, 0.8, data_length)
    mock_volumes = np.random.randint(1000, 5000, data_length)

    # Ensure valid OHLC structure
    mock_highs = np.maximum(mock_highs, mock_lows)
    mock_highs = np.maximum(mock_highs, np.maximum(mock_opens, mock_closes))
    mock_lows = np.minimum(mock_lows, mock_highs)
    mock_lows = np.minimum(mock_lows, np.minimum(mock_opens, mock_closes))

    mock_df = pd.DataFrame({
        'open': mock_opens,
        'high': mock_highs,
        'low': mock_lows,
        'close': mock_closes,
        'volume': mock_volumes
    }, index=dates)
    mock_df.index.name = 'timestamp'

    # --- Simulate analysis results from AnalyticsEngine ---
    # In a real scenario, you would run the AnalyticsEngine on mock_df
    # For this test, we create a simplified mock analysis_results
    mock_analysis_results_for_scanner = {
        'zigzag_swing_points': get_swing_points(mock_df['high'].to_numpy(), mock_df['low'].to_numpy(), mock_df['close'].to_numpy(), deviation=0.01).tolist(),
        'standard_indicators': {
            'rsi': np.random.uniform(30, 70, data_length), # Mock RSI data
            'volume': mock_df['volume'].to_numpy() # Pass volume data
        },
        'wso_wro_levels': detect_wso_wro_trend_lines(mock_df['high'].to_numpy(), mock_df['low'].to_numpy(), mock_df['close'].to_numpy(), mock_df.index.to_numpy())
        # Other analysis results would be here too
    }
    # To prevent potential issues with `analysis_results` expecting a symbol key later, wrap it.
    mock_analysis_results_full = {"MOCK_SYMBOL": mock_analysis_results_for_scanner}


    print("\n--- Initializing Pattern Scanner ---")
    scanner = initialize_pattern_scanner()

    print("\n--- Scanning for Patterns ---")
    # Scan using data for a single symbol
    detected_patterns = scanner.scan_for_patterns(mock_df, mock_analysis_results_full["MOCK_SYMBOL"])

    if detected_patterns:
        print("\n--- Detected Patterns Summary ---")
        for pattern in detected_patterns:
            print(f"Name: {pattern['name']}, Is Present: {pattern['is_present']}, Score: {pattern['score']:.2f}")
            if pattern['target_price'] is not None:
                print(f"  Projected Target: {pattern['target_price']:.2f}")
            print(f"  Matched Rules: {', '.join([r['rule'] for r in pattern['matched_rules'] if r['satisfied']])}")
    else:
        print("\nNo patterns detected by the scanner.")