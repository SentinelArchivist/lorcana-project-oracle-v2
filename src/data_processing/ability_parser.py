"""
Legacy compatibility module for ability_parser.
This module provides backward compatibility for code that still imports the old ability_parser.
The actual parsing functionality has been moved to src/abilities/create_abilities_database.py
"""

from typing import List, Dict, Any
from src.abilities.create_abilities_database import parse_keywords, ParsedAbility


def parse_abilities(ability_input) -> List[Dict[str, Any]]:
    """
    Legacy compatibility function for parse_abilities.
    
    This function maintains the old interface expected by existing code and tests,
    parsing ability strings in the exact format expected by legacy tests.
    
    Args:
        ability_input: Raw ability text to parse (str) or list of abilities
        
    Returns:
        List[Dict[str, Any]]: List of parsed abilities in legacy format
    """
    # Handle different input types for compatibility
    if isinstance(ability_input, list):
        if not ability_input:
            return []
        # Join list elements into a single string
        ability_string = ', '.join(str(item) for item in ability_input if item)
    else:
        ability_string = ability_input
    
    if not ability_string or (isinstance(ability_string, str) and not ability_string.strip()):
        return []
    
    import re
    
    # Split by commas and process each part
    parts = [part.strip() for part in ability_string.split(',')]
    legacy_format = []
    
    for part in parts:
        if not part:
            continue
            
        # Try to match patterns like "Resist +1", "Shift 5", "Puppy Shift 3"
        # Pattern: (ability name) (optional +) (number)
        match = re.search(r'^(.+?)\s*\+?\s*(\d+)$', part)
        if match:
            ability_name = match.group(1).strip()
            value = int(match.group(2))
            legacy_format.append({"ability": ability_name, "value": value})
        else:
            # Simple keyword without value
            legacy_format.append({"ability": part, "value": None})
    
    return legacy_format
