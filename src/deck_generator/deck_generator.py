import pandas as pd
import random
from typing import List, Dict

DATASET_PATH = 'data/processed/lorcana_card_master_dataset.csv'

def generate_random_deck(card_pool: pd.DataFrame, ink_colors: List[str]) -> List[str]:
    """Generates a single random, legal deck from a given card pool and ink colors."""
    deck = []
    deck_card_counts: Dict[str, int] = {}

    # Filter the card pool to only include the selected ink colors and colorless cards
    allowed_cards = card_pool[card_pool['Color'].isin(ink_colors + ['Colorless'])].copy()

    # Ensure we have cards to choose from
    if allowed_cards.empty:
        return []

    while len(deck) < 60:
        # Select a random card from the allowed pool
        random_card = allowed_cards.sample(n=1).iloc[0]
        card_id = random_card['Unique_ID']

        # Respect the 4-copy limit
        if deck_card_counts.get(card_id, 0) < 4:
            deck.append(card_id)
            deck_card_counts[card_id] = deck_card_counts.get(card_id, 0) + 1
        
    return deck

def create_initial_population(size: int) -> List[List[str]]:
    """Creates an initial population of random, legal decks."""
    try:
        df = pd.read_csv(DATASET_PATH)
    except FileNotFoundError:
        print(f"Error: Master dataset '{DATASET_PATH}' not found.")
        return []

    # Get all possible ink colors from the dataset
    all_inks = df[df['Color'] != 'Colorless']['Color'].unique().tolist()
    population = []

    print(f"Generating initial population of {size} decks...")
    while len(population) < size:
        # Choose 2 random, distinct ink colors for the deck
        chosen_inks = random.sample(all_inks, 2)
        
        new_deck = generate_random_deck(df, chosen_inks)
        if new_deck:
            population.append(new_deck)
            print(f"  Generated deck #{len(population)} with inks: {', '.join(chosen_inks)}")

    return population

if __name__ == '__main__':
    # Example of how to use the generator
    initial_population = create_initial_population(size=10)
    if initial_population:
        print(f"\nSuccessfully generated {len(initial_population)} decks.")
        print("First deck's card count:", len(initial_population[0]))
        print("First deck's first 5 card IDs:", initial_population[0][:5])
