import pygad
import random
import numpy as np
import time
from typing import List, Dict, Any, Optional, Tuple, Callable, Union
from src.deck_generator import DeckGenerator
from src.evolution import FitnessCalculator
from src.deck_analyzer import DeckAnalyzer
from src.utils.logger import get_logger
from src.utils.error_handler import safe_operation

# Get the logger instance
logger = get_logger()

class GeneticAlgorithm:
    """Manages the genetic algorithm process for evolving Lorcana decks."""

    def __init__(self, deck_generator: DeckGenerator, fitness_calculator: FitnessCalculator, population_size: int, num_generations: int, num_parents_mating: int, on_generation_callback=None, max_turns_per_game: int = 50, progress_callback=None):
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
        self.deck_analyzer = DeckAnalyzer(deck_generator.card_df)
        
        self.population_size = population_size
        self.num_generations = num_generations
        self.num_parents_mating = num_parents_mating
        self.on_generation_callback = on_generation_callback
        self.max_turns_per_game = max_turns_per_game
        
        self.best_solution = None
        self.best_solution_fitness = -1
        self.best_solution_detailed_results = {}
        self.deck_analysis = None
        self.deck_report = None
        
        # Track progress metrics
        self.progress_callback = progress_callback
        self.fitness_history = []
        self.generation_times = []
        self.last_generation_time = None
        self.estimated_time_remaining = None

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
        try:
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
            
                # Fill the rest of the deck to ensure it has exactly 60 cards
                while len(child_deck) < 60:
                    if not valid_card_pool_ids:
                        # Emergency fallback: if the pool is empty, pad with a card from a parent.
                        child_deck.append(parent1[0])
                        continue

                    # Prioritize cards that don't violate the 4-copy rule
                    available_cards = [card for card in valid_card_pool_ids if card_counts.get(card, 0) < 4]
                
                    if available_cards:
                        new_card = random.choice(available_cards)
                        child_deck.append(new_card)
                        card_counts[new_card] = card_counts.get(new_card, 0) + 1
                    else:
                        # If all cards are at the 4-copy limit, we must violate the rule to fill the deck.
                        new_card = random.choice(list(valid_card_pool_ids))
                        child_deck.append(new_card)
            
                # Ensure the deck is exactly 60 cards, truncating if necessary
                final_deck = child_deck[:60]
            
                offspring.append(np.array(final_deck))

            return np.array(offspring)
        except Exception as e:
            logger.error(f"Error in _crossover_func: {e}")
            print(f"[DIAGNOSTIC] Error in _crossover_func: {e}")
            import traceback
            print(f"[DIAGNOSTIC] Traceback: {traceback.format_exc()}")
            # Return empty offspring as fallback
            return np.array([])

    def _mutation_func(self, offspring, ga_instance):
        """
        Custom mutation function to respect deck constraints.
        
        Args:
            offspring (numpy.ndarray): The offspring to be mutated.
            ga_instance (pygad.GA): The GA instance.
            
        Returns:
            numpy.ndarray: The mutated population of offspring.
        """
        try:
            mutated_population = []
            for mutated_individual in offspring:
                mutated_individual = mutated_individual.copy()

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

                # For a small percentage of the deck (~10%), replace cards with others from the valid pool
                for i in range(len(mutated_individual)):
                    if random.random() < self.mutation_rate:
                        mutated_individual[i] = random.choice(valid_card_pool_ids)
            
                mutated_population.append(mutated_individual)
            
            return np.array(mutated_population)
        except Exception as e:
            logger.error(f"Error in _mutation_func: {e}")
            print(f"[DIAGNOSTIC] Error in _mutation_func: {e}")
            import traceback
            print(f"[DIAGNOSTIC] Traceback: {traceback.format_exc()}")  
            # Return unchanged offspring as fallback
            return offspring

    def _fitness_function_wrapper(self, ga_instance, solution, solution_idx):
        """
        A wrapper for the fitness function to be compatible with pygad.
        It stores detailed results for the best solution found.
        """
        # Convert solution (card IDs) to actual card names before fitness calculation
        card_names = [self.deck_generator.id_to_card[gene] for gene in solution]
        
        # Now pass the card names to the fitness calculator
        fitness, detailed_results = self.fitness_calculator.calculate_fitness(
            card_names, self.max_turns_per_game)
        
        # Store detailed results for the best solution (for analysis later)
        if fitness > self.best_solution_fitness:
            self.best_solution = solution
            self.best_solution_fitness = fitness
            self.best_solution_detailed_results = detailed_results
            
        return fitness

    def _on_generation(self, ga_instance):
        """Callback function for on_generation to print progress and notify external listeners."""
        try:
            gen = ga_instance.generations_completed
            best_fitness = ga_instance.best_solution()[1]
            
            # Store fitness for history tracking
            self.fitness_history.append(best_fitness)
            
            # Calculate time per generation for ETA estimates
            current_time = time.time()
            if self.last_generation_time:
                generation_time = current_time - self.last_generation_time
                self.generation_times.append(generation_time)
                
                # Calculate estimated time remaining using a moving average
                if len(self.generation_times) >= 3:  # Need a few data points for a reasonable average
                    window_size = min(5, len(self.generation_times))
                    recent_times = self.generation_times[-window_size:]
                    avg_time_per_gen = sum(recent_times) / window_size
                    gens_remaining = ga_instance.num_generations - gen
                    self.estimated_time_remaining = avg_time_per_gen * gens_remaining
            
            self.last_generation_time = current_time
            
            # Internal logging
            logger.info(f"Generation {gen:3} | Best Fitness = {best_fitness:.4f}")
            print(f"[DIAGNOSTIC] Generation {gen:3} | Best Fitness = {best_fitness:.4f}")

            # External callbacks
            if self.progress_callback:
                progress_data = {
                    'generation': gen,
                    'max_generation': ga_instance.num_generations,
                    'best_fitness': best_fitness,
                    'fitness_history': self.fitness_history.copy(),
                    'estimated_time_remaining': self.estimated_time_remaining
                }
                self.progress_callback(progress_data)
                
            if self.on_generation_callback:
                # Pass the entire instance of this class, not just the pygad instance
                self.on_generation_callback(self)
        except Exception as e:
            logger.error(f"Error in _on_generation: {e}")
            print(f"[DIAGNOSTIC] Error in _on_generation: {e}")
            import traceback
            print(f"[DIAGNOSTIC] Traceback: {traceback.format_exc()}")

    def _on_stop(self, ga_instance, last_population):
        """Callback function called after the genetic algorithm stops."""
        try:
            solution, solution_fitness, solution_idx = ga_instance.best_solution()
            logger.info(f"Best solution found: fitness {solution_fitness:.4f}")
            print(f"[DIAGNOSTIC] Best solution found: fitness {solution_fitness:.4f}")
        except Exception as e:
            logger.error(f"Error in _on_stop: {e}")
            print(f"[DIAGNOSTIC] Error in _on_stop: {e}")
            import traceback
            print(f"[DIAGNOSTIC] Traceback: {traceback.format_exc()}")
    
    @safe_operation(log_level='error')
    def analyze_best_solution(self):
        """
        Analyzes the best solution deck and generates an explanation report.
        """
        if not self.best_solution:
            logger.warning("No best solution available to analyze")
            return None, None
            
        # Generate detailed analysis of the deck
        self.deck_analysis = self.deck_analyzer.analyze_deck(
            self.best_solution, 
            self.best_solution_detailed_results
        )
        
        # Generate a human-readable report
        self.deck_report = self.deck_analyzer.generate_report(
            "Evolved Deck", 
            self.best_solution, 
            self.best_solution_detailed_results
        )
        
        return self.deck_analysis, self.deck_report
    
    def get_deck_report(self):
        """
        Returns the deck analysis report or generates it if not available.
        """
        if not self.deck_report and self.best_solution:
            self.analyze_best_solution()
        return self.deck_report

    def run(self):
        """
        Configures and runs the genetic algorithm evolution process.
        """
        try:
            # Record start time for overall timing stats
            self.start_time = time.time()
            self.last_generation_time = self.start_time
            
            initial_population_lists = [list(deck) for deck in self.initial_population]
            # The gene_space should define the range of possible gene values (card IDs).
            gene_space = range(len(self.deck_generator.unique_card_names))

            # Configure and initialize the GA instance
            logger.info(f"Configuring GA with population size: {self.population_size}, generations: {self.num_generations}")
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
            logger.info("Starting GA evolution process...")
            self.ga_instance.run()

            solution, solution_fitness, solution_idx = self.ga_instance.best_solution()
            self.best_solution = [self.deck_generator.id_to_card[gene] for gene in solution]
            self.best_solution_fitness = solution_fitness
            logger.info(f"GA evolution completed. Best fitness: {solution_fitness:.4f}")
            
            # Generate deck analysis and explanation report
            logger.info("Analyzing best solution...")
            try:
                self.analyze_best_solution()
                logger.info("Analysis complete")
            except Exception as e:
                logger.error(f"Error during best solution analysis: {e}")
                # Continue even if analysis fails
            
            return solution, solution_fitness
        except Exception as e:
            logger.error(f"Critical error in GA run(): {e}")
            # Return a fallback solution to avoid NoneType errors
            fallback_solution = self.initial_population[0] if len(self.initial_population) > 0 else [0] * 60
            return fallback_solution, 0.0
