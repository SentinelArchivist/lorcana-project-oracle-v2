def parse_abilities(ability_string: str):
    """
    Parses a raw ability string into a structured list of abilities.
    Handles single keywords, comma-separated lists, and keywords with numeric values (including signed).
    """
    abilities = []
    # Split the string by commas and process each part
    for part in ability_string.split(','):
        stripped_part = part.strip()
        if not stripped_part:
            continue

        words = stripped_part.split()
        
        # Try to parse the last word as an integer
        try:
            # This handles '5', '+1', etc.
            value = int(words[-1])
            # If successful, and there's more than one word, it's a keyword with value
            if len(words) > 1:
                name = " ".join(words[:-1])
                abilities.append({"ability": name, "value": value})
            else: # It's just a number, treat as a simple keyword for now
                abilities.append({"ability": stripped_part, "value": None})
        except (ValueError, IndexError):
            # If parsing fails, it's a simple keyword
            abilities.append({"ability": stripped_part, "value": None})
            
    return abilities