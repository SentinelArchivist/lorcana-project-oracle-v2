import cProfile
import pstats
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.deck_generator import DeckGenerator
from src.evolution import FitnessCalculator

def main():
    """Sets up and runs a single game simulation under the profiler."""
    print("Initializing components...")
    # Initialize DeckGenerator
    deck_generator = DeckGenerator()

    # Define two simple decks for the simulation
    deck1 = ['Aladdin, Cornered Swordsman'] * 30 + ['Elsa, Queen Regent'] * 30
    deck2 = ['Beast, Hardheaded'] * 30 + ['Cruella De Vil, Miserable as Usual'] * 30

    # Initialize FitnessCalculator with one of the decks as a placeholder "meta" deck
    fitness_calculator = FitnessCalculator(meta_decks=[deck2], deck_generator=deck_generator)

    # Set up the profiler
    profiler = cProfile.Profile()

    print("Starting profiled simulation...")
    # Run the simulation under the profiler
    profiler.enable()
    fitness_calculator.simulate_game(deck1, deck2, goes_first=True, max_turns=50)
    profiler.disable()
    print("Simulation finished.")

    # Print the stats
    stats = pstats.Stats(profiler).sort_stats('cumulative')
    print("\n--- Profiling Results ---")
    stats.print_stats(30)  # Print the top 30 most time-consuming functions

if __name__ == "__main__":
    main()
