# backend/ai_core/rule_engine.py

from typing import Dict, Any, List

class RuleEngine:
    """
    A simple, forward-chaining rule engine that evaluates a set of facts against a rulebook.
    This is used to encode specific, human-defined financial logic, such as compliance checks
    or simple trading heuristics, which can then be combined with the more nuanced output of the AI.
    """
    def __init__(self):
        """Initializes the rule engine with an empty rulebook."""
        self.rules = []
        print("Rule Engine initialized.")

    def add_rule(self, rule: Dict[str, Any]):
        """
        Adds a new rule to the rulebook.
        A rule consists of 'conditions' (what to check) and 'actions' (what to do if conditions are met).
        
        Args:
            rule (Dict[str, Any]): A dictionary representing the rule.
                Example:
                {
                    "name": "High Volatility Risk Reduction",
                    "conditions": {
                        "all": [
                            {"fact": "vix_index", "operator": "greater_than", "value": 30},
                            {"fact": "portfolio_exposure", "operator": "greater_than", "value": 0.8}
                        ]
                    },
                    "actions": [
                        {"action": "generate_alert", "params": {"level": "critical", "message": "High volatility detected. Consider reducing portfolio exposure."}},
                        {"action": "set_fact", "params": {"fact_name": "risk_appetite", "value": "low"}}
                    ]
                }
        """
        if 'name' in rule and 'conditions' in rule and 'actions' in rule:
            self.rules.append(rule)
            # print(f"Added rule: '{rule['name']}'")
        else:
            raise ValueError("Rule must contain 'name', 'conditions', and 'actions'.")

    def evaluate(self, facts: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evaluates all rules against a given set of facts.
        
        Args:
            facts (Dict[str, Any]): A dictionary of current facts, e.g., {"vix_index": 35, "portfolio_exposure": 0.9}.
            
        Returns:
            List[Dict[str, Any]]: A list of actions to be taken, triggered by the rules that fired.
        """
        triggered_actions = []
        for rule in self.rules:
            if self._check_conditions(rule['conditions'], facts):
                # print(f"Rule '{rule['name']}' triggered.")
                triggered_actions.extend(rule['actions'])
        return triggered_actions

    def _check_conditions(self, conditions: Dict[str, List[Dict[str, Any]]], facts: Dict[str, Any]) -> bool:
        """Helper function to check the conditions of a single rule."""
        if 'all' in conditions:
            return all(self._check_condition(cond, facts) for cond in conditions['all'])
        if 'any' in conditions:
            return any(self._check_condition(cond, facts) for cond in conditions['any'])
        return False

    def _check_condition(self, condition: Dict[str, Any], facts: Dict[str, Any]) -> bool:
        """Helper function to check a single condition."""
        fact_name = condition.get('fact')
        operator = condition.get('operator')
        value = condition.get('value')

        if fact_name not in facts:
            return False
            
        fact_value = facts[fact_name]

        operators = {
            "equal": lambda a, b: a == b,
            "not_equal": lambda a, b: a != b,
            "greater_than": lambda a, b: a > b,
            "less_than": lambda a, b: a < b,
            "in": lambda a, b: a in b,
            "not_in": lambda a, b: a not in b,
        }

        if operator in operators:
            return operators[operator](fact_value, value)
        else:
            # print(f"Warning: Unknown operator '{operator}'.")
            return False

# Example Usage:
if __name__ == '__main__':
    engine = RuleEngine()

    # Define some rules
    rule1 = {
        "name": "High Volatility Risk Reduction",
        "conditions": {
            "all": [
                {"fact": "vix_index", "operator": "greater_than", "value": 30},
                {"fact": "portfolio_exposure", "operator": "greater_than", "value": 0.8}
            ]
        },
        "actions": [
            {"action": "generate_alert", "params": {"level": "critical", "message": "High volatility detected. Consider reducing exposure."}},
            {"action": "set_fact", "params": {"fact_name": "trading_mode", "value": "risk_off"}}
        ]
    }

    rule2 = {
        "name": "Tech Sector Overweight Alert",
        "conditions": {
            "any": [
                {"fact": "sector_allocation_tech", "operator": "greater_than", "value": 0.4},
                {"fact": "dominant_sentiment_tech", "operator": "equal", "value": "very_negative"}
            ]
        },
        "actions": [
            {"action": "generate_alert", "params": {"level": "warning", "message": "Tech sector exposure is high or sentiment is very negative."}}
        ]
    }
    
    engine.add_rule(rule1)
    engine.add_rule(rule2)

    # Define some facts about the current market state
    market_facts = {
        "vix_index": 35.2,
        "portfolio_exposure": 0.9,
        "sector_allocation_tech": 0.35,
        "dominant_sentiment_tech": "neutral"
    }

    print("Evaluating facts:", market_facts)
    actions_to_take = engine.evaluate(market_facts)
    print("Triggered Actions:", actions_to_take)
    
    print("\n" + "="*30 + "\n")
    
    # Change the facts
    market_facts_2 = {
        "vix_index": 20.5,
        "portfolio_exposure": 0.7,
        "sector_allocation_tech": 0.45, # This will trigger the second rule
        "dominant_sentiment_tech": "neutral"
    }
    
    print("Evaluating facts:", market_facts_2)
    actions_to_take_2 = engine.evaluate(market_facts_2)
    print("Triggered Actions:", actions_to_take_2)
