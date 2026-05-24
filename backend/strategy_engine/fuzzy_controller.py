# backend/strategy_engine/fuzzy_controller.py

import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from typing import Dict, Any, Optional
import logging

# Ensure skfuzzy is installed: pip install scikit-fuzzy

logger = logging.getLogger(__name__)

class FuzzyController:
    """
    A fuzzy logic controller for generating trading signals based on
    technical indicators, patterns, fundamental news context, and confirmation count.

    This controller will take various inputs, fuzzify them, apply fuzzy rules,
    and then defuzzify the result into a crisp trading signal strength.
    """
    def __init__(self):
        self.signal_strength_ctrl = None
        self._setup_fuzzy_system()
        logger.info("Fuzzy Trading Controller initialized with updated signal classifications.")

    def _setup_fuzzy_system(self):
        """
        Defines the fuzzy variables (antecedents/consequents) and rules
        for the trading signal generation, incorporating new classifications.
        """
        # --- Antecedent (Input) Variables ---
        # 1. Technical Momentum (e.g., based on RSI, MACD)
        #    Range: 0 to 100 (normalized score)
        self.momentum_score = ctrl.Antecedent(np.arange(0, 101, 1), 'momentum_score')
        self.momentum_score['weak_bearish'] = fuzz.trimf(self.momentum_score.universe, [0, 0, 30])
        self.momentum_score['neutral'] = fuzz.trimf(self.momentum_score.universe, [20, 50, 80])
        self.momentum_score['strong_bullish'] = fuzz.trimf(self.momentum_score.universe, [70, 100, 100])

        # 2. Pattern Confirmation (e.g., Candlestick, Harmonic, Outside Bar)
        #    Range: 0 to 100 (normalized score based on pattern strength/reliability)
        self.pattern_confirmation = ctrl.Antecedent(np.arange(0, 101, 1), 'pattern_confirmation')
        self.pattern_confirmation['none'] = fuzz.trimf(self.pattern_confirmation.universe, [0, 0, 20])
        self.pattern_confirmation['weak'] = fuzz.trimf(self.pattern_confirmation.universe, [10, 30, 50])
        self.pattern_confirmation['moderate'] = fuzz.trimf(self.pattern_confirmation.universe, [40, 60, 80])
        self.pattern_confirmation['strong'] = fuzz.trimf(self.pattern_confirmation.universe, [70, 100, 100])

        # 3. News Impact (from EconomicCalendarManager)
        #    Range: 0 to 100 (normalized impact: 0=low/none, 50=medium, 100=high)
        self.news_impact = ctrl.Antecedent(np.arange(0, 101, 1), 'news_impact')
        self.news_impact['low'] = fuzz.trimf(self.news_impact.universe, [0, 0, 40])
        self.news_impact['medium'] = fuzz.trimf(self.news_impact.universe, [30, 60, 90])
        self.news_impact['high'] = fuzz.trimf(self.news_impact.universe, [80, 100, 100])

        # NEW: 4. Confirmation Count (Number of confirming signals from various analyses)
        #    Range: 0 to 10 (assuming a maximum of 10 distinct confirmations)
        self.confirmation_count = ctrl.Antecedent(np.arange(0, 11, 1), 'confirmation_count')
        self.confirmation_count['very_low_conf'] = fuzz.trimf(self.confirmation_count.universe, [0, 0, 3]) # 0-3 confirmations
        self.confirmation_count['low_conf'] = fuzz.trimf(self.confirmation_count.universe, [2, 4, 6]) # 2-6 confirmations
        self.confirmation_count['mild_conf'] = fuzz.trimf(self.confirmation_count.universe, [5, 7, 9]) # 5-9 confirmations (7 is mild)
        self.confirmation_count['high_conf'] = fuzz.trimf(self.confirmation_count.universe, [8, 10, 10]) # 8-10 confirmations (highest is very high)


        # --- Consequent (Output) Variable ---
        # Trading Signal Strength: -100 (Very Low) to 100 (Very High)
        self.signal_strength = ctrl.Consequent(np.arange(-100, 101, 1), 'signal_strength')
        self.signal_strength['very_low'] = fuzz.trimf(self.signal_strength.universe, [-100, -100, -60]) # Strong Sell equivalent
        self.signal_strength['low'] = fuzz.trimf(self.signal_strength.universe, [-70, -30, 0])      # Sell equivalent
        self.signal_strength['mild'] = fuzz.trimf(self.signal_strength.universe, [-20, 0, 20])        # Hold equivalent
        self.signal_strength['high'] = fuzz.trimf(self.signal_strength.universe, [0, 30, 70])       # Buy equivalent
        self.signal_strength['very_high'] = fuzz.trimf(self.signal_strength.universe, [50, 100, 100]) # Strong Buy equivalent

        # --- Fuzzy Rules ---
        # These rules are expanded to incorporate confirmation_count and new output terms.
        # The logic aims to reflect: more confirmations -> stronger signal.

        # Rule 1: Strong Bullish, Strong Pattern, High Confirmations -> Very High Buy
        rule1 = ctrl.Rule(self.momentum_score['strong_bullish'] &
                          self.pattern_confirmation['strong'] &
                          self.confirmation_count['high_conf'],
                          self.signal_strength['very_high'])

        # Rule 2: Strong Bullish, Strong Pattern, Mild Confirmations -> High Buy
        rule2 = ctrl.Rule(self.momentum_score['strong_bullish'] &
                          self.pattern_confirmation['strong'] &
                          self.confirmation_count['mild_conf'],
                          self.signal_strength['high'])

        # Rule 3: Weak Bearish, No Pattern, Very Low Confirmations -> Very Low Sell
        rule3 = ctrl.Rule(self.momentum_score['weak_bearish'] &
                          self.pattern_confirmation['none'] &
                          self.confirmation_count['very_low_conf'],
                          self.signal_strength['very_low'])

        # Rule 4: Neutral Momentum, Weak Pattern, Low Confirmations -> Mild (Hold)
        rule4 = ctrl.Rule(self.momentum_score['neutral'] &
                          self.pattern_confirmation['weak'] &
                          self.confirmation_count['low_conf'],
                          self.signal_strength['mild'])
        
        # Rule 5: High News Impact (overrides/cautions) -> Mild (Hold)
        rule5 = ctrl.Rule(self.news_impact['high'], self.signal_strength['mild'])

        # Rule 6: Medium News Impact, Strong Bullish Momentum, Mild Confirmations -> High Buy
        rule6 = ctrl.Rule(self.news_impact['medium'] &
                          self.momentum_score['strong_bullish'] &
                          self.confirmation_count['mild_conf'],
                          self.signal_strength['high'])
        
        # Rule 7: Weak Bearish Momentum, Low Confirmations -> Low Sell
        rule7 = ctrl.Rule(self.momentum_score['weak_bearish'] &
                          self.confirmation_count['low_conf'],
                          self.signal_strength['low'])

        self.signal_strength_ctrl = ctrl.ControlSystem([rule1, rule2, rule3, rule4, rule5, rule6, rule7])
        self.signal_strength_simulation = ctrl.ControlSystemSimulation(self.signal_strength_ctrl)

    def get_signal(self, inputs: Dict[str, float]) -> float:
        """
        Calculates the crisp trading signal strength based on fuzzy logic.

        Args:
            inputs (Dict[str, float]): A dictionary of crisp input values.
                                       Expected keys: 'momentum_score', 'pattern_confirmation',
                                       'news_impact', 'confirmation_count'.

        Returns:
            float: The defuzzified trading signal strength (-100 to 100).
                   Positive values indicate Buy, negative indicate Sell.
        """
        try:
            self.signal_strength_simulation.input['momentum_score'] = inputs.get('momentum_score', 50)
            self.signal_strength_simulation.input['pattern_confirmation'] = inputs.get('pattern_confirmation', 50)
            self.signal_strength_simulation.input['news_impact'] = inputs.get('news_impact', 0)
            self.signal_strength_simulation.input['confirmation_count'] = inputs.get('confirmation_count', 0) # New input

            self.signal_strength_simulation.compute()
            
            signal = self.signal_strength_simulation.output['signal_strength']
            logger.info(f"Fuzzy signal computed: {signal:.2f} for inputs: {inputs}")
            return signal
        except Exception as e:
            logger.error(f"Error computing fuzzy signal: {e}", exc_info=True)
            # Return a neutral signal or raise an error depending on desired behavior
            return 0.0

    def get_trading_recommendation(self, signal_strength: float) -> Dict[str, str]:
        """
        Interprets the crisp fuzzy signal strength into a trading recommendation
        and an associated aggression level.

        Args:
            signal_strength (float): The defuzzified signal strength from -100 to 100.

        Returns:
            Dict[str, str]: A dictionary with 'recommendation' (BUY/SELL/HOLD)
                            and 'aggression' (Aggressive/Normal/Cautious/Very Cautious).
        """
        recommendation = "HOLD"
        aggression = "Normal"

        if signal_strength >= 60: # Corresponds to 'very_high'
            recommendation = "BUY"
            aggression = "Aggressive"
        elif signal_strength >= 20: # Corresponds to 'high'
            recommendation = "BUY"
            aggression = "Normal"
        elif signal_strength > -20 and signal_strength < 20: # Corresponds to 'mild'
            recommendation = "HOLD"
            aggression = "Cautious" # User specified cautious for mild
        elif signal_strength <= -60: # Corresponds to 'very_low'
            recommendation = "SELL"
            aggression = "Aggressive"
        elif signal_strength <= -20: # Corresponds to 'low'
            recommendation = "SELL"
            aggression = "Normal"
        
        # Special handling for 'mild' signal leading to cautious trading, as per user request
        if -20 <= signal_strength <= 20: # Overlap with hold
            if "HOLD" in recommendation: # Only apply if it's already a hold or very mild buy/sell
                aggression = "Cautious"


        return {"recommendation": recommendation, "aggression": aggression}


