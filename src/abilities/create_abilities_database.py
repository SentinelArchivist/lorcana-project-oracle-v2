import pandas as pd
import json
import re
from typing import List, Dict, Optional, Any
import pandas as pd
import os
from src.utils.logger import get_logger

# Get the logger instance
logger = get_logger()

# --- Data Structures ---

class ParsedAbility:
    """Represents a single, machine-readable game ability."""
    def __init__(self, trigger: Dict[str, Any], effect: str, target: str, value: Any, cost: Optional[Dict[str, Any]] = None, condition: Optional[Dict[str, Any]] = None, duration: Optional[str] = None, notes: str = ""):
        self.trigger = trigger
        self.effect = effect
        self.target = target
        self.value = value
        self.cost = cost
        self.condition = condition
        self.duration = duration
        self.notes = notes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trigger": self.trigger,
            "effect": self.effect,
            "target": self.target,
            "value": self.value,
            "cost": self.cost,
            "condition": self.condition,
            "duration": self.duration,
            "notes": self.notes
        }

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

# --- Full-Spectrum Ability Parser (Task 2.8) ---

# A comprehensive grammar of Lorcana effects based on the programmer's guide
# This dictionary maps effect primitives to regex patterns.
ABILITY_GRAMMAR = {
    'Triggers': {
        # Simple, self-referential triggers
        'OnPlay': {'pattern': r'When you play this character', 'primary_trigger': 'OnPlay'},
        'OnQuest': {'pattern': r'Whenever this character quests', 'primary_trigger': 'OnQuest'},
        'OnSingSong': {'pattern': r'Whenever one of your characters sings a song', 'primary_trigger': 'OnSingSong'},
        'EndOfTurn': {'pattern': r'At the end of your turn', 'primary_trigger': 'EndOfTurn'},
        'OnBanish': {'pattern': r'When this character is banished', 'primary_trigger': 'OnBanish'},
        'Activated': {'pattern': r'\{EXERT\}', 'primary_trigger': 'Activated'},

        # Complex triggers with subjects
        'ComplexBanishWithSubtype': {
            'pattern': r'Whenever one of your other (.*?) characters is banished,?',
            'primary_trigger': 'OnBanish',
            'subject': 'OtherCharacters'
        },
        'ComplexBanishWithSubtypeAndContext': {
            'pattern': r'Whenever one of your other (.*?) characters is banished in a challenge,?',
            'primary_trigger': 'OnBanish',
            'subject': 'OtherCharacters',
            'context': 'OnChallenge'
        },
        'ComplexBanish': {
            'pattern': r'Whenever one of (your other characters) is challenged and banished',
            'primary_trigger': 'OnBanish',
            'subject': 'OtherCharacters',
            'context': 'OnChallenge'
        }
    },
    'Effects': {
        'DrawCard': r'draw (\d+|a) card',
        'DealDamage': r'deal (\d+) damage',
        'GainLore': r'gain (\d+) lore',
        'LoseLore': r'lose (\d+) lore',
        'Banish': r'banish chosen',
        'ReturnToHand': r'return (chosen .*|that card) to (?:its owner.s hand|their hand|your hand)',
        'ModifyStrength': r'gains? \+?(-?\d+) Strength',
        'ModifyWillpower': r'gets? \+(\d+) \{w\}',
        'ModifyLore': r'(?:gets?|give) \+?(\d+) \{l\}', 
        'RemoveDamage': r'remove up to (\d+) damage',
        'GrantStatus': r"can't be challenged", 
        'OpponentChoosesAndBanishes': r'(?:each opponent )?chooses and banishes one of their characters',
        'ReadyCharacter': r'\bready\b',
        'RemoveAllDamage': r'remove all damage',
    },
    'Targets': {
        # Order is important here: check for more specific targets first.
        'EachPuppyCharacter': r'each of your Puppy characters',
        'OtherCharacters': r'Your other characters',
        'Self': r'this character',
        'ChosenCharacter': r'chosen character',
        'AnotherChosenCharacter': r'another chosen character',
        'OpponentCharacter': r'opponent.s character',
        'AllOpponentCharacters': r'each of your opponent.s characters',
        'Player': r'\byou\b', # Use word boundary to not match 'your'
        'Opponent': r'opponent',
        'EachOpponent': r'each opponent',
    },
    'Conditions': {
        'PlayerHasCharacterNamed': {
            'pattern': r'While you have a character named (.*?) in play'
        },
        'PlayerHasCharacters': {
            'pattern': r'If you have (\d+ or more) other characters in play'
        },
        'CharacterIsExerted': {
            'pattern': r'if this character is exerted',
            'target': 'Self'
        },
        'MayPayCost': {
            'pattern': r'you may pay (\d+) \{i\} to',
            'target': 'Player'
        }
    },
    'Durations': {
        'StartOfNextTurn': r'until the start of your next turn',
        'EndOfTurn': r'until the end of the turn',
    }
}

