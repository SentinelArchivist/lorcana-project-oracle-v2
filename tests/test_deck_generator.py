import unittest
import os
import pandas as pd
from src.deck_generator import DeckGenerator

class TestDeckGenerator(unittest.TestCase):
    """Tests the DeckGenerator class."""

    @classmethod
    def setUpClass(cls):
        """Set up for the tests, run once per class."""
        dataset_path = 'data/processed/lorcana_card_master_dataset.csv'
        # Ensure the dataset exists before running tests
        if not os.path.exists(dataset_path):
            raise FileNotFoundError(f"Dataset not found at {dataset_path}")
        cls.generator = DeckGenerator(dataset_path)
        cls.card_pool = pd.read_csv(dataset_path)

    def test_generator_initialization(self):
        """Tests that the DeckGenerator initializes correctly."""
        self.assertIsNotNone(self.generator, "Generator should not be None")

    def test_generate_deck_has_60_cards(self):
        """Tests that a generated deck has exactly 60 cards."""
        deck = self.generator.generate_deck()
        self.assertEqual(len(deck), 60, "Deck should contain exactly 60 cards.")

    def test_generate_deck_has_max_4_copies(self):
        """Tests that no card appears more than 4 times in a deck."""
        deck = self.generator.generate_deck()
        card_counts = {card: deck.count(card) for card in set(deck)}
        for card, count in card_counts.items():
            self.assertLessEqual(count, 4, f"Card '{card}' appears more than 4 times.")

    def test_generate_deck_has_exactly_two_inks(self):
        """Tests that the deck uses exactly two ink colors, plus colorless."""
        deck = self.generator.generate_deck()
        card_details = self.card_pool[self.card_pool['Name'].isin(deck)]
        
        found_inks = set()
        for color_str in card_details['Color'].dropna():
            found_inks.update(color_str.split(', '))
            
        self.assertEqual(len(found_inks), 2, f"Deck should have exactly 2 ink colors, but found {len(found_inks)}: {found_inks}")

    def test_generate_initial_population(self):
        """Tests that a population of unique decks can be generated."""
        num_decks = 5
        population = self.generator.generate_initial_population(num_decks)
        self.assertEqual(len(population), num_decks, f"Should generate {num_decks} decks.")

        # Check that all decks in the population are unique by converting them to hashable types
        unique_decks = {tuple(sorted(deck)) for deck in population}
        self.assertEqual(len(unique_decks), num_decks, "All generated decks in the population should be unique.")

if __name__ == '__main__':
    unittest.main()
