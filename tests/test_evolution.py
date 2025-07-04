import unittest
import os
import pandas as pd
from src.evolution import FitnessCalculator
from src.deck_generator import DeckGenerator

class TestFitnessCalculator(unittest.TestCase):
    def test_initialization_with_csv_meta_decks(self):
        """Tests that the FitnessCalculator can be initialized with decks from the CSV."""
        meta_decks_path = 'data/processed/lorcana_metagame_decks.csv'
        self.assertTrue(os.path.exists(meta_decks_path), f"Meta decks CSV not found at {meta_decks_path}")
        
        meta_decks_df = pd.read_csv(meta_decks_path)
        meta_decks_list = meta_decks_df.groupby('Deck_Name')['Card_Name'].apply(list).tolist()
        
        try:
            calculator = FitnessCalculator(meta_decks=meta_decks_list, deck_generator=self.deck_generator)
            self.assertIsNotNone(calculator)
            self.assertEqual(len(calculator.meta_decks), len(meta_decks_list))
        except Exception as e:
            self.fail(f"FitnessCalculator initialization failed with CSV meta decks: {e}")

    @classmethod
    def setUpClass(cls):
        """Set up for the tests, run once per class."""
        dataset_path = 'data/processed/lorcana_card_master_dataset.csv'
        if not os.path.exists(dataset_path):
            raise FileNotFoundError(f"Dataset not found at {dataset_path}")
        cls.deck_generator = DeckGenerator(dataset_path)
        cls.meta_decks = cls.deck_generator.generate_initial_population(num_decks=2)
        cls.candidate_deck = cls.deck_generator.generate_deck()

    def setUp(self):
        """Set up for each test."""
        self.calculator = FitnessCalculator(meta_decks=self.meta_decks, deck_generator=self.deck_generator)

    def test_fitness_calculator_initialization(self):
        """Tests that the FitnessCalculator initializes correctly."""
        self.assertIsInstance(self.calculator, FitnessCalculator)
        self.assertEqual(self.calculator.meta_decks, self.meta_decks)
        self.assertIsInstance(self.calculator.deck_generator, DeckGenerator)

    def test_calculate_fitness_win_rate(self):
        """Tests that calculate_fitness correctly computes the win rate."""
        # We can't know the exact win rate, but we can check if it's a valid float between 0 and 1.
        fitness, _ = self.calculator.calculate_fitness(self.candidate_deck)
        self.assertIsInstance(fitness, float)
        self.assertGreaterEqual(fitness, 0.0)
        self.assertLessEqual(fitness, 1.0)

    def test_calculate_fitness_no_meta_decks(self):
        """Tests that fitness is 0 if there are no meta decks."""
        calculator = FitnessCalculator(meta_decks=[], deck_generator=self.deck_generator)
        fitness, _ = calculator.calculate_fitness(self.candidate_deck)
        self.assertEqual(fitness, 0.0)

    def test_simulate_game(self):
        """Tests the full game simulation."""
        winner = self.calculator.simulate_game(self.candidate_deck, self.meta_decks[0], goes_first=True)
        self.assertIn(winner, ["player1", "player2"])

if __name__ == '__main__':
    unittest.main()