# Pre-sort grammar by pattern length (desc) for matching priority
SORTED_TRIGGERS = sorted(ABILITY_GRAMMAR['Triggers'].items(), key=lambda x: len(x[1]['pattern']), reverse=True)
SORTED_TARGETS = sorted(ABILITY_GRAMMAR['Targets'].items(), key=lambda x: len(x[1]), reverse=True)
SORTED_DURATIONS = sorted(ABILITY_GRAMMAR['Durations'].items(), key=lambda x: len(x[1]), reverse=True)
SORTED_CONDITIONS = sorted(ABILITY_GRAMMAR['Conditions'].items(), key=lambda x: len(x[1]['pattern']), reverse=True)
SORTED_EFFECTS = sorted(ABILITY_GRAMMAR['Effects'].items(), key=lambda x: len(x[1]), reverse=True)

KEYWORD_PATTERNS = {
    'Evasive': r'\bEvasive\b',
    'Rush': r'\bRush\b',
    'Ward': r'\bWard\b',
    'Reckless': r'\bReckless\b',
    'Vanish': r'\bVanish\b',
    'Bodyguard': r'\bBodyguard\b',
    'Support': r'\bSupport\b',
    'Challenger': r'\bChallenger\s*\+\s*(\d+)\b',
    'Resist': r'\bResist\s*\+\s*(\d+)\b',
    'Shift': r'\bShift\s*(\d+)\b',
    'Singer': r'\bSinger\s*(\d+)\b',
}

def parse_keywords(text: str) -> tuple[list[ParsedAbility], str]:
    """Parses all standard keywords from the text and returns them along with the remaining text."""
    abilities = []
    remaining_text = text
    # Iterate over a sorted list of keywords to handle cases where one keyword is a substring of another (e.g., Resist vs Resist +1)
    # Sorting by length of pattern descending ensures longer matches are tried first.
    sorted_keywords = sorted(KEYWORD_PATTERNS.items(), key=lambda item: len(item[1]), reverse=True)

    for keyword, pattern in sorted_keywords:
        match = re.search(pattern, remaining_text, re.IGNORECASE)
        if match:
            amount = 1  # Default for keywords without a value (like Rush, Evasive)
            if match.groups():
                # If there's a capture group, it's the value (like Challenger +2)
                amount = int(match.group(1))

            abilities.append(ParsedAbility(
                trigger={"type": "Passive"},
                effect="GainKeyword",
                target="Self",
                value={"keyword": keyword, "amount": amount},
                condition=None,
                notes=f"Character has {keyword} keyword."
            ))

            # Remove the matched keyword phrase to avoid re-parsing
            # We use match.group(0) to ensure we remove exactly what was matched.
            remaining_text = remaining_text.replace(match.group(0), '', 1).strip()
            # Also remove any leading comma that might be left over.
            if remaining_text.startswith(','):
                remaining_text = remaining_text[1:].strip()

    return abilities, remaining_text

