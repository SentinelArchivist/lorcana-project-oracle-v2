import pandas as pd
import re
import sys

def parse_and_validate_decks(master_dataset_path: str, decklist_path: str, output_path: str) -> pd.DataFrame:
    """
    Parses a local decklist file, validates every card against the master dataset,
    and outputs a single, validated CSV file.

    Args:
        master_dataset_path: Path to the master card dataset CSV.
        decklist_path: Path to the raw decklist markdown file.
        output_path: Path to save the validated output CSV.

    Returns:
        A pandas DataFrame containing the validated deck data.

    Raises:
        FileNotFoundError: If the master dataset or decklist file is not found.
        ValueError: If a card in the decklist is not found in the master dataset.
    """
    # --- 1. Load Master Card Data & Create Validation Set ---
    try:
        master_df = pd.read_csv(master_dataset_path)
        master_card_names = set(master_df['Name'])
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Master dataset not found at {master_dataset_path}") from e

    # --- 2. Parse Decklist File ---
    parsed_cards = []
    current_deck_name = None

    try:
        with open(decklist_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                deck_match = re.match(r'^#\s*\[Set\s*\d+\]\s*(.*)', line)
                if deck_match:
                    current_deck_name = deck_match.group(1).strip()
                    continue

                card_match = re.match(r'^(\d+)\s+(.*)', line)
                if card_match and current_deck_name:
                    quantity = int(card_match.group(1))
                    card_name = card_match.group(2).strip()

                    # --- 3. CRUCIAL: Non-Negotiable Data Validation ---
                    if card_name not in master_card_names:
                        raise ValueError(
                            f"Validation Failed: Card '{card_name}' from deck '{current_deck_name}' "
                            f"not found in the master dataset."
                        )

                    parsed_cards.append({
                        'DeckName': current_deck_name,
                        'CardName': card_name,
                        'Quantity': quantity
                    })

    except FileNotFoundError as e:
        raise FileNotFoundError(f"Decklist file not found at {decklist_path}") from e

    # --- 4. Final Output ---
    output_df = pd.DataFrame(parsed_cards)
    try:
        output_df.to_csv(output_path, index=False, encoding='utf-8')
    except IOError as e:
        raise RuntimeError(f"Failed to save output file to {output_path}: {e}") from e

    return output_df

if __name__ == "__main__":
    MASTER_DATASET = 'data/processed/lorcana_card_master_dataset.csv'
    DECKLIST = 'data/raw/2025.07.01-meta-decks.md'
    OUTPUT_CSV = 'data/processed/lorcana_metagame_decks.csv'

    print("Starting decklist parsing and validation...")
    try:
        validated_df = parse_and_validate_decks(MASTER_DATASET, DECKLIST, OUTPUT_CSV)
        print(f"VALIDATION SUCCESSFUL. Parsed and validated {len(validated_df)} card entries.")
        print(f"Validated deck data saved to '{OUTPUT_CSV}'.")
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

