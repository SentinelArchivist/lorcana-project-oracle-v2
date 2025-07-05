"""
Legacy compatibility module for ability_transformer.
This module provides backward compatibility for code that still imports the old ability_transformer.
The actual transformation functionality has been moved to src/abilities/create_abilities_database.py
"""

from typing import List, Dict, Any


def transform_abilities(parsed_abilities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Legacy compatibility function for transform_abilities.
    
    This function maintains the old interface expected by existing code and tests,
    transforming parsed abilities into the schema format.
    
    Args:
        parsed_abilities (List[Dict[str, Any]]): List of parsed abilities in legacy format
        
    Returns:
        List[Dict[str, Any]]: List of abilities in schema format
    """
    if not parsed_abilities:
        return []
    
    schema_abilities = []
    
    for ability in parsed_abilities:
        ability_name = ability.get("ability", "")
        value = ability.get("value")
        
        # Transform based on ability type
        if ability_name.lower() == "evasive":
            schema_abilities.append({"effect": "ADD_KEYWORD", "keyword": "EVASIVE"})
        elif ability_name.lower() == "rush":
            schema_abilities.append({"effect": "ADD_KEYWORD", "keyword": "RUSH"})
        elif ability_name.lower() == "ward":
            schema_abilities.append({"effect": "ADD_KEYWORD", "keyword": "WARD"})
        elif ability_name.lower() == "bodyguard":
            schema_abilities.append({"effect": "ADD_KEYWORD", "keyword": "BODYGUARD"})
        elif ability_name.lower() == "reckless":
            schema_abilities.append({"effect": "ADD_KEYWORD", "keyword": "RECKLESS"})
        elif ability_name.lower() == "support":
            schema_abilities.append({"effect": "ADD_KEYWORD", "keyword": "SUPPORT"})
        elif ability_name.lower() == "vanish":
            schema_abilities.append({"effect": "ADD_KEYWORD", "keyword": "VANISH"})
        elif ability_name.lower() == "challenger":
            if value is not None:
                schema_abilities.append({"effect": "ADD_KEYWORD", "keyword": "CHALLENGER", "value": value})
            else:
                schema_abilities.append({"effect": "ADD_KEYWORD", "keyword": "CHALLENGER"})
        elif ability_name.lower() == "resist":
            if value is not None:
                schema_abilities.append({"effect": "ADD_KEYWORD", "keyword": "RESIST", "value": value})
            else:
                schema_abilities.append({"effect": "ADD_KEYWORD", "keyword": "RESIST"})
        elif ability_name.lower() == "shift" or "shift" in ability_name.lower():
            # Handle both "Shift" and compound shifts like "Puppy Shift"
            if value is not None:
                schema_abilities.append({"effect": "SET_SHIFT_COST", "value": value})
            else:
                schema_abilities.append({"effect": "SET_SHIFT_COST"})
        elif ability_name.lower() == "singer":
            if value is not None:
                schema_abilities.append({"effect": "SINGER", "value": value})
            else:
                schema_abilities.append({"effect": "SINGER"})
        else:
            # Generic keyword handling
            if value is not None:
                schema_abilities.append({"effect": "ADD_KEYWORD", "keyword": ability_name.upper(), "value": value})
            else:
                schema_abilities.append({"effect": "ADD_KEYWORD", "keyword": ability_name.upper()})
    
    return schema_abilities
