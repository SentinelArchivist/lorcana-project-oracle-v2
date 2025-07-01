import pandas as pd
import json
from typing import List, Dict, Optional, Any

class ParsedAbility:
    """
    Represents a single, machine-readable game ability, translated from raw card text.
    This class defines the structured format for an ability.
    """
    def __init__(self, trigger: str, effect: str, target: str, value: Any, notes: str = ""):
        self.trigger = trigger  # e.g., 'OnPlay', 'When this character quests'
        self.effect = effect    # e.g., 'DrawCard', 'DealDamage'
        self.target = target    # e.g., 'ChosenCharacter', 'Self', 'OpponentPlayer'
        self.value = value      # e.g., 1, 2, 'Rush'
        self.notes = notes      # For complex rules or conditions not easily captured

    def to_dict(self) -> Dict[str, Any]:
        """Converts the ability to a dictionary for JSON serialization."""
        return self.__dict__

class CardProfile:
    """
    Holds all relevant data for a single card, including its parsed abilities.
    """
    def __init__(self, card_name: str, unique_id: str, raw_text: str):
        self.card_name = card_name
        self.unique_id = unique_id
        self.raw_text = raw_text
        self.parsed_abilities: List[ParsedAbility] = [] # To be populated in Task 1.2

    def to_dict(self) -> Dict[str, Any]:
        """Converts the card's profile to a dictionary."""
        return {
            'card_name': self.card_name,
            'unique_id': self.unique_id,
            'raw_text': self.raw_text,
            'parsed_abilities': [ability.to_dict() for ability in self.parsed_abilities]
        }

def design_abilities_data_structure():
    """
    Reads the master card dataset, defines the data structures for abilities,
    and prepares the project for the manual parsing task (Task 1.2).
    This script fulfills Task 1.1 of the project plan.
    """
    master_dataset_path = 'data/processed/lorcana_card_master_dataset.csv'
    
    print(f"Loading master dataset from '{master_dataset_path}'...")
    try:
        df = pd.read_csv(master_dataset_path)
    except FileNotFoundError:
        print(f"Error: Master dataset '{master_dataset_path}' not found. Please run Stage 1a first.")
        return

    all_card_profiles: List[CardProfile] = []

    print("Processing cards to define data structures and extract raw ability text...")
    # Iterate through each card to extract text that needs to be parsed in the next step.
    for _, row in df.iterrows():
        # We only care about cards that have abilities described in their body text.
        raw_body_text = row['Body_Text'] if pd.notna(row['Body_Text']) else ""
        if raw_body_text:
            card_profile = CardProfile(
                card_name=row['Name'],
                unique_id=row['Unique_ID'],
                raw_text=raw_body_text
            )
            all_card_profiles.append(card_profile)

    print(f"Identified {len(all_card_profiles)} cards with ability text requiring translation.")
    print("Defined 'ParsedAbility' and 'CardProfile' classes for holding structured data.")
    print("The system is now ready for the implementation of the parsing logic in Task 1.2.")
    print("\nTask 1.1 (Stage 1) is complete.")

if __name__ == "__main__":
    design_abilities_data_structure()
