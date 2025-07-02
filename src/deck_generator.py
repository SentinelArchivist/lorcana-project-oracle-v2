import pandas as pd
import random

class DeckGenerator:
    """Generates legal Lorcana decks based on a master card dataset."""

    def __init__(self, card_dataset_path: str):
        """Initializes the generator with the path to the card data."""
        card_pool = pd.read_csv(card_dataset_path)
        # Filter for cards that are part of the main game
        card_pool = card_pool[card_pool['Set_Name'] != 'Lorcana TCG Quick Start Decks']

        # Separate colorless cards first
        self.colorless_cards = list(card_pool[card_pool['Color'].isna()]['Name'].unique())

        # Now, filter for inkable, colored cards
        inkable_cards = card_pool[(card_pool['Inkable'] == True) & (card_pool['Color'].notna())].copy()

        # Define the canonical ink colors
        self.ink_colors = ['Amber', 'Amethyst', 'Emerald', 'Ruby', 'Sapphire', 'Steel']
        
        # Create a map of card names to their set of colors for efficient lookup
        self.inkable_card_colors = {}
        for _, row in inkable_cards.iterrows():
            card_name = row['Name']
            card_colors = set(str(row['Color']).split(', '))
            self.inkable_card_colors[card_name] = card_colors

    def generate_deck(self) -> list[str]:
        """Generates a single, legal, 60-card deck from pre-processed lists."""
        if len(self.ink_colors) < 2:
            raise ValueError("Not enough ink colors in the dataset to generate a deck.")

        while True:
            # 1. Select two random ink colors
            chosen_inks = random.sample(self.ink_colors, 2)
            chosen_inks_set = set(chosen_inks)

            # 2. Create a pool of eligible cards whose colors are a subset of the chosen inks
            eligible_unique_cards = []
            for card_name, color_set in self.inkable_card_colors.items():
                if color_set.issubset(chosen_inks_set):
                    eligible_unique_cards.append(card_name)
            
            # Add colorless cards to the pool
            eligible_unique_cards.extend(self.colorless_cards)

            # 3. Check if we have enough unique cards to form a deck (15 * 4 = 60)
            if len(eligible_unique_cards) >= 15:
                break  # Found a valid pair, exit the loop

        # 4. Build the final deck
        card_pool = []
        for card in eligible_unique_cards:
            card_pool.extend([card] * 4)

        # 5. Shuffle the pool and take the first 60 cards
        random.shuffle(card_pool)
        return card_pool[:60]

    def generate_initial_population(self, num_decks: int) -> list[list[str]]:
        """Generates a population of unique decks."""
        population = set()
        # Add a safeguard against infinite loops if the variety of possible decks is low
        max_attempts = num_decks * 10
        attempts = 0
        while len(population) < num_decks and attempts < max_attempts:
            deck = self.generate_deck()
            population.add(tuple(sorted(deck)))
            attempts += 1
        
        if len(population) < num_decks:
            print(f"Warning: Could only generate {len(population)} unique decks out of {num_decks} requested.")

        return [list(deck) for deck in population]