# Example Usage (for testing the fuzzy controller in isolation)
if __name__ == "__main__":
    controller = FuzzyController()

    print("\n--- Test Case 1: Strong Bullish Technicals, High Confirmations, Low News Impact ---")
    inputs_1 = {
        'momentum_score': 90,
        'pattern_confirmation': 95,
        'news_impact': 10,
        'confirmation_count': 9 # High confirmations
    }
    signal_1 = controller.get_signal(inputs_1)
    rec_1 = controller.get_trading_recommendation(signal_1)
    print(f"Signal: {signal_1:.2f}, Recommendation: {rec_1['recommendation']}, Aggression: {rec_1['aggression']}")
    # Expected: Very High Buy, Aggressive

    print("\n--- Test Case 2: Neutral Technicals, Mild Confirmations (7), High News Impact (should lean towards Mild/Hold Cautious) ---")
    inputs_2 = {
        'momentum_score': 50,
        'pattern_confirmation': 40,
        'news_impact': 90, # High news impact
        'confirmation_count': 7 # Mild confirmations
    }
    signal_2 = controller.get_signal(inputs_2)
    rec_2 = controller.get_trading_recommendation(signal_2)
    print(f"Signal: {signal_2:.2f}, Recommendation: {rec_2['recommendation']}, Aggression: {rec_2['aggression']}")
    # Expected: Mild/Hold, Cautious

    print("\n--- Test Case 3: Weak Bearish Technicals, Low Confirmations (3), Medium News Impact ---")
    inputs_3 = {
        'momentum_score': 10,
        'pattern_confirmation': 15,
        'news_impact': 60,
        'confirmation_count': 3 # Low confirmations
    }
    signal_3 = controller.get_signal(inputs_3)
    rec_3 = controller.get_trading_recommendation(signal_3)
    print(f"Signal: {signal_3:.2f}, Recommendation: {rec_3['recommendation']}, Aggression: {rec_3['aggression']}")
    # Expected: Low/Sell, Normal

    print("\n--- Test Case 4: Moderate Bullish, Mild Confirmations (7), Low News Impact ---")
    inputs_4 = {
        'momentum_score': 70,
        'pattern_confirmation': 60,
        'news_impact': 10,
        'confirmation_count': 7 # Mild confirmations
    }
    signal_4 = controller.get_signal(inputs_4)
    rec_4 = controller.get_trading_recommendation(signal_4)
    print(f"Signal: {signal_4:.2f}, Recommendation: {rec_4['recommendation']}, Aggression: {rec_4['aggression']}")
    # Expected: High/Buy, Normal (or slightly cautious depending on defuzzification)

