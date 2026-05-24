# backend/support_ai/indicators/harmonics.py

import numpy as np
from typing import List, Dict, Any

# --------------------- Harmonic Pattern Definitions ---------------------
# These dictionaries define the Fibonacci ratios for each harmonic pattern.
# Each pattern has minimum and maximum acceptable ratios for its legs.

HARMONIC_PATTERNS = {
    "Gartley": {
        "ab_min": 0.618, "ab_max": 0.618,
        "bc_min": 0.382, "bc_max": 0.886,
        "cd_min": 1.272, "cd_max": 1.618,
        "xd_min": 0.786, "xd_max": 0.786,
    },
    "Bat": {
        "ab_min": 0.382, "ab_max": 0.5,
        "bc_min": 0.382, "bc_max": 0.886,
        "cd_min": 1.618, "cd_max": 2.618,
        "xd_min": 0.886, "xd_max": 0.886,
    },
    "Butterfly": {
        "ab_min": 0.786, "ab_max": 0.786,
        "bc_min": 0.382, "bc_max": 0.886,
        "cd_min": 1.618, "cd_max": 2.24,
        "xd_min": 1.272, "xd_max": 1.618,
    },
    "Crab": {
        "ab_min": 0.382, "ab_max": 0.618,
        "bc_min": 0.382, "bc_max": 0.886,
        "cd_min": 2.24, "cd_max": 3.618,
        "xd_min": 1.618, "xd_max": 1.618,
    },
    "Deep Crab": {
        "ab_min": 0.886, "ab_max": 0.886,
        "bc_min": 0.382, "bc_max": 0.886,
        "cd_min": 2.0, "cd_max": 3.618,
        "xd_min": 1.618, "xd_max": 1.618,
    },
    "Cypher": {
        "ab_min": 0.382, "ab_max": 0.618,
        "bc_min": 1.13, "bc_max": 1.414,
        "cd_min": 1.272, "cd_max": 2.0,
        "xd_min": 0.786, "xd_max": 0.786,
    },
    "Shark": {
        "ab_min": 0.382, "ab_max": 0.618,
        "bc_min": 1.618, "bc_max": 2.24,
        "cd_min": 1.618, "cd_max": 2.24,
        "xd_min": 0.886, "xd_max": 1.13,
    },
}

def _check_ratios(val: float, min_val: float, max_val: float, tolerance: float = 0.05) -> bool:
    """Checks if a value is within a min/max range with a given tolerance."""
    return (val >= min_val * (1 - tolerance)) and (val <= max_val * (1 + tolerance))

def find_harmonic_patterns(swing_points: np.ndarray) -> List[Dict[str, Any]]:
    """
    Identifies harmonic patterns from a series of swing points.

    Args:
        swing_points (np.ndarray): A structured numpy array of swing points from the ZigZag indicator.
                                  Expected fields: 'index', 'price', 'type'.

    Returns:
        List[Dict[str, Any]]: A list of found harmonic patterns. Each pattern is a dictionary
                              containing its name, direction (bullish/bearish), and the
                              price/index data for its X, A, B, C, and D points.
    """
    found_patterns = []
    if len(swing_points) < 5:
        return found_patterns

    # Iterate through the swing points to find 5-point patterns (X, A, B, C, D)
    for i in range(len(swing_points) - 4):
        p_x = swing_points[i]
        p_a = swing_points[i+1]
        p_b = swing_points[i+2]
        p_c = swing_points[i+3]
        p_d = swing_points[i+4]

        # Ensure alternating swing types (high, low, high, low, etc.)
        if not (p_x['type'] != p_a['type'] and \
                p_a['type'] != p_b['type'] and \
                p_b['type'] != p_c['type'] and \
                p_c['type'] != p_d['type']):
            continue

        # Determine if the potential pattern is bullish or bearish
        # A bullish pattern starts with a swing low at X and ends with a swing low at D
        is_bullish = p_a['price'] > p_x['price']

        # Calculate the lengths of the pattern legs
        xa_leg = abs(p_a['price'] - p_x['price'])
        ab_leg = abs(p_b['price'] - p_a['price'])
        bc_leg = abs(p_c['price'] - p_b['price'])
        cd_leg = abs(p_d['price'] - p_c['price'])
        xd_leg = abs(p_d['price'] - p_x['price'])

        if xa_leg == 0 or ab_leg == 0 or bc_leg == 0:
            continue

        # Calculate Fibonacci Ratios
        ab_ratio = ab_leg / xa_leg
        bc_ratio = bc_leg / ab_leg
        cd_ratio = cd_leg / bc_leg
        xd_ratio = xd_leg / xa_leg

        # Check against each defined harmonic pattern
        for name, ratios in HARMONIC_PATTERNS.items():
            if (_check_ratios(ab_ratio, ratios["ab_min"], ratios["ab_max"]) and
                _check_ratios(bc_ratio, ratios["bc_min"], ratios["bc_max"]) and
                _check_ratios(cd_ratio, ratios["cd_min"], ratios["cd_max"]) and
                _check_ratios(xd_ratio, ratios["xd_min"], ratios["xd_max"])):
                
                pattern_data = {
                    "name": f"{'Bullish' if is_bullish else 'Bearish'} {name}",
                    "direction": "Bullish" if is_bullish else "Bearish",
                    "points": {
                        "X": {"index": int(p_x['index']), "price": float(p_x['price'])},
                        "A": {"index": int(p_a['index']), "price": float(p_a['price'])},
                        "B": {"index": int(p_b['index']), "price": float(p_b['price'])},
                        "C": {"index": int(p_c['index']), "price": float(p_c['price'])},
                        "D": {"index": int(p_d['index']), "price": float(p_d['price'])},
                    }
                }
                found_patterns.append(pattern_data)
                # A sequence of swings can only form one type of pattern, so we break
                # after the first match to avoid multiple detections on the same points.
                break 

    return found_patterns
