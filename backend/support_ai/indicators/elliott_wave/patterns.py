# backend/support_ai/indicators/elliott_wave/patterns.py

from typing import List, Optional # ADD Optional here
from .rules import Rules
from .wave import Wave

class Fibo:
    """Data class for a single Fibonacci relationship rule."""
    def __init__(self):
        self.num_wave1: int = 0
        self.num_wave2: int = 0
        self.score: float = 0.0
        self.low: float = 0.0
        self.middle: float = 0.0
        self.high: float = 0.0

class FiboSet:
    """A collection of Fibonacci rules."""
    def __init__(self):
        self.fibos: List[Fibo] = []

    def add(self, fibo: Fibo):
        self.fibos.append(fibo)
        
    def get_score(self, num_wave1: int, num_wave2: int, ratio: float) -> float:
        """Calculates a score based on how well a given ratio fits the defined Fibonacci rules."""
        score = 0.0
        for fibo in self.fibos:
            if fibo.num_wave1 == num_wave1 and fibo.num_wave2 == num_wave2:
                if fibo.low < ratio < fibo.high:
                    if ratio < fibo.middle:
                        score += fibo.score * (1 - (ratio - fibo.low) / (fibo.middle - fibo.low)) * 100
                    elif ratio > fibo.middle:
                        score += fibo.score * (1 - (fibo.high - ratio) / (fibo.high - fibo.middle)) * 100
                    else: # ratio == fibo.middle
                        score += fibo.score * 100
        return score

class SubwaveDescription:
    """Describes the expected properties and sub-patterns for a single sub-wave."""
    def __init__(self):
        self.wave_label: str = ""
        self.ratio1: float = 0.0
        self.ratio2: float = 0.0
        self.num_wave1: int = 0
        self.num_wave2: int = 0
        self.probabilities: List[float] = []
        self.name_waves: List[str] = []

class Pattern:
    """
    The main container for an Elliott Wave pattern definition.
    It holds all the rules, subwave descriptions, and metadata.
    """
    def __init__(self):
        self.name: str = ""
        self.type: str = ""
        self.probability: float = 0.0
        self.description: str = ""
        self.num_wave: int = 0
        
        self.rules: Rules = Rules()
        self.guidelines: Rules = Rules()
        self.entry_signals: Rules = Rules()
        self.exit_signals: Rules = Rules()
        self.stop_signals: Rules = Rules()
        self.wave_signals: Rules = Rules()
        self.confirm_signals: Rules = Rules()
        
        self.subwaves: List[SubwaveDescription] = []
        self.value_fibos: FiboSet = FiboSet()
        self.time_fibos: FiboSet = FiboSet()
        self.proportion_fibos: FiboSet = FiboSet()
        self.proportion_fibos_required: FiboSet = FiboSet()

    def check(self, wave: Wave) -> bool:
        """
        Checks if a given wave candidate satisfies all the rules for this pattern.
        """
        # This is a placeholder for the complex checking logic from patterns.mqh
        # The full implementation will validate against all rule sets (rules, guidelines, etc.)
        # and calculate the final pattern score.
        if not self.rules.get_result(wave):
            return False

        # Placeholder for Fibo score calculation
        wave.fibo_score = self.value_fibos.get_score(1, 2, 0.618) # Example
        wave.pattern_score = (0.11 * self.probability) + (0.3 * wave.fibo_score)
        
        return True

class Patterns:
    """A collection manager for all defined Elliott Wave patterns."""
    def __init__(self):
        self.patterns: List[Pattern] = []

    def add(self, pattern: Pattern):
        self.patterns.append(pattern)

    def find(self, name: str) -> Optional[Pattern]:
        for p in self.patterns:
            if p.name == name:
                return p
        return None

    def clear(self):
        self.patterns.clear()

