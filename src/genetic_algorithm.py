import pygad
import random
import numpy as np
from src.deck_generator import DeckGenerator
from src.evolution import FitnessCalculator

class GeneticAlgorithm:
    """Manages the genetic algorithm process for evolving Lorcana decks."""

    def __init__(self, deck_generator: DeckGenerator, fitness_calculator: FitnessCalculator, population_size: int, num_generations: int, num_parents_mating: int):
        """
        Initializes the Genetic Algorithm.

        Args:
            deck_generator (DeckGenerator): An instance of the deck generator.
            fitness_calculator (FitnessCalculator): An instance of the fitness calculator.
            population_size (int): The number of decks to generate for the population.
            num_generations (int): The number of generations to run the evolution for.
            num_parents_mating (int): The number of parents to select for mating.
        """
        self.deck_generator = deck_generator
        self.fitness_calculator = fitness_calculator
        self.population_size = population_size
        self.num_generations = num_generations
        self.num_parents_mating = num_parents_mating
        self.best_solution = None
        self.best_solution_fitness = -1

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
            offspring_size (tuple): The size of the offspring to be produced.
            ga_instance: The pygad.GA instance (unused, but required by the API).

        Returns:
            list: A list containing the new offspring (deck of card IDs).
        """
        parent1 = parents[0]
        parent2 = parents[1]

        child_inks = tuple(sorted(self.deck_generator.get_deck_inks(parent1)))
        valid_card_names = self.deck_generator.ink_pair_card_lists.get(child_inks, [])
        if not valid_card_names:
            return parent1.copy()
        
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

        return np.array(child_deck)

    def _mutation_func(self, offspring, ga_instance):
        """
        Custom mutation function for pygad.
        It swaps one card in the deck for another from the valid pool,
        ensuring the 2-ink and 4-copy rules are maintained.

        Args:
            offspring (list): The offspring (deck of card IDs) to be mutated.
            ga_instance: The pygad.GA instance.

        Returns:
            list: The mutated offspring (deck of card IDs).
        """
        mutated_offspring = offspring.copy()
        offspring_inks = tuple(sorted(self.deck_generator.get_deck_inks(mutated_offspring)))
        valid_card_names = self.deck_generator.ink_pair_card_lists.get(offspring_inks, [])
        if not valid_card_names:
            return mutated_offspring
        
        valid_card_pool_ids = [self.deck_generator.card_to_id[name] for name in valid_card_names]

        max_attempts = 100
        for _ in range(max_attempts):
            idx_to_replace = random.randrange(len(mutated_offspring))
            new_card = random.choice(valid_card_pool_ids)

            if new_card != mutated_offspring[idx_to_replace] and mutated_offspring.tolist().count(new_card) < 4:
                mutated_offspring[idx_to_replace] = new_card
                return mutated_offspring

        return offspring

    def _fitness_function_wrapper(self, ga_instance, solution, solution_idx):
        """
        A wrapper for the fitness function to be compatible with pygad.

        Args:
            ga_instance: The pygad instance (unused, but required by the library).
            solution (list[int]): The deck (chromosome of card IDs) to be evaluated.
            solution_idx (int): The index of the solution in the population.

        Returns:
            float: The fitness value of the solution.
        """
        deck_names = [self.deck_generator.id_to_card[gene] for gene in solution]
        return self.fitness_calculator.calculate_fitness(deck_names)

    def _on_generation(self, ga_instance):
        """Callback function for on_generation to print progress."""
        print(f"Generation {ga_instance.generations_completed:3} | Best Fitness = {ga_instance.best_solution()[1]:.4f}")

    def _on_stop(self, ga_instance, last_fitness_values):
        """Callback function for on_stop."""
        print("Evolution stopped.")

    def run(self):
        """
        Configures and runs the genetic algorithm evolution process.
        """
        initial_population_lists = [list(deck) for deck in self.initial_population]
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
