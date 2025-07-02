import pandas as pd
from typing import List, Dict

# Project-specific imports
from src.game_engine.game_engine import GameState, Player, Deck, Card
from src.game_engine.player_logic import run_main_phase
from src.deck_generator.deck_generator import create_initial_population

CARD_MASTER_PATH = 'data/processed/lorcana_card_master_dataset.csv'
META_DECKS_PATH = 'data/processed/lorcana_metagame_decks.csv'

def load_card_master_dataset() -> pd.DataFrame:
    """Loads the master card dataset."""
    try:
        return pd.read_csv(CARD_MASTER_PATH)
    except FileNotFoundError:
        print(f"Error: Master dataset '{CARD_MASTER_PATH}' not found.")
        return pd.DataFrame()

def load_meta_decks() -> Dict[str, List[str]]:
    """Loads the pillar metagame decks."""
    # This is a placeholder implementation. We will need to parse the CSV correctly.
    print("Note: Meta deck loading is not fully implemented.")
    return {"Amber/Steel Songs": []} # Placeholder

def run_simulation(deck1_ids: List[str], deck2_ids: List[str], card_master_df: pd.DataFrame) -> int:
    """Simulates a single game and returns the winner's player_id."""
    print(f"Simulating a game...\nDeck 1 starts with {len(deck1_ids)} cards. Deck 2 starts with {len(deck2_ids)} cards.")
    # This is a placeholder. Full game loop logic will be added here.
    # For now, we'll just return a random winner to test the structure.
    return 1 # Placeholder

def calculate_fitness(deck_ids: List[str], meta_decks: Dict[str, List[str]], card_master_df: pd.DataFrame) -> float:
    """Calculates the fitness of a single deck by playing it against the meta decks."""
    total_games = 0
    wins = 0

    for meta_deck_name, meta_deck_ids in meta_decks.items():
        # For now, we'll simulate just one game against each meta deck
        # In the future, this should be a statistically significant number (e.g., 100 games)
        
        # We need to implement the logic to create Deck objects from IDs
        # For now, we'll pass the IDs directly to our placeholder simulation
        winner_id = run_simulation(deck_ids, meta_deck_ids, card_master_df)
        if winner_id == 1: # Assuming the generated deck is always player 1
            wins += 1
        total_games += 1

    if total_games == 0:
        return 0.0

    win_rate = wins / total_games
    print(f"Deck fitness (win rate vs meta): {win_rate:.2f}")
    return win_rate

if __name__ == '__main__':
    print("--- Setting up Evolution Environment ---")
    card_master = load_card_master_dataset()
    meta_decks = load_meta_decks()

    if not card_master.empty and meta_decks:
        print("\n--- Generating a sample deck to test fitness calculation ---")
        # Generate one random deck to test the fitness function
        sample_population = create_initial_population(size=1)
        if sample_population:
            test_deck = sample_population[0]
            print(f"\n--- Calculating fitness for the sample deck ---")
            calculate_fitness(test_deck, meta_decks, card_master)
