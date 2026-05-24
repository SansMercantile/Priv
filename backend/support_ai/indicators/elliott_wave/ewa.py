# backend/support_ai/indicators/elliott_wave/ewa.py

import logging
import numpy as np
from typing import List, Optional, Any

from .defines import EW_ANALYSIS_TYPE
from .parser import Parser
# UPDATED: Import Zigzags and Points from the new zigzags.py file
from .zigzags import Zigzags, Points # Corrected import path

from .analysis import Analysis
from .node import Node
from .wave import Wave
from .patterns import Patterns

# --- Setup Logging ---
logger = logging.getLogger(__name__)

class EwaController:
    """
    The main controller for running the Elliott Wave Analysis (EWA).
    This class orchestrates the parsing of rules, identification of zigzags,
    and the recursive analysis of wave patterns.
    """
    def __init__(self, rules_filepath: str):
        self.is_ready = False
        self.parser = Parser(rules_filepath)
        self.patterns: Optional[Patterns] = None
        self.first_node: Optional[Node] = None
        # NEW: Initialize our custom Zigzags wrapper
        self.zigzags: Zigzags = Zigzags()
        self.analysis: Analysis = Analysis()

    def initialize(self):
        """
        Initializes the controller by parsing the rules file.
        This must be called once before running any analysis.
        """
        if self.parser.parse():
            self.patterns = self.parser.patterns
            self.analysis.patterns = self.patterns # Link the parsed patterns to the analysis engine
            self.analysis.zigzags = self.zigzags # Link the zigzags instance to analysis
            self.is_ready = True
            logger.info("EWA Controller initialized successfully.")
        else:
            logger.error("EWA Controller failed to initialize.")
            self.is_ready = False

    def run_analysis(self, price_data: np.ndarray) -> Optional[List[dict]]:
        """
        Executes the full Elliott Wave analysis on the given price data.

        Args:
            price_data (np.ndarray): A structured numpy array containing price bars
                                     with fields 'high' and 'low'.

        Returns:
            Optional[List[dict]]: A list of the most probable wave counts, or None if analysis fails.
        """
        if not self.is_ready:
            logger.error("EWA Controller is not initialized. Please call initialize() first.")
            return None

        # 1. Clear previous results
        self.zigzags.remove()
        if self.first_node:
            self.first_node.clear()

        # 2. Create Zigzags from price data
        # The 'type' determines how the zigzag boundaries are handled.
        # Pass high and low prices directly
        self.zigzags.create(price_data['high'], price_data['low'], EW_ANALYSIS_TYPE.FULL_ANALYSIS)
        if self.zigzags.total() == 0:
            logger.warning("No zigzags could be identified from the price data.")
            return [] # Return empty list, not None, if no zigzags

        # 3. Setup the root of the analysis tree
        wave = Wave()
        # The num_zigzag in Wave refers to the total number of zigzags available for analysis
        wave.num_zigzag = self.zigzags.total()
        
        # For the root wave, index[0] and index[1] typically refer to the start and end
        # of the *entire* price series being analyzed.
        wave.index[0] = 0
        wave.index[1] = len(price_data) - 1
        wave.value[0] = price_data['high'][0] # Placeholder, should be actual price at index 0
        wave.value[1] = price_data['high'][len(price_data) - 1] # Placeholder, actual price at end

        self.first_node = Node("Root", wave)

        # 4. Begin the recursive analysis
        # Get all pattern names to start the analysis from the root
        all_pattern_names = [p.name for p in self.patterns.patterns]
        
        self.analysis.run(
            parent_wave=wave,
            node=self.first_node,
            name_subwaves=",".join(all_pattern_names),
            level=0
        )
        
        # 5. Extract and return the results
        results = self._extract_best_wave_counts(self.first_node)
        
        return results

    def _extract_best_wave_counts(self, root_node: Node, count: int = 5) -> List[dict]:
        """
        Traverses the analysis tree and extracts the top N highest-scored wave counts.
        """
        all_patterns = []
        
        def traverse(node: Node):
            if node.wave and node.wave.pattern_score > 0:
                # Ensure points are extracted correctly, handling potential zeros/negatives
                # based on how wave.index and wave.value are populated in Analysis._analysis
                valid_points = []
                for i_idx, p_val in zip(node.wave.index, node.wave.value):
                    if i_idx >= 0 and p_val != 0: # Filter out unused/invalid points
                        valid_points.append({"index": int(i_idx), "price": float(p_val)})

                all_patterns.append({
                    "name": node.wave.name,
                    "score": node.wave.pattern_score,
                    "trend": node.wave.trend,
                    "points": valid_points
                })
            for child in node.childs:
                traverse(child)

        if root_node:
            traverse(root_node)
            
        # Sort by score descending and return the top N
        sorted_patterns = sorted(all_patterns, key=lambda x: x['score'], reverse=True)
        return sorted_patterns[:count]

