import unittest
import os
import pandas as pd
from collections import Counter

# This assumes the tests are run from the project root directory.
# e.g., python -m unittest discover tests
from src.deck_generator import DeckGenerator

class TestDeckGenerator(unittest.TestCase):
    """Tests the DeckGenerator class."""

    @classmethod
    def setUpClass(cls):
        """Set up for the tests, run once per class."""
        # Construct a robust path to the dataset
        dir_path = os.path.dirname(os.path.realpath(__file__))
        dataset_path = os.path.join(dir_path, '..', 'data', 'processed', 'lorcana_card_master_dataset.csv')
        
        if not os.path.exists(dataset_path):
            raise FileNotFoundError(f"Dataset not found at {dataset_path}. Please run the data processing scripts first.")
        
        cls.generator = DeckGenerator(dataset_path)

    def test_generator_initialization(self):
        """Tests that the DeckGenerator initializes correctly."""
        self.assertIsNotNone(self.generator, "Generator should not be None")
        self.assertGreater(len(self.generator.unique_card_names), 0, "Card pool should not be empty.")

    def test_generate_deck_has_60_cards(self):
        """Tests that a generated deck has exactly 60 cards."""
        deck = self.generator.generate_deck()
        self.assertEqual(len(deck), 60, "Deck should contain exactly 60 cards.")

    def test_generate_deck_has_max_4_copies(self):
        """Tests that no card appears more than 4 times in a deck."""
        deck_ids = self.generator.generate_deck()
        card_counts = Counter(deck_ids)
        for card_id, count in card_counts.items():
            card_name = self.generator.id_to_card.get(card_id, "Unknown ID")
            self.assertLessEqual(count, 4, f"Card '{card_name}' (ID: {card_id}) appears {count} times, more than the allowed 4.")

    def test_generate_deck_has_exactly_two_inks(self):
        """Tests that the deck uses exactly two ink colors, plus colorless."""
        deck_ids = self.generator.generate_deck()
        inks = self.generator.get_deck_inks(deck_ids)
        self.assertEqual(len(inks), 2, f"Deck should have exactly 2 ink colors, but found {len(inks)}: {inks}")

    def test_get_deck_inks_returns_hashable_tuple(self):
        """
        CRITICAL: Verifies the fix for the 'unhashable type: numpy.ndarray' bug.
        Ensures the deck's ink set is returned as a hashable tuple.
        """
        deck_ids = self.generator.generate_deck()
        inks = self.generator.get_deck_inks(deck_ids)
        self.assertIsInstance(inks, tuple, "Deck inks should be a tuple to be hashable.")
        # Check if it's actually hashable by using it as a dictionary key
        try:
            {inks: "is_hashable"}
        except TypeError:
            self.fail("get_deck_inks() returned a non-hashable type.")

    def test_generate_initial_population(self):
        """Tests that a population of unique decks can be generated."""
        num_decks = 10
        population = self.generator.generate_initial_population(num_decks)
        self.assertEqual(len(population), num_decks, f"Should generate {num_decks} decks.")

        # Check that all decks in the population are unique by converting them to hashable types
        unique_decks = {tuple(sorted(deck)) for deck in population}
        self.assertEqual(len(unique_decks), num_decks, "All generated decks in the population should be unique.")

if __name__ == '__main__':
    unittest.main()