def parse_complex_abilities(text: str) -> List[ParsedAbility]:
    """Parses triggered and activated abilities based on the defined grammar."""
    abilities: List[ParsedAbility] = []
    sentences = re.split(r'(?<!e\.g)(?<!i\.e)\.\s*', text)

    for sentence in sentences:
        original_sentence = sentence.strip()
        if not original_sentence: continue

        # --- 0. Pre-process: Named Abilities ---
        sentence = re.sub(r'^[A-Z\s\'’]+:\s*', '', original_sentence, flags=re.IGNORECASE)

        # --- 1. Identify Trigger ---
        trigger_dict = {'type': 'Passive'}
        for trigger_key, trigger_def in SORTED_TRIGGERS:
            match = re.search(trigger_def['pattern'], sentence, re.IGNORECASE)
            if match:
                trigger_dict['type'] = trigger_def['primary_trigger']
                if 'subject' in trigger_def: trigger_dict['subject'] = trigger_def['subject']
                if 'context' in trigger_def: trigger_dict['context'] = trigger_def['context']
                if match.groups():
                    trigger_dict['subtype'] = match.group(1).strip()
                sentence = sentence[match.end():].strip()
                if sentence.startswith(','):
                    sentence = sentence[1:].strip()
                break

        # --- 2. Identify Duration ---
        parsed_duration = None
        for duration_key, duration_pattern in SORTED_DURATIONS:
            duration_match = re.search(duration_pattern, sentence, re.IGNORECASE)
            if duration_match:
                parsed_duration = duration_key
                sentence = sentence.replace(duration_match.group(0), '', 1).strip()
                break

        # --- 3. Identify Condition ---
        parsed_condition = None
        for cond_key, cond_def in SORTED_CONDITIONS:
            cond_match = re.search(cond_def['pattern'], sentence, re.IGNORECASE)
            if cond_match:
                parsed_condition = {'type': cond_key}
                if 'target' in cond_def: parsed_condition['target'] = cond_def['target']
                if cond_match.groups():
                    val_str = cond_match.group(1).strip()
                    if ' or more' in val_str: val_str = val_str.replace(' or more', '')
                    try: parsed_condition['value'] = int(val_str)
                    except (ValueError, TypeError): parsed_condition['value'] = val_str
                sentence = sentence.replace(cond_match.group(0), '', 1).strip()
                if sentence.startswith(','): sentence = sentence[1:].strip()
                break

        # --- 4. Identify Effects and Targets ---
        protected_phrases = ["chooses and banishes"]
        
        should_split = True
        for phrase in protected_phrases:
            if phrase in sentence:
                should_split = False
                break
        
        if should_split:
            effect_clauses = re.split(r'\s+and\s+|, and |, ', sentence)
        else:
            effect_clauses = [sentence]

        parsed_effects = []
        last_target = 'Self'  # Default/carry-over target

        for sub_clause in effect_clauses:
            sub_clause = sub_clause.strip()
            if not sub_clause: continue

            current_target = last_target
            found_target_in_clause = False
            for target, target_pattern in SORTED_TARGETS:
                if re.search(target_pattern, sub_clause, re.IGNORECASE):
                    current_target = target
                    found_target_in_clause = True
                    break
            
            if 'you may' in original_sentence.lower() and not found_target_in_clause:
                current_target = 'Player'
            
            if ' them' in sub_clause.lower():
                current_target = last_target

            for effect, effect_pattern in SORTED_EFFECTS:
                effect_match = re.search(effect_pattern, sub_clause, re.IGNORECASE)
                if effect_match:
                    value = 1
                    if effect == 'GrantStatus':
                        value = 'CannotBeChallenged'
                    elif effect_match.groups():
                        val_str = effect_match.group(1).strip()
                        if val_str.lower() == 'a': value = 1
                        else:
                            try: value = int(val_str)
                            except (ValueError, TypeError): value = val_str
                    
                    if effect == 'OpponentChoosesAndBanishes': current_target = 'OpponentCharacter'

                    parsed_effects.append({"effect": effect, "value": value, "target": current_target})
                    last_target = current_target  # Update for next clause
                    break
        
        # --- 5. Create abilities from parsed effects ---
        if not parsed_effects and not trigger_dict['type'] == 'Passive':
             # Handle cases where the whole sentence is the effect, e.g., simple triggers
             pass # Future improvement

        for p_effect in parsed_effects:
            abilities.append(ParsedAbility(
                trigger=trigger_dict,
                effect=p_effect["effect"],
                target=p_effect["target"],
                value=p_effect["value"],
                condition=parsed_condition,
                duration=parsed_duration,
                notes=original_sentence
            ))

    return abilities

def parse_ability_text(text: str) -> list[ParsedAbility]:
    """Orchestrates the parsing of keywords and complex abilities."""
    if not text:
        return []

    keyword_abilities, text_minus_keywords = parse_keywords(text)

    complex_text = re.sub(r'\s*\([^)]*\)', '', text_minus_keywords)
    complex_abilities = parse_complex_abilities(complex_text)

    return keyword_abilities + complex_abilities

# --- Main Execution ---

def create_abilities_database():
    """
    Reads the master card dataset, parses the ability text for each card,
    and saves the structured data to a JSON file.
    This script fulfills Task 2.8 of the project plan.
    """
    master_dataset_path = 'data/processed/lorcana_card_master_dataset.csv'
    output_json_path = 'data/processed/lorcana_abilities_master.json'
    
    logger.info(f"Loading master dataset from '{master_dataset_path}'...")
    try:
        df = pd.read_csv(master_dataset_path)
    except FileNotFoundError:
        logger.error(f"Master dataset '{master_dataset_path}' not found.")
        return

    all_card_profiles: List[CardProfile] = []
    parsed_count = 0

    logger.info("Parsing abilities for all cards with new full-spectrum parser...")
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

    logger.info(f"Successfully parsed abilities for {parsed_count} out of {len(df)} cards.")

    output_data = [profile.to_dict() for profile in all_card_profiles]

    logger.info(f"Saving structured abilities database to '{output_json_path}'...")
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)

    logger.info("\nTask 2.8 is complete.")
    logger.info(f"Created '{output_json_path}' with new structured ability data.")

if __name__ == "__main__":
    create_abilities_database()
