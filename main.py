import time
from src.deck_generator import DeckGenerator
from src.evolution import FitnessCalculator
from src.genetic_algorithm import GeneticAlgorithm

# --- Constants ---
CARD_DATASET_PATH = 'data/processed/lorcana_card_master_dataset.csv'
POPULATION_SIZE = 50
NUM_GENERATIONS = 100
NUM_PARENTS_MATING = 10
NUM_META_DECKS = 10

def main():
    """
    Main function to run the Lorcana deck evolution process.
    """
    print("--- Lorcana Deck Evolution Engine ---")
    print("Initializing components...")

    start_time = time.time()

    # 1. Initialize Deck Generator
    try:
        deck_generator = DeckGenerator(card_dataset_path=CARD_DATASET_PATH)
        print(f"Deck Generator initialized with {len(deck_generator.unique_card_names)} unique cards.")
    except FileNotFoundError:
        print(f"ERROR: Card dataset not found at '{CARD_DATASET_PATH}'. Please check the path.")
        return

    # 2. Create Meta Decks for Fitness Evaluation
    print(f"Generating {NUM_META_DECKS} meta decks for fitness evaluation...")
    meta_deck_ids = [deck_generator.generate_deck() for _ in range(NUM_META_DECKS)]
    meta_decks_names = [[deck_generator.id_to_card[id] for id in deck] for deck in meta_deck_ids]

    # 3. Initialize Fitness Calculator
    fitness_calculator = FitnessCalculator(
        deck_generator=deck_generator,
        meta_decks=meta_decks_names
    )
    print("Fitness Calculator initialized.")

    # 4. Initialize Genetic Algorithm
    ga = GeneticAlgorithm(
        deck_generator=deck_generator,
        fitness_calculator=fitness_calculator,
        population_size=POPULATION_SIZE,
        num_generations=NUM_GENERATIONS,
        num_parents_mating=NUM_PARENTS_MATING
    )
    print("Genetic Algorithm initialized.")
    print("-" * 20)
    print(f"Starting evolution with population size: {POPULATION_SIZE}, generations: {NUM_GENERATIONS}")

    # 5. Run the Genetic Algorithm
    best_solution, best_fitness = ga.run()

    end_time = time.time()
    print("-" * 20)
    print(f"Evolution finished in {end_time - start_time:.2f} seconds.")
    print("-" * 20)

    # 6. Print the results
    if best_solution:
        print(f"Best solution fitness: {best_fitness:.4f}")
        print("\n--- Best Evolved Deck ---")
        
        card_counts = {}
        for card_name in sorted(best_solution):
            card_counts[card_name] = card_counts.get(card_name, 0) + 1
            
        for card_name, count in card_counts.items():
            print(f"{count}x {card_name}")
            
    else:
        print("No solution was found.")

if __name__ == '__main__':
    main()