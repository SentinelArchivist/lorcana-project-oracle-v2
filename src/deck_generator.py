import pandas as pd
import random
import itertools
import os

class DeckGenerator:
    """Generates legal Lorcana decks based on a master card dataset."""

    def __init__(self, card_dataset_path: str = 'data/processed/lorcana_card_master_dataset.csv'):
        """Initializes the generator with the path to the card data."""
        # If the default path is used, construct an absolute path to be robust
        if card_dataset_path == 'data/processed/lorcana_card_master_dataset.csv':
            script_dir = os.path.dirname(__file__)
            project_root = os.path.abspath(os.path.join(script_dir, '..'))
            card_dataset_path = os.path.join(project_root, 'data', 'processed', 'lorcana_card_master_dataset.csv')

        card_pool = pd.read_csv(card_dataset_path)
        card_pool = card_pool[card_pool['Set_Name'] != 'Lorcana TCG Quick Start Decks']
        self.card_df = card_pool

        # Create card <-> ID mappings
        self.unique_card_names = sorted(list(self.card_df['Name'].unique()))
        self.card_to_id = {name: i for i, name in enumerate(self.unique_card_names)}
        self.id_to_card = {i: name for i, name in enumerate(self.unique_card_names)}

        self.colorless_cards = list(card_pool[card_pool['Color'].isna()]['Name'].unique())
        inkable_cards = card_pool[(card_pool['Inkable'] == True) & (card_pool['Color'].notna())].copy()
        self.ink_colors = ['Amber', 'Amethyst', 'Emerald', 'Ruby', 'Sapphire', 'Steel']
        
        self.inkable_card_colors = {}
        for _, row in inkable_cards.iterrows():
            card_name = row['Name']
            card_colors = set(str(row['Color']).split(', '))
            self.inkable_card_colors[card_name] = card_colors

        self.ink_pair_card_lists = {}
        for ink1, ink2 in itertools.combinations(self.ink_colors, 2):
            ink_pair = tuple(sorted((ink1, ink2)))
            ink_pair_set = set(ink_pair)
            eligible_cards = []
            for card_name, color_set in self.inkable_card_colors.items():
                if color_set.issubset(ink_pair_set):
                    eligible_cards.append(card_name)
            eligible_cards.extend(self.colorless_cards)
            self.ink_pair_card_lists[ink_pair] = eligible_cards

        self._memo_get_deck_inks = {}

    def generate_deck(self) -> list[int]:
        """Generates a single, legal, 60-card deck represented by card IDs."""
        if not self.ink_pair_card_lists:
            raise ValueError("Not enough ink combinations to generate a deck.")

        while True:
            chosen_inks_pair = random.choice(list(self.ink_pair_card_lists.keys()))
            eligible_unique_cards = self.ink_pair_card_lists[chosen_inks_pair]
            if len(eligible_unique_cards) >= 15:
                break

        card_pool = []
        for card_name in eligible_unique_cards:
            card_id = self.card_to_id[card_name]
            card_pool.extend([card_id] * 4)

        random.shuffle(card_pool)
        return tuple(sorted(card_pool[:60]))

    def get_deck_inks(self, deck: list[int]) -> tuple[str, ...]:
        """Determines the tuple of inks present in a given deck of card IDs."""
        # Convert numpy.ndarray to a hashable tuple for dictionary key usage
        # Force conversion to a tuple of standard Python integers to ensure hashability.
        # This handles lists, tuples, and numpy arrays of various int types.
        deck_tuple = tuple(int(x) for x in deck)
        if deck_tuple in self._memo_get_deck_inks:
            return self._memo_get_deck_inks[deck_tuple]

        deck_names = [self.id_to_card[card_id] for card_id in deck]
        inks = set()
        # Pre-creating this series is faster than repeated lookups inside the loop
        name_to_color = self.card_df.set_index('Name')['Color']
        for card_name in set(deck_names):
            card_colors_lookup = name_to_color.get(card_name)
            # Handle cases where a card might appear multiple times with different data (shouldn't happen with good data)
            if isinstance(card_colors_lookup, pd.Series):
                card_colors = card_colors_lookup.iloc[0]
            else:
                card_colors = card_colors_lookup
            if pd.notna(card_colors):
                for color in str(card_colors).split(', '):
                    if color in self.ink_colors:
                        inks.add(color)

        # Convert to a sorted tuple for consistent hashing and to meet requirements
        result_tuple = tuple(sorted(list(inks)))
        self._memo_get_deck_inks[deck_tuple] = result_tuple
        return result_tuple

    def generate_initial_population(self, num_decks: int) -> list[list[int]]:
        """Generates a population of unique decks represented by card IDs."""
        population = set()
        max_attempts = num_decks * 20
        attempts = 0
        while len(population) < num_decks and attempts < max_attempts:
            deck = self.generate_deck() # Now returns a sorted tuple
            population.add(deck)
            attempts += 1
        
        if len(population) < num_decks:
            print(f"Warning: Could only generate {len(population)} unique decks out of {num_decks} requested.")

        return [list(deck) for deck in population]
