import unittest
from src.deck_generator import DeckGenerator
from src.evolution import FitnessCalculator
from src.genetic_algorithm import GeneticAlgorithm

class TestGAIntegration(unittest.TestCase):
    def test_ga_run_does_not_crash(self):
        """
        Integration test to ensure the full GA run completes without crashing.
        This replicates the setup from main.py to isolate the backend error.
        """
        # --- Constants for the test (scaled up to match main.py) ---
        CARD_DATASET_PATH = 'data/processed/lorcana_card_master_dataset.csv'
        POPULATION_SIZE = 50
        NUM_GENERATIONS = 10  # Keep this reasonably low to avoid long test runs
        NUM_PARENTS_MATING = 10
        NUM_META_DECKS = 10
        MAX_TURNS_PER_GAME = 40

        print("\n--- Running GA Integration Test (Increased Scale) ---")
        try:
            # 1. Initialize components
            print("Initializing components...")
            deck_generator = DeckGenerator(card_dataset_path=CARD_DATASET_PATH)
            meta_deck_ids = [deck_generator.generate_deck() for _ in range(NUM_META_DECKS)]
            meta_decks_names = [[deck_generator.id_to_card[id] for id in deck] for deck in meta_deck_ids]
            fitness_calculator = FitnessCalculator(deck_generator=deck_generator, meta_decks=meta_decks_names)
            print("Components initialized.")

            # 2. Initialize the Genetic Algorithm
            print("Initializing Genetic Algorithm...")
            ga = GeneticAlgorithm(
                deck_generator=deck_generator,
                fitness_calculator=fitness_calculator,
                population_size=POPULATION_SIZE,
                num_generations=NUM_GENERATIONS,
                num_parents_mating=NUM_PARENTS_MATING,
                max_turns_per_game=MAX_TURNS_PER_GAME
            )
            print("GA initialized.")

            # 3. Run the evolution
            print(f"Starting evolution for {NUM_GENERATIONS} generations...")
            best_solution, best_fitness = ga.run()
            print("Evolution finished.")

            # 4. Assertions
            print(f"Best solution fitness: {best_fitness:.4f}")
            self.assertIsNotNone(best_solution)
            self.assertIsInstance(best_solution, list)
            self.assertEqual(len(best_solution), 60)
            self.assertGreaterEqual(best_fitness, 0)

        except Exception as e:
            self.fail(f"GA run failed with an unexpected exception: {e}")

if __name__ == '__main__':
    unittest.main()
