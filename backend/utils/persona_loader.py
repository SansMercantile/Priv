# backend/utils/persona_loader.py

import logging
import os
import re
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

def parse_persona_file(file_content: str) -> Dict[str, any]:
    """
    Parses the content of a persona markdown file into a structured dictionary.
    """
    persona_data = {}
    lines = file_content.split('\n')
    
    current_section = None
    current_list = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check for section headers like "### 4. Persona: MEZZO (...)" or "Identity & Origin:"
        header_match = re.match(r'^(#+\s*)?([\w\s&]+):\s*(.*)', line)
        if header_match:
            if current_section and current_list:
                persona_data[current_section] = current_list
                current_list = []

            key = header_match.group(2).strip().lower().replace(' ', '_').replace('&', 'and')
            value = header_match.group(3).strip()
            persona_data[key] = value
            current_section = key
        elif line.startswith('*'):
            # It's a list item
            item_text = line.lstrip('* ').strip()
            if ':' in item_text:
                sub_key, sub_value = [s.strip() for s in item_text.split(':', 1)]
                if isinstance(persona_data.get(current_section), list):
                     persona_data[current_section].append({sub_key: sub_value})
                else: # Start a new list of dicts
                    if not isinstance(persona_data.get(current_section), list):
                        persona_data[current_section] = []
                    persona_data[current_section].append({sub_key: sub_value})
            else:
                 if not isinstance(persona_data.get(current_section), list):
                    persona_data[current_section] = []
                 persona_data[current_section].append(item_text)
        elif current_section:
            # Append to the current section's value if it's a string
            if isinstance(persona_data[current_section], str):
                persona_data[current_section] += " " + line
    
    if current_section and current_list:
        persona_data[current_section] = current_list

    return persona_data


def load_persona(persona_name: str) -> Optional[Dict[str, any]]:
    """
    Finds and loads the persona file for a given agent name.

    Args:
        persona_name (str): The name of the persona (e.g., "PRIV", "MPETI", "MEZZO").

    Returns:
        Optional[Dict[str, any]]: A dictionary with the parsed persona data, or None if not found.
    """
    # Define potential filenames based on conventions in the repo
    # This makes the loader robust to slight naming variations.
    potential_filenames = [
        f"{persona_name.capitalize()}'s Personal File",
        f"{persona_name.upper()}'s Personal File",
        f"{persona_name.lower()}_personal_file.md"
    ]
    
    # This path is now a direct, relative path based on the known repository structure.
    # It navigates from `backend/utils` up to the root and then into `docs/personas`.
    docs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'docs', 'personas'))

    for filename in potential_filenames:
        file_path = os.path.join(docs_dir, filename)

        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                parsed_data = parse_persona_file(content)
                logger.info(f"Successfully loaded and parsed persona file for '{persona_name}' from {file_path}")
                return parsed_data
            except Exception as e:
                logger.error(f"Error reading or parsing persona file {file_path}: {e}", exc_info=True)
                return None
                
    logger.warning(f"No persona file found for '{persona_name}' in expected locations within {docs_dir}.")
    return None

