# backend/support_ai/indicators/elliott_wave/parser.py

import logging
import re
from typing import TextIO, List, Tuple

from .defines import WaveLevelDescription
from .patterns import Pattern, Patterns, SubwaveDescription, Fibo, FiboSet
from .rules import Rule, Rules, InternalRetrace, RelativePosition, FibonacciRule, And, Or

# --- Setup Logging ---
logger = logging.getLogger(__name__)

class Parser:
    """
    Parses the EWM.txt file to build a library of Elliott Wave patterns and rules.
    This is a Python translation of the MQL parser logic.
    """
    def __init__(self, rules_filepath: str):
        self.filepath = rules_filepath
        self.lines: List[str] = []
        self.current_line_index: int = 0
        self.patterns: Patterns = Patterns()
        self.rules: Rules = Rules()
        self.level_descriptions: List[WaveLevelDescription] = []

    def parse(self) -> bool:
        """
        Main method to execute the parsing process.
        Returns True on success, False on failure.
        """
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                # Clean up lines: remove comments, strip whitespace, and filter out empty lines
                self.lines = [line.split('/')[0].strip() for line in f]
                self.lines = [line for line in self.lines if line]
        except FileNotFoundError:
            logger.error(f"EWM rules file not found at: {self.filepath}")
            return False
        except Exception as e:
            logger.error(f"Error reading EWM rules file: {e}")
            return False

        # The main parsing loop
        while self.current_line_index < len(self.lines):
            line = self.lines[self.current_line_index]
            
            if line.startswith("Pattern:"):
                self._parse_pattern()
            elif line.startswith("LevelsDescription"):
                self._parse_levels_description()
            elif ":" in line and "{" in self.lines[self.current_line_index + 1]:
                # This is a generic rule definition
                self._parse_rule()
            else:
                self.current_line_index += 1 # Move to next line if not a recognized block start
        
        # Post-processing to link logical rules (And/Or)
        self._set_logical_rules()
        logger.info(f"Successfully parsed {len(self.patterns.patterns)} patterns and {len(self.rules.rules)} rules.")
        return True

    def _get_block(self) -> List[str]:
        """Extracts a block of text enclosed in curly braces {}."""
        block_lines = []
        if "{" not in self.lines[self.current_line_index]:
            self.current_line_index += 1 # Move past the block title
        
        if self.current_line_index >= len(self.lines) or "{" not in self.lines[self.current_line_index]:
             logger.warning(f"Expected '{{' to start a block, but not found at line {self.current_line_index}.")
             return []

        self.current_line_index += 1 # Move past '{'
        
        brace_level = 1
        start_line = self.current_line_index
        
        while self.current_line_index < len(self.lines):
            line = self.lines[self.current_line_index]
            brace_level += line.count("{")
            brace_level -= line.count("}")
            if brace_level == 0:
                block_lines = self.lines[start_line:self.current_line_index]
                self.current_line_index += 1 # Move past '}'
                return block_lines
            self.current_line_index += 1
        
        logger.error("Parsing error: Mismatched braces in EWM file.")
        return []

    def _parse_pattern(self):
        """Parses a full 'Pattern' block."""
        line = self.lines[self.current_line_index]
        pattern = Pattern()
        pattern.name = line.split(':')[1].strip()
        
        block = self._get_block()
        
        sub_block_name = ""
        sub_block_content = []

        for line in block:
            if ":" in line and "{" in self.lines[self.current_line_index + (block.index(line) - len(block)) + 1]: # A new sub-block starts
                if sub_block_name: # Process the previous sub-block
                    self._process_pattern_sub_block(pattern, sub_block_name, sub_block_content)
                
                sub_block_name = line.split(':')[0].strip()
                sub_block_content = []
            elif "}" not in line:
                 sub_block_content.append(line)

        if sub_block_name: # Process the last sub-block
            self._process_pattern_sub_block(pattern, sub_block_name, sub_block_content)

        self.patterns.add(pattern)

    def _process_pattern_sub_block(self, pattern: Pattern, name: str, content: List[str]):
        """Helper to delegate parsing of different sections within a Pattern block."""
        if name == "Type":
            pattern.type = content[0].replace(";", "").strip()
        elif name == "Probability":
            pattern.probability = float(content[0].replace(";", "").strip())
        elif name == "Description":
            pattern.description = content[0].replace(";", "").strip()
        elif name == "Rules" or name == "Guidelines" or name == "EntrySignals" or name == "ExitSignals" or name == "StopSignals" or name == "WaveSignals" or name == "ConfirmSignals":
            rules_list = [r.replace(";", "").strip() for r in content]
            # We will link these rule names to actual rule objects later
            setattr(pattern, name.lower(), rules_list)
        # Add other sub-block parsers here (Subwaves, Fibo, etc.) as needed

    def _parse_rule(self):
        """Parses a single rule definition block."""
        line = self.lines[self.current_line_index]
        rule_type, rule_name = line.split(':')
        rule_type = rule_type.strip()
        rule_name = rule_name.strip()
        
        block = self._get_block()
        content = block[0].replace(";", "").strip() if block else ""

        rule = None
        if rule_type == "InternalRetrace":
            num_wave, ratio = content.split(',')
            rule = InternalRetrace(rule_name, int(num_wave), float(ratio))
        elif rule_type == "RelativePosition":
            # This requires more complex regex parsing due to its format
            # Example: min(1)>=0
            match = re.match(r"(min|max|val)?\(?(\d)\)?(>=|<=)(min|max|val)?\(?(\d)\)?", content)
            if match:
                mod1, num1, sign, mod2, num2 = match.groups()
                rule = RelativePosition(rule_name, mod1 or 'val', int(num1), sign, mod2 or 'val', int(num2))
        elif rule_type == "LengthRatio" or rule_type == "TimeRatio":
             # Placeholder for FibonacciRule parsing
             pass
        elif rule_type == "And" or rule_type == "Or":
            rule1_name, rule2_name = content.split(',')
            # We store names for now and link objects later
            rule = (rule_name, rule_type, rule1_name.strip(), rule2_name.strip())

        if rule and isinstance(rule, Rule):
            self.rules.add(rule)
        elif rule: # It's a tuple for a logical rule
            # Store it temporarily to be processed by _set_logical_rules
            if not hasattr(self, '_temp_logical_rules'):
                self._temp_logical_rules = []
            self._temp_logical_rules.append(rule)

    def _set_logical_rules(self):
        """Second pass to link logical AND/OR rules to their actual rule objects."""
        if not hasattr(self, '_temp_logical_rules'):
            return
            
        for name, type, r1_name, r2_name in self._temp_logical_rules:
            rule1 = self.rules.find(r1_name)
            rule2 = self.rules.find(r2_name)
            if rule1 and rule2:
                if type == "And":
                    self.rules.add(And(name, rule1, rule2))
                elif type == "Or":
                    self.rules.add(Or(name, rule1, rule2))
            else:
                logger.warning(f"Could not create logical rule '{name}': one or both sub-rules not found ('{r1_name}', '{r2_name}').")

    def _parse_levels_description(self):
        """Parses the LevelsDescription block."""
        block = self._get_block()
        # Logic to parse the multi-line level descriptions will go here
        pass

