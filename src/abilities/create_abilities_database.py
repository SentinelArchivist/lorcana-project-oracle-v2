import pandas as pd
import json
import re
from typing import List, Dict, Optional, Any

# --- Data Structures (from Task 1.1) ---

class ParsedAbility:
    """Represents a single, machine-readable game ability."""
    def __init__(self, trigger: str, effect: str, target: str, value: Any, notes: str = ""):
        self.trigger = trigger
        self.effect = effect
        self.target = target
        self.value = value
        self.notes = notes

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__

class CardProfile:
    """Holds all relevant data for a single card, including its parsed abilities."""
    def __init__(self, card_name: str, unique_id: str, raw_text: str):
        self.card_name = card_name
        self.unique_id = unique_id
        self.raw_text = raw_text
        self.parsed_abilities: List[ParsedAbility] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            'card_name': self.card_name,
            'unique_id': self.unique_id,
            'raw_text': self.raw_text,
            'parsed_abilities': [ability.to_dict() for ability in self.parsed_abilities]
        }

# --- Ability Parser (Task 1.2) ---

def parse_ability_text(text: str) -> List[ParsedAbility]:
    """
    Translates raw card ability text into a list of structured ParsedAbility objects.
    This is the core of the "Abilities Engine".

    Analogy: This function is like a language translator. It reads a sentence in
    "Lorcana English" and translates it into "Computer Logic" (our ParsedAbility class)
    that the simulation engine can understand and execute.
    """
    parsed_abilities = []
    
    # Define patterns for keywords.
    # Some are simple presence checks, others have values to extract.
    keyword_patterns = {
        # Keywords with no value
        'Evasive': r'\bEvasive\b',
        'Rush': r'\bRush\b',
        'Ward': r'\bWard\b',
        'Reckless': r'\bReckless\b',
        'Vanish': r'\bVanish\b',
        'Bodyguard': r'\bBodyguard\b',
        'Support': r'\bSupport\b',
        # Keywords with a numeric value
        'Challenger': r'\bChallenger\s*\+\s*(\d+)\b',
        'Resist': r'\bResist\s*\+\s*(\d+)\b',
        'Shift': r'\bShift\s*(\d+)\b',
        'Singer': r'\bSinger\s*(\d+)\b',
    }

    for keyword, pattern in keyword_patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount = True
            notes = f"Character has the {keyword} keyword."
            
            # If the pattern has a capture group, it's a keyword with a numeric value.
            if match.groups():
                amount = int(match.group(1))
                notes = f"Character has {keyword} with value {amount}."

            parsed_abilities.append(ParsedAbility(
                trigger="Passive",
                effect="GainKeyword",
                target="Self",
                value={"keyword": keyword, "amount": amount},
                notes=notes
            ))

    # Pattern for activated abilities, e.g., "{EXERT} - Draw a card."
    # This is a simplified example focusing on a common pattern.
    activated_ability_pattern = re.compile(r'\{\s*EXERT\s*\}\s*-\s*(.+)', re.IGNORECASE)
    for match in activated_ability_pattern.finditer(text):
        effect_text = match.group(1).strip()
        # Simple mapping from text to structured effect
        if 'draw a card' in effect_text.lower():
            parsed_abilities.append(ParsedAbility(
                trigger="Activated",
                effect="DrawCard",
                target="Player",
                value=1,
                notes=f"Activated ability: {effect_text}"
            ))

    return parsed_abilities

# --- Main Execution ---

def create_abilities_database():
    """
    Reads the master card dataset, parses the ability text for each card,
    and saves the structured data to a JSON file.
    This script fulfills Task 1.2 of the project plan.
    """
    master_dataset_path = 'data/processed/lorcana_card_master_dataset.csv'
    output_json_path = 'data/processed/lorcana_abilities_master.json'
    
    print(f"Loading master dataset from '{master_dataset_path}'...")
    try:
        df = pd.read_csv(master_dataset_path)
    except FileNotFoundError:
        print(f"Error: Master dataset '{master_dataset_path}' not found. Please run data collection scripts first.")
        return

    all_card_profiles: List[CardProfile] = []
    parsed_count = 0

    print("Parsing abilities for all cards...")
    for _, row in df.iterrows():
        raw_body_text = row['Body_Text'] if pd.notna(row['Body_Text']) else ""
        
        profile = CardProfile(
            card_name=row['Name'],
            unique_id=row['Unique_ID'],
            raw_text=raw_body_text
        )

        if raw_body_text:
            profile.parsed_abilities = parse_ability_text(raw_body_text)
            if profile.parsed_abilities:
                parsed_count += 1
        
        all_card_profiles.append(profile)

    print(f"Successfully parsed abilities for {parsed_count} out of {len(all_card_profiles)} cards with text.")
    
    output_data = [profile.to_dict() for profile in all_card_profiles]

    print(f"Saving structured abilities database to '{output_json_path}'...")
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)

    print("\nTask 1.2 (Stage 1) is complete.")
    print(f"Created '{output_json_path}' with structured ability data.")

if __name__ == "__main__":
    create_abilities_database()
