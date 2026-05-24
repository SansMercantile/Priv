# backend/support_ai/indicators/elliott_wave/wave.py

import numpy as np
from typing import List, Dict

class Wave:
    """
    A data class to store all information about a detected Elliott Wave pattern.
    This is a Pythonic representation of the Wave class from the MQL code.
    """
    def __init__(self):
        self.name: str = ""
        self.level: int = 0
        self.num_zigzag: int = 0
        self.trend: str = "Undefined"
        
        # The values (prices) and indices of the 6 key points (0-5 or XABCDE)
        self.value: np.ndarray = np.zeros(6)
        self.index: np.ndarray = np.zeros(6, dtype=int)
        
        # Indicates if a point is fixed (1), unfixed (0), or not used (-1)
        self.fixed: np.ndarray = np.full(6, -1, dtype=int)
        
        # The absolute high/low within each wave segment
        self.maximum: np.ndarray = np.zeros(6)
        self.minimum: np.ndarray = np.zeros(6)
        
        # Ratios and scores
        self.length_ratio: np.ndarray = np.full((6, 6), -1.0)
        self.time_ratio: np.ndarray = np.full((6, 6), -1.0)
        self.length: np.ndarray = np.zeros(6)
        self.time: np.ndarray = np.zeros(6)
        
        self.value_fibo_score: float = 0.0
        self.time_fibo_score: float = 0.0
        self.proportion_fibo_score: float = 0.0
        self.fibo_score: float = 0.0
        self.pattern_score: float = 0.0
