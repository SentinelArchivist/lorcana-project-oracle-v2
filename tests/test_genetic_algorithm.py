import unittest
from unittest.mock import Mock
import numpy as np
from src.deck_generator import DeckGenerator
from src.evolution import FitnessCalculator
from src.genetic_algorithm import GeneticAlgorithm

class TestGeneticAlgorithm(unittest.TestCase):
    def setUp(self):
        """Set up the necessary components for testing the genetic algorithm."""
        self.deck_generator = DeckGenerator(card_dataset_path='data/processed/lorcana_card_master_dataset.csv')
        
        # Meta decks for fitness calculator should be lists of card names
        meta_deck_ids = [self.deck_generator.generate_deck() for _ in range(3)]
        meta_decks_names = [[self.deck_generator.id_to_card[id] for id in deck] for deck in meta_deck_ids]
        
        self.fitness_calculator = FitnessCalculator(
            deck_generator=self.deck_generator,
            meta_decks=meta_decks_names
        )
        self.ga = GeneticAlgorithm(
            deck_generator=self.deck_generator,
            fitness_calculator=self.fitness_calculator,
            population_size=10,
            num_generations=5, # A few generations to test the run
            num_parents_mating=2
        )

    def test_ga_initialization(self):
        """Tests that the GeneticAlgorithm class initializes correctly."""
        self.assertIsNotNone(self.ga)
        self.assertEqual(self.ga.deck_generator, self.deck_generator)
        self.assertEqual(self.ga.fitness_calculator, self.fitness_calculator)

    def test_fitness_function_wrapper(self):
        """Tests the fitness function wrapper for pygad."""
        solution_ids = self.deck_generator.generate_deck()
        solution_names = [self.deck_generator.id_to_card[id] for id in solution_ids]
        solution_idx = 0

        self.ga.fitness_calculator.calculate_fitness = Mock(return_value=0.5)

        fitness_value = self.ga._fitness_function_wrapper(None, solution_ids, solution_idx)

        self.ga.fitness_calculator.calculate_fitness.assert_called_once_with(solution_names)
        self.assertEqual(fitness_value, 0.5)

    def test_initial_population_is_created(self):
        """Tests that the initial population is created correctly during initialization."""
        self.assertIsNotNone(self.ga.initial_population)
        self.assertEqual(len(self.ga.initial_population), 10)
        for deck in self.ga.initial_population:
            self.assertIsInstance(deck, list)
            self.assertEqual(len(deck), 60)
            self.assertTrue(all(isinstance(card_id, int) for card_id in deck))

    def test_crossover_produces_legal_deck(self):
        """Tests that the custom crossover function produces a legal deck of card IDs."""
        parent1 = np.array(self.deck_generator.generate_deck())
        parent2 = np.array(self.deck_generator.generate_deck())
        parents = np.vstack([parent1, parent2])

        child_deck = self.ga._crossover_func(parents, (1, 60), None) # ga_instance is mocked

        self.assertEqual(len(child_deck), 60, "Child deck must have 60 cards.")

        card_counts = {card: child_deck.count(card) for card in set(child_deck)}
        for card, count in card_counts.items():
            self.assertLessEqual(count, 4, f"Card ID {card} exceeds the 4-copy limit.")

        inks = self.deck_generator.get_deck_inks(child_deck)
        self.assertEqual(len(inks), 2, "Child deck must have exactly two inks.")

    def test_mutation_produces_legal_deck(self):
        """Tests that the custom mutation function produces a legal deck of card IDs."""
        original_deck = np.array(self.deck_generator.generate_deck())
        original_inks = self.deck_generator.get_deck_inks(original_deck.tolist())

        mutated_deck_np = self.ga._mutation_func(original_deck, 0)
        mutated_deck = mutated_deck_np.tolist()

        # It's possible, though unlikely, that a mutation results in the same deck.
        # A better test is to ensure it's still legal.
        self.assertEqual(len(mutated_deck), 60, "Mutated deck must have 60 cards.")

        card_counts = {card: mutated_deck.count(card) for card in set(mutated_deck)}
        for card, count in card_counts.items():
            self.assertLessEqual(count, 4, f"Card ID {card} exceeds the 4-copy limit after mutation.")

        mutated_inks = self.deck_generator.get_deck_inks(mutated_deck)
        self.assertEqual(original_inks, mutated_inks, "Mutation must not change the deck's inks.")

    def test_ga_run_completes(self):
        """Tests that the GA can run to completion without errors."""
        try:
            best_solution, best_fitness = self.ga.run()
            self.assertIsNotNone(best_solution)
            self.assertIsInstance(best_solution, list)
            self.assertEqual(len(best_solution), 60)
            self.assertTrue(all(isinstance(card_name, str) for card_name in best_solution))
            self.assertGreaterEqual(best_fitness, -1)
        except Exception as e:
            self.fail(f"GA run failed with an exception: {e}")


if __name__ == '__main__':
    unittest.main()
