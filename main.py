import time
import pandas as pd
import tkinter as tk
from tkinter import scrolledtext, ttk
import threading

from src.deck_generator import DeckGenerator
from src.evolution import FitnessCalculator
from src.genetic_algorithm import GeneticAlgorithm

# --- Constants ---
CARD_DATASET_PATH = 'data/processed/lorcana_card_master_dataset.csv'
META_DECKS_PATH = 'data/processed/lorcana_metagame_decks.csv'
POPULATION_SIZE = 50
NUM_GENERATIONS = 100
NUM_PARENTS_MATING = 10
MAX_TURNS_PER_GAME = 40  # Circuit breaker for each game simulation

def main():
    """
    Main function to create and run the UI.
    """
    root = tk.Tk()
    root.title("Project Oracle")
    root.geometry("900x700")

    # --- UI Elements ---
    main_frame = tk.Frame(root, padx=10, pady=10)
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Top frame for title and stats
    top_frame = tk.Frame(main_frame)
    top_frame.pack(fill=tk.X)
    title_label = tk.Label(top_frame, text="Lorcana Deck Evolution Engine", font=("Helvetica", 16))
    title_label.pack(side=tk.LEFT, anchor=tk.W)

    stats_frame = tk.Frame(main_frame, pady=5)
    stats_frame.pack(fill=tk.X)
    gen_label = tk.Label(stats_frame, text="Generation: 0 / 0")
    gen_label.pack(side=tk.LEFT, padx=(0, 10))
    fitness_label = tk.Label(stats_frame, text="Best Fitness: N/A")
    fitness_label.pack(side=tk.LEFT)

    progress_bar = ttk.Progressbar(main_frame, orient='horizontal', mode='determinate', length=100)
    progress_bar.pack(fill=tk.X, pady=(5, 10))

    # Create notebook (tabbed interface) for displaying different sections
    notebook = ttk.Notebook(main_frame)
    notebook.pack(fill=tk.BOTH, expand=True)
    
    # Tab 1: Evolution Log
    log_frame = ttk.Frame(notebook)
    log_widget = scrolledtext.ScrolledText(log_frame, state=tk.DISABLED, wrap=tk.WORD, height=20)
    log_widget.pack(fill=tk.BOTH, expand=True)
    notebook.add(log_frame, text="Evolution Log")
    
    # Tab 2: Best Deck
    deck_frame = ttk.Frame(notebook)
    best_deck_widget = scrolledtext.ScrolledText(deck_frame, state=tk.DISABLED, wrap=tk.WORD, height=20)
    best_deck_widget.pack(fill=tk.BOTH, expand=True)
    notebook.add(deck_frame, text="Best Deck")
    
    # Tab 3: Deck Analysis
    analysis_frame = ttk.Frame(notebook)
    deck_analysis_widget = scrolledtext.ScrolledText(analysis_frame, state=tk.DISABLED, wrap=tk.WORD, height=20)
    deck_analysis_widget.pack(fill=tk.BOTH, expand=True)
    notebook.add(analysis_frame, text="Deck Analysis")

    # Bottom frame for buttons
    button_frame = tk.Frame(main_frame)
    button_frame.pack(fill=tk.X, pady=(10, 0))
    start_button = tk.Button(button_frame, text="Start Evolution")
    start_button.pack(side=tk.LEFT)
    exit_button = tk.Button(button_frame, text="Exit", command=root.destroy)
    exit_button.pack(side=tk.RIGHT)

    # --- Helper Functions ---
    def log_message(message):
        log_widget.config(state=tk.NORMAL)
        log_widget.insert(tk.END, message + '\n')
        log_widget.config(state=tk.DISABLED)
        log_widget.see(tk.END)

    def update_best_deck_display(deck_list):
        best_deck_widget.config(state=tk.NORMAL)
        best_deck_widget.delete('1.0', tk.END)
        if deck_list:
            card_counts = {}
            for card_name in sorted(deck_list):
                card_counts[card_name] = card_counts.get(card_name, 0) + 1
            for card_name, count in card_counts.items():
                best_deck_widget.insert(tk.END, f"{count}x {card_name}\n")
        best_deck_widget.config(state=tk.DISABLED)
        
    def update_deck_analysis_display(analysis_report):
        deck_analysis_widget.config(state=tk.NORMAL)
        deck_analysis_widget.delete('1.0', tk.END)
        if analysis_report:
            deck_analysis_widget.insert(tk.END, analysis_report)
        deck_analysis_widget.config(state=tk.DISABLED)

    def update_ui(ga_object):
        ga_instance = ga_object.ga_instance
        gen = ga_instance.generations_completed
        max_gen = ga_instance.num_generations
        best_solution, best_fitness, _ = ga_instance.best_solution()

        gen_label.config(text=f"Generation: {gen} / {max_gen}")
        fitness_label.config(text=f"Best Fitness: {best_fitness:.4f}")
        progress_bar['value'] = (gen / max_gen) * 100
        
        # Use the deck_generator from the passed ga_object to map IDs to names
        deck_names = [ga_object.deck_generator.id_to_card[gene] for gene in best_solution]
        update_best_deck_display(deck_names)
        
        # Update deck analysis report if available
        if hasattr(ga_object, 'get_deck_report') and ga_object.best_solution:
            update_deck_analysis_display(ga_object.get_deck_report())

    def handle_generation_update(ga_object):
        # The callback now receives the entire GeneticAlgorithm object
        root.after(0, lambda: update_ui(ga_object))

    # --- Evolution Logic ---
    def run_evolution_task():
        try:
            start_button.config(state=tk.DISABLED)
            log_widget.config(state=tk.NORMAL)
            log_widget.delete('1.0', tk.END)
            log_widget.config(state=tk.DISABLED)

            log_message("--- Lorcana Deck Evolution Engine ---")
            log_message("Initializing components...")
            start_time = time.time()

            deck_generator = DeckGenerator(card_dataset_path=CARD_DATASET_PATH)
            log_message(f"Deck Generator initialized with {len(deck_generator.unique_card_names)} unique cards.")

            log_message(f"Loading meta decks from {META_DECKS_PATH}...")
            try:
                meta_decks_df = pd.read_csv(META_DECKS_PATH)
                # Group by deck name and aggregate card names into a list
                meta_decks_names = meta_decks_df.groupby('Deck_Name')['Card_Name'].apply(list).tolist()
                log_message(f"Successfully loaded {len(meta_decks_names)} meta decks.")
            except FileNotFoundError:
                log_message(f"ERROR: Meta decks file not found at '{META_DECKS_PATH}'. Using an empty list.")
                meta_decks_names = []

            fitness_calculator = FitnessCalculator(deck_generator=deck_generator, meta_decks=meta_decks_names)
            log_message("Fitness Calculator initialized.")

            ga = GeneticAlgorithm(
                deck_generator=deck_generator,
                fitness_calculator=fitness_calculator,
                population_size=POPULATION_SIZE,
                num_generations=NUM_GENERATIONS,
                num_parents_mating=NUM_PARENTS_MATING,
                on_generation_callback=handle_generation_update,
                max_turns_per_game=MAX_TURNS_PER_GAME
            )
            log_message("Genetic Algorithm initialized.")
            log_message(f"Starting evolution for {NUM_GENERATIONS} generations...")

            # This is a blocking call, run in a thread
            best_solution, best_fitness = ga.run()

            end_time = time.time()
            log_message(f"\nEvolution finished in {end_time - start_time:.2f} seconds.")
            log_message(f"Final Best Fitness: {best_fitness:.4f}")

            log_message("\n--- Champion Deck Performance Breakdown ---")
            if ga.best_solution_detailed_results:
                for deck_name, win_rate in ga.best_solution_detailed_results.items():
                    log_message(f"  - vs. {deck_name}: {win_rate:.2%} win rate")
            else:
                log_message("  - Detailed results not available.")
                
            # Generate and display deck analysis
            log_message("\n--- Generating Deck Analysis Report ---")
            update_deck_analysis_display(ga.get_deck_report())
            log_message("Deck analysis report available in the 'Deck Analysis' tab.")
            notebook.select(analysis_frame)  # Switch to analysis tab

        except FileNotFoundError:
            log_message(f"ERROR: Card dataset not found at '{CARD_DATASET_PATH}'.")
        except Exception as e:
            log_message(f"An unexpected error occurred: {e}")
        finally:
            start_button.config(state=tk.NORMAL)

    def start_evolution_thread():
        thread = threading.Thread(target=run_evolution_task, daemon=True)
        thread.start()

    start_button.config(command=start_evolution_thread)
    root.mainloop()

if __name__ == '__main__':
    main()