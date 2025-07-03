import pygad
import random
import numpy as np
from src.deck_generator import DeckGenerator
from src.evolution import FitnessCalculator

class GeneticAlgorithm:
    """Manages the genetic algorithm process for evolving Lorcana decks."""

    def __init__(self, deck_generator: DeckGenerator, fitness_calculator: FitnessCalculator, population_size: int, num_generations: int, num_parents_mating: int, on_generation_callback=None, max_turns_per_game: int = 50):
        """
        Initializes the Genetic Algorithm.

        Args:
            deck_generator (DeckGenerator): An instance of the deck generator.
            fitness_calculator (FitnessCalculator): An instance of the fitness calculator.
            population_size (int): The number of decks to generate for the population.
            num_generations (int): The number of generations to run the evolution for.
            num_parents_mating (int): The number of parents to select for mating.
            on_generation_callback (callable, optional): A function to call after each generation. Defaults to None.
        """
        self.deck_generator = deck_generator
        self.fitness_calculator = fitness_calculator
        self.population_size = population_size
        self.num_generations = num_generations
        self.num_parents_mating = num_parents_mating
        self.on_generation_callback = on_generation_callback
        self.max_turns_per_game = max_turns_per_game
        self.best_solution = None
        self.best_solution_fitness = -1
        self.best_solution_detailed_results = {}

        self.initial_population = self.create_initial_population()

    def create_initial_population(self) -> list[list[int]]:
        """
        Creates an initial population of decks.

        Returns:
            list[list[int]]: A list of decks, where each deck is a list of card IDs.
        """
        return self.deck_generator.generate_initial_population(num_decks=self.population_size)

    def _crossover_func(self, parents, offspring_size, ga_instance):
        """
        Custom crossover function for pygad to produce legal Lorcana decks.
        It ensures the offspring respects the 2-ink and 4-copy rules.

        Args:
            parents (list): A list of parent solutions (decks of card IDs).
            offspring_size (tuple): The size of the offspring to be produced (num_offspring, num_genes).
            ga_instance: The pygad.GA instance (unused, but required by the API).

        Returns:
            numpy.ndarray: An array of the new offspring, shape (num_offspring, 60).
        """
        offspring = []
        for _ in range(offspring_size[0]):
            parent1, parent2 = parents[random.randint(0, len(parents) - 1)], parents[random.randint(0, len(parents) - 1)]

            child_inks = tuple(sorted(self.deck_generator.get_deck_inks(parent1)))
            valid_card_names = self.deck_generator.ink_pair_card_lists.get(child_inks, [])
            if not valid_card_names:
                offspring.append(parent1.copy())
                continue

            valid_card_pool_ids = {self.deck_generator.card_to_id[name] for name in valid_card_names}
            parent_pool = [gene for gene in (parent1.tolist() + parent2.tolist()) if gene in valid_card_pool_ids]
            random.shuffle(parent_pool)

            child_deck = []
            card_counts = {}
            for gene in parent_pool:
                if len(child_deck) >= 60:
                    break
                if card_counts.get(gene, 0) < 4:
                    child_deck.append(gene)
                    card_counts[gene] = card_counts.get(gene, 0) + 1
            
            valid_card_pool_list = list(valid_card_pool_ids)
            while len(child_deck) < 60:
                if not valid_card_pool_list:
                    break
                new_card = random.choice(valid_card_pool_list)
                if card_counts.get(new_card, 0) < 4:
                    child_deck.append(new_card)
                    card_counts[new_card] = card_counts.get(new_card, 0) + 1
            
            offspring.append(np.array(child_deck))

        return np.array(offspring)

    def _mutation_func(self, offspring, ga_instance):
        """
        Custom mutation function for pygad. It iterates through each offspring (deck)
        in the population and applies a mutation to it, ensuring the 2-ink and
        4-copy rules are maintained.

        Args:
            offspring (numpy.ndarray): The population of offspring solutions (2D array).
            ga_instance: The pygad.GA instance.

        Returns:
            numpy.ndarray: The mutated population of offspring.
        """
        mutated_population = []
        for individual_offspring in offspring:
            mutated_individual = individual_offspring.copy()

            # The individual_offspring is a 1D numpy array, which get_deck_inks can handle
            offspring_inks = tuple(sorted(self.deck_generator.get_deck_inks(mutated_individual)))
            
            valid_card_names = self.deck_generator.ink_pair_card_lists.get(offspring_inks, [])
            if not valid_card_names:
                mutated_population.append(mutated_individual)
                continue
            
            valid_card_pool_ids = [self.deck_generator.card_to_id[name] for name in valid_card_names]
            if not valid_card_pool_ids:
                mutated_population.append(mutated_individual)
                continue

            # Attempt to mutate one gene
            max_attempts = 100
            for _ in range(max_attempts):
                idx_to_replace = random.randrange(len(mutated_individual))
                new_card = random.choice(valid_card_pool_ids)

                # Use numpy for efficient counting in a numpy array
                if new_card != mutated_individual[idx_to_replace] and np.count_nonzero(mutated_individual == new_card) < 4:
                    mutated_individual[idx_to_replace] = new_card
                    break  # Exit after one successful mutation
            
            mutated_population.append(mutated_individual)

        return np.array(mutated_population)

    def _fitness_function_wrapper(self, ga_instance, solution, solution_idx):
        """
        A wrapper for the fitness function to be compatible with pygad.
        It stores detailed results for the best solution found.
        """
        deck_names = [self.deck_generator.id_to_card[gene] for gene in solution]
        fitness, detailed_results = self.fitness_calculator.calculate_fitness(
            deck_names, max_turns=self.max_turns_per_game
        )

        # The best_solution attribute is a tuple of (solution, fitness, idx).
        # It's only updated after a generation, so this check is against the last gen's best.
        # This is sufficient for our purpose of capturing the detailed results for the new best.
        current_best_fitness = -1
        if ga_instance.best_solution_generation != -1:
            current_best_fitness = ga_instance.best_solution()[1]

        if fitness > current_best_fitness:
            self.best_solution_detailed_results = detailed_results

        return fitness

    def _on_generation(self, ga_instance):
        """Callback function for on_generation to print progress and notify external listeners."""
        # Internal logging
        print(f"Generation {ga_instance.generations_completed:3} | Best Fitness = {ga_instance.best_solution()[1]:.4f}")

        # External callback
        if self.on_generation_callback:
            # Pass the entire instance of this class, not just the pygad instance
            self.on_generation_callback(self)

    def _on_stop(self, ga_instance, last_fitness_values):
        """Callback function for on_stop."""
        print("Evolution stopped.")

    def run(self):
        """
        Configures and runs the genetic algorithm evolution process.
        """
        initial_population_lists = [list(deck) for deck in self.initial_population]
        # The gene_space should define the range of possible gene values (card IDs).
        gene_space = range(len(self.deck_generator.unique_card_names))

        ga_instance = pygad.GA(
            num_generations=self.num_generations,
            num_parents_mating=self.num_parents_mating,
            initial_population=initial_population_lists,
            fitness_func=self._fitness_function_wrapper,
            crossover_type=self._crossover_func,
            mutation_type=self._mutation_func,
            on_generation=self._on_generation,
            on_stop=self._on_stop,
            gene_space=gene_space,
            gene_type=int,
            allow_duplicate_genes=True,
            stop_criteria="saturate_3"
        )

        self.ga_instance = ga_instance
        self.ga_instance.run()

        solution, solution_fitness, solution_idx = self.ga_instance.best_solution()
        self.best_solution = [self.deck_generator.id_to_card[gene] for gene in solution]
        self.best_solution_fitness = solution_fitness

        return self.best_solution, self.best_solution_fitness
