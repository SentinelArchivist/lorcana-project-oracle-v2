def transform_abilities(parsed_abilities: list):
    """
    Transforms a list of parsed abilities into the canonical schema format.
    """
    transformed = []
    for ability in parsed_abilities:
        ability_name = ability['ability']
        value = ability['value']

        # Handle Shift variations
        if 'Shift' in ability_name:
            transformed.append({
                "effect": "SET_SHIFT_COST",
                "value": value
            })
        # Handle Singer keyword
        elif ability_name == 'Singer':
            transformed.append({
                "effect": "SINGER",
                "value": value
            })
        # Handle other keywords with values (e.g., Resist, Challenger)
        elif value is not None:
            transformed.append({
                "effect": "ADD_KEYWORD",
                "keyword": ability_name.upper(),
                "value": value
            })
        # Handle simple keywords that have no value
        else:  # value is None
            transformed.append({
                "effect": "ADD_KEYWORD",
                "keyword": ability_name.upper()
            })

    return transformed