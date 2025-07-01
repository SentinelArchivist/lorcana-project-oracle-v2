import pandas as pd
import re
import sys

def parse_and_validate_decks():
    """
    Parses a local decklist file, validates every card against the master dataset,
    and outputs a single, validated CSV file.
    """
    master_dataset_path = 'data/processed/lorcana_card_master_dataset.csv'
    decklist_path = 'data/raw/2025.07.01-meta-decks.md'
    output_filename = 'data/processed/lorcana_metagame_decks.csv'

    # --- 1. Load Master Card Data & Create Validation Set ---
    try:
        master_df = pd.read_csv(master_dataset_path)
        master_card_names = set(master_df['Name'])
        print(f"Successfully loaded {len(master_card_names)} card names from '{master_dataset_path}'.")
    except FileNotFoundError:
        print(f"Error: Master dataset '{master_dataset_path}' not found. Please run Stage 1a first.")
        sys.exit(1)

    # --- 2. Parse Decklist File ---
    parsed_cards = []
    current_deck_name = None
    deck_count = 0

    print(f"Parsing decklists from '{decklist_path}'...")
    try:
        with open(decklist_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # Check for deck name line
                deck_match = re.match(r'^#\s*\[Set\s*\d+\]\s*(.*)', line)
                if deck_match:
                    current_deck_name = deck_match.group(1).strip()
                    deck_count += 1
                    continue

                # Check for card entry line
                card_match = re.match(r'^(\d+)\s+(.*)', line)
                if card_match and current_deck_name:
                    quantity = int(card_match.group(1))
                    card_name = card_match.group(2).strip()

                    # --- 3. CRUCIAL: Non-Negotiable Data Validation ---
                    if card_name not in master_card_names:
                        error_message = (
                            f"VALIDATION FAILED: Card '{card_name}' from deck '{current_deck_name}' "
                            f"not found in {master_dataset_path}. Please correct the name in "
                            f"{decklist_path} and rerun."
                        )
                        print(error_message)
                        sys.exit(1) # Halt execution immediately

                    parsed_cards.append({
                        'DeckName': current_deck_name,
                        'CardName': card_name,
                        'Quantity': quantity
                    })

    except FileNotFoundError:
        print(f"Error: Decklist file '{decklist_path}' not found.")
        sys.exit(1)

    # --- 4. Final Output & User Verification ---
    if not parsed_cards:
        print("Warning: No card entries were parsed. The output file will be empty.")
        # Still create an empty file as the process didn't fail validation

    total_entries = len(parsed_cards)
    success_message = f"VALIDATION SUCCESSFUL. Parsed {deck_count} decks, creating a total of {total_entries} validated card entries."
    print(success_message)

    output_df = pd.DataFrame(parsed_cards)
    try:
        output_df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"Successfully saved validated deck data to '{output_path}'.")
    except Exception as e:
        print(f"Error: Failed to save output file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parse_and_validate_decks()
