import unittest
from unittest.mock import Mock, patch
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

        # Mock to return a tuple (fitness, detailed_results)
        self.ga.fitness_calculator.calculate_fitness = Mock(return_value=(0.5, {'wins': 1, 'losses': 1}))

        # Mock the ga_instance that pygad would normally pass to the wrapper
        mock_ga_instance = Mock()
        mock_ga_instance.best_solution_generation = -1 # Simulate initial state
        fitness_value = self.ga._fitness_function_wrapper(mock_ga_instance, solution_ids, solution_idx)

        # The wrapper should only care about the deck names
        self.ga.fitness_calculator.calculate_fitness.assert_called_once_with(solution_names, max_turns=self.ga.max_turns_per_game)
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

        # The crossover function returns an array of offspring.
        offspring = self.ga._crossover_func(parents, (1, 60), None) # ga_instance is mocked

        self.assertIsInstance(offspring, np.ndarray)
        self.assertEqual(offspring.shape[0], 1)
        child_deck = offspring[0]

        self.assertEqual(len(child_deck), 60, "Child deck must have 60 cards.")

        # Convert to list for counting
        child_deck_list = child_deck.tolist()
        card_counts = {card: child_deck_list.count(card) for card in set(child_deck_list)}
        for card, count in card_counts.items():
            self.assertLessEqual(count, 4, f"Card ID {card} exceeds the 4-copy limit.")

        inks = self.deck_generator.get_deck_inks(child_deck)
        self.assertEqual(len(inks), 2, "Child deck must have exactly two inks.")

    def test_mutation_maintains_legality(self):
        """Tests that the custom mutation function maintains deck legality."""
        original_deck = np.array(self.deck_generator.generate_deck())

        # The mutation function expects a population (2D array), not a single individual.
        # We pass it as a population of one.
        population = np.array([original_deck])

        mutated_population = self.ga._mutation_func(population, None) # ga_instance is mocked

        self.assertEqual(mutated_population.shape[0], 1)
        mutated_deck_np = mutated_population[0]

        self.assertEqual(len(mutated_deck_np), 60, "Mutated deck must have 60 cards.")

        inks = self.deck_generator.get_deck_inks(mutated_deck_np)
        self.assertEqual(len(inks), 2, "Mutated deck must have exactly two inks.")

        card_counts = {card: mutated_deck_np.tolist().count(card) for card in set(mutated_deck_np.tolist())}
        for card, count in card_counts.items():
            self.assertLessEqual(count, 4, f"Card ID {card} exceeds the 4-copy limit after mutation.")

        original_inks = self.deck_generator.get_deck_inks(original_deck)
        mutated_inks = self.deck_generator.get_deck_inks(mutated_deck_np)
        self.assertEqual(original_inks, mutated_inks, "Mutation must not change the deck's inks.")

    def test_ga_run_completes(self):
        """Tests that the GA can run to completion without errors."""
        # Create a simple mock fitness function that returns a fixed value
        def mock_fitness_function(ga_instance, solution, solution_idx):
            return 0.75
        
        # Save the original function
        original_function = self.ga._fitness_function_wrapper
        
        # Replace with our mock function
        self.ga._fitness_function_wrapper = mock_fitness_function
        
        try:
            # Run with a very small number of generations for testing
            self.ga.num_generations = 1
            best_solution, best_fitness = self.ga.run()
            
            self.assertIsNotNone(best_solution)
            self.assertIsInstance(best_solution, list)
            self.assertEqual(len(best_solution), 60)
            self.assertTrue(all(isinstance(card_name, str) for card_name in best_solution))
            self.assertGreaterEqual(best_fitness, -1)
        except Exception as e:
            self.fail(f"GA run failed with an exception: {e}")
        finally:
            # Restore the original function
            self.ga._fitness_function_wrapper = original_function


if __name__ == '__main__':
    unittest.main()
