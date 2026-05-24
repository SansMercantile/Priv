# backend/support_ai/indicators/elliott_wave/rules.py

import numpy as np
from typing import List, Optional

# Assuming wave.py and defines.py are in the same directory
from .wave import Wave
from .defines import EW_TREND, EW_RULE_MOD, EW_RELATION_TYPE

class Rule:
    """Base class for all Elliott Wave rules."""
    def __init__(self, name: str, rule_type: str):
        self.name = name
        self.type = rule_type

    def check(self, wave: Wave) -> bool:
        """
        Checks if the given wave satisfies this rule.
        This method must be implemented by all subclasses.
        """
        raise NotImplementedError

class InternalRetrace(Rule):
    """Rule for checking the internal retracement of a wave."""
    def __init__(self, name: str, num_wave: int, ratio: float):
        super().__init__(name, "InternalRetrace")
        self.num_wave = num_wave
        self.ratio = ratio

    def check(self, wave: Wave) -> bool:
        # Placeholder for complex internal retracement logic
        # This would check if the wave's internal structure meets the ratio requirement
        return True

class RelativePosition(Rule):
    """Rule for checking the relative price position of two wave points."""
    def __init__(self, name: str, mod1: str, num_wave1: int, sign: str, mod2: str, num_wave2: int):
        super().__init__(name, "RelativePosition")
        self.mod1 = mod1
        self.num_wave1 = num_wave1
        self.sign = sign
        self.mod2 = mod2
        self.num_wave2 = num_wave2

    def _get_value(self, mod: str, num: int, wave: Wave) -> float:
        """Helper to get the correct price value based on the modifier (min, max, or val)."""
        if mod == EW_RULE_MOD.MIN.value:
            return wave.minimum[num]
        if mod == EW_RULE_MOD.MAX.value:
            return wave.maximum[num]
        return wave.value[num]

    def check(self, wave: Wave) -> bool:
        val1 = self._get_value(self.mod1, self.num_wave1, wave)
        val2 = self._get_value(self.mod2, self.num_wave2, wave)
        
        if wave.trend == EW_TREND.UP.value:
            return val1 >= val2 if self.sign == ">=" else val1 <= val2
        elif wave.trend == EW_TREND.DOWN.value:
            return val1 <= val2 if self.sign == ">=" else val1 >= val2
        return False

class FibonacciRule(Rule):
    """Rule for checking Fibonacci relationships between wave legs."""
    def __init__(self, name: str, rule_type: str, num_wave1: int, sign: str, num_wave2: int, ratio: float, num_wave3: int, num_wave4: int):
        super().__init__(name, rule_type)
        self.num_wave1 = num_wave1
        self.sign = sign
        self.num_wave2 = num_wave2
        self.ratio = ratio
        self.num_wave3 = num_wave3
        self.num_wave4 = num_wave4

    def check(self, wave: Wave) -> bool:
        leg1_len = wave.length[self.num_wave1]
        leg2_len = wave.length[self.num_wave3]
        
        if leg1_len <= 0 or leg2_len <= 0:
            return False # Cannot check rule if lengths are invalid
            
        target_val = wave.value[self.num_wave2] + (self.ratio * leg2_len)
        
        if self.sign == ">=":
            return wave.value[self.num_wave1] >= target_val
        else: # sign == "<="
            return wave.value[self.num_wave1] <= target_val

class Logical(Rule):
    """A rule that combines two other rules with a logical operator (AND/OR)."""
    def __init__(self, name: str, rule_type: str, rule1: Rule, rule2: Rule):
        super().__init__(name, rule_type)
        self.rule1 = rule1
        self.rule2 = rule2

class And(Logical):
    def __init__(self, name: str, rule1: Rule, rule2: Rule):
        super().__init__(name, "And", rule1, rule2)

    def check(self, wave: Wave) -> bool:
        return self.rule1.check(wave) and self.rule2.check(wave)

class Or(Logical):
    def __init__(self, name: str, rule1: Rule, rule2: Rule):
        super().__init__(name, "Or", rule1, rule2)

    def check(self, wave: Wave) -> bool:
        return self.rule1.check(wave) or self.rule2.check(wave)

class Rules:
    """A container to manage and execute a list of rules for a pattern."""
    def __init__(self):
        self.rules: List[Rule] = []

    def add(self, rule: Rule):
        self.rules.append(rule)

    def find(self, name: str) -> Optional[Rule]:
        """Finds a rule by its name."""
        for rule in self.rules:
            if rule.name == name:
                return rule
        return None

    def get_result(self, wave: Wave) -> bool:
        """Checks if the wave satisfies all rules in the list."""
        for rule in self.rules:
            if not rule.check(wave):
                return False
        return True

