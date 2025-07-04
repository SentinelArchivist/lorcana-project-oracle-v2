import os
import time
import pandas as pd
import datetime
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from src.deck_generator import DeckGenerator
from src.evolution import FitnessCalculator
from src.genetic_algorithm import GeneticAlgorithm
from src.card_database_manager import CardDatabaseManager
from src.ui_utils import UIManager

# --- Constants ---
CARD_DATASET_PATH = 'data/processed/lorcana_card_master_dataset.csv'
META_DECKS_DIR = 'data/processed/meta_decks'
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
    
    # Initialize UI Manager
    ui_manager = UIManager(root)

    # --- UI Elements ---
    main_frame = tk.Frame(root, padx=10, pady=10)
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Top frame for title and stats
    top_frame = tk.Frame(main_frame)
    top_frame.pack(fill=tk.X)
    title_label = ttk.Label(top_frame, text="Lorcana Deck Evolution Engine", style="Header.TLabel")
    title_label.pack(side=tk.LEFT, anchor=tk.W)

    # Progress and Stats Frame - Using a grid layout for more organized display
    progress_frame = ttk.LabelFrame(main_frame, text="Evolution Progress")
    progress_frame.pack(fill=tk.X, pady=5)
    
    # Setup grid layout
    progress_frame.columnconfigure(0, weight=1)
    progress_frame.columnconfigure(1, weight=1)
    progress_frame.columnconfigure(2, weight=1)
    
    # Row 1: Generation and Fitness
    gen_label = ttk.Label(progress_frame, text="Generation: 0 / 0")
    gen_label.grid(row=0, column=0, sticky="w", padx=5, pady=2)
    
    fitness_label = ttk.Label(progress_frame, text="Best Fitness: N/A")
    fitness_label.grid(row=0, column=1, sticky="w", padx=5, pady=2)
    
    time_label = ttk.Label(progress_frame, text="Time Remaining: N/A")
    time_label.grid(row=0, column=2, sticky="w", padx=5, pady=2)
    
    # Row 2: Progress Bar
    progress_bar = ttk.Progressbar(progress_frame, orient='horizontal', mode='determinate', length=100)
    progress_bar.grid(row=1, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
    
    # Row 3: Progress Details
    progress_details_label = ttk.Label(progress_frame, text="")
    progress_details_label.grid(row=2, column=0, columnspan=3, sticky="w", padx=5, pady=2)
    
    # Row 4: Fitness Graph
    fitness_graph_frame = ttk.Frame(progress_frame)
    fitness_graph_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
    
    # Create a figure for fitness history graph
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.set_title('Fitness History')
    ax.set_xlabel('Generation')
    ax.set_ylabel('Fitness')
    canvas = FigureCanvasTkAgg(fig, master=fitness_graph_frame)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # Create notebook (tabbed interface) for displaying different sections
    notebook = ttk.Notebook(main_frame)
    notebook.pack(fill=tk.BOTH, expand=True)
    
    # Tab 1: Evolution Log
    log_frame = ttk.Frame(notebook)
    log_widget = scrolledtext.ScrolledText(log_frame, state=tk.DISABLED, wrap=tk.WORD, height=20)
    log_widget.pack(fill=tk.BOTH, expand=True)
    notebook.add(log_frame, text="Evolution Log")
    
    # Tab 2: Best Deck - Enhanced with statistics and copy button
    deck_frame = ttk.Frame(notebook)
    
    # Deck header frame
    deck_header_frame = ttk.Frame(deck_frame)
    deck_header_frame.pack(fill=tk.X, padx=5, pady=5)
    
    deck_title_label = ttk.Label(deck_header_frame, text="Evolved Deck", style="Header.TLabel")
    deck_title_label.pack(side=tk.LEFT, anchor=tk.W)
    
    copy_button = ttk.Button(deck_header_frame, text="Copy to Clipboard", command=lambda: copy_deck_to_clipboard())
    copy_button.pack(side=tk.RIGHT, anchor=tk.E, padx=5)
    
    # Stats frame for deck
    deck_stats_frame = ttk.Frame(deck_frame)
    deck_stats_frame.pack(fill=tk.X, padx=5, pady=5)
    
    deck_stats_label = ttk.Label(deck_stats_frame, text="")
    deck_stats_label.pack(side=tk.LEFT, anchor=tk.W)
    
    # Deck content with improved formatting
    deck_content_frame = ttk.Frame(deck_frame)
    deck_content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    best_deck_widget = scrolledtext.ScrolledText(deck_content_frame, state=tk.DISABLED, wrap=tk.WORD, height=20)
    best_deck_widget.pack(fill=tk.BOTH, expand=True)
    
    notebook.add(deck_frame, text="Best Deck")
    
    # Tab 3: Deck Analysis
    analysis_frame = ttk.Frame(notebook)
    deck_analysis_widget = scrolledtext.ScrolledText(analysis_frame, state=tk.DISABLED, wrap=tk.WORD, height=20)
    deck_analysis_widget.pack(fill=tk.BOTH, expand=True)
    notebook.add(analysis_frame, text="Deck Analysis")

    # Bottom frame for buttons and additional controls
    control_frame = tk.Frame(main_frame)
    control_frame.pack(fill=tk.X, pady=10)
    
    # Database management frame (top part of control frame)
    db_frame = tk.LabelFrame(control_frame, text="Database Management")
    db_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
    
    # Meta deck selection
    meta_deck_frame = tk.Frame(db_frame)
    meta_deck_frame.pack(fill=tk.X, padx=5, pady=5)
    meta_deck_label = ttk.Label(meta_deck_frame, text="Meta Decks:")
    meta_deck_label.pack(side=tk.LEFT)
    meta_deck_var = tk.StringVar(value="Latest")
    meta_deck_dropdown = ttk.Combobox(meta_deck_frame, textvariable=meta_deck_var, state="readonly")
    meta_deck_dropdown.pack(side=tk.LEFT, padx=5)
    refresh_meta_button = ttk.Button(meta_deck_frame, text="Refresh", command=lambda: refresh_meta_deck_list())
    refresh_meta_button.pack(side=tk.LEFT, padx=5)
    
    # Add tooltips
    ui_manager.create_tooltip(meta_deck_label, "Select which meta deck file to use for evolution")
    ui_manager.create_tooltip(meta_deck_dropdown, "Choose 'Latest' for the most recent meta deck file, or select a specific file")
    ui_manager.create_tooltip(refresh_meta_button, "Refresh the list of available meta deck files")
    
    # Set rotation controls
    rotation_frame = tk.Frame(db_frame)
    rotation_frame.pack(fill=tk.X, padx=5, pady=5)
    rotation_label = ttk.Label(rotation_frame, text="Set Rotation:")
    rotation_label.pack(side=tk.LEFT)
    rotation_var = tk.BooleanVar(value=False)
    rotation_check = ttk.Checkbutton(rotation_frame, text="Enable", variable=rotation_var)
    rotation_check.pack(side=tk.LEFT, padx=5)
    date_label = ttk.Label(rotation_frame, text="Date:")
    date_label.pack(side=tk.LEFT, padx=(10, 0))
    rotation_date_var = tk.StringVar(value=datetime.date.today().strftime("%Y-%m-%d"))
    rotation_date_entry = ttk.Entry(rotation_frame, textvariable=rotation_date_var, width=10)
    rotation_date_entry.pack(side=tk.LEFT, padx=5)
    
    # Add validation to date entry
    def validate_date_entry(event=None):
        if not ui_manager.validate_date_format(rotation_date_var.get()):
            ui_manager.show_error("Invalid Date", "Please enter a valid date in YYYY-MM-DD format.")
            rotation_date_entry.focus_set()
            return False
        return True
    
    rotation_date_entry.bind("<FocusOut>", validate_date_entry)
    
    # Add tooltips
    ui_manager.create_tooltip(rotation_label, "Enable set rotation to filter cards based on release date")
    ui_manager.create_tooltip(rotation_check, "When enabled, only cards from legal sets will be used")
    ui_manager.create_tooltip(date_label, "Specify the rotation date (YYYY-MM-DD)")
    ui_manager.create_tooltip(rotation_date_entry, "Enter date in YYYY-MM-DD format")
    
    # Button frame
    button_frame = tk.Frame(control_frame)
    button_frame.pack(fill=tk.X, pady=5)
    start_button = ttk.Button(button_frame, text="Start Evolution", style="Primary.TButton", command=start_evolution_thread)
    start_button.pack(side=tk.LEFT, padx=10)
    exit_button = ttk.Button(button_frame, text="Exit", command=root.quit)
    exit_button.pack(side=tk.RIGHT, padx=10)
    
    # Add tooltips
    ui_manager.create_tooltip(start_button, "Begin the deck evolution process")
    ui_manager.create_tooltip(exit_button, "Exit the application")

    # --- Helper Functions ---
    def log_message(message):
        log_widget.config(state=tk.NORMAL)
        log_widget.insert(tk.END, message + '\n')
        log_widget.config(state=tk.DISABLED)
        log_widget.see(tk.END)

    def update_best_deck_display(deck_list, detailed_results=None, ga_stats=None):
        """Update the best deck display with improved formatting and statistics"""
        best_deck_widget.config(state=tk.NORMAL)
        best_deck_widget.delete('1.0', tk.END)
        
        if deck_list:
            # Process the deck list to get card counts
            card_counts = {}
            for card_name in sorted(deck_list):
                card_counts[card_name] = card_counts.get(card_name, 0) + 1
            
            # Group cards by cost (mana curve) for better organization
            cards_by_cost = {}
            costs_info = {}  # To store cost information for each card
            
            # First pass to gather cost information
            try:
                df = pd.read_csv(CARD_DATASET_PATH)
                for card_name in card_counts.keys():
                    card_info = df[df['Card_Name'] == card_name]
                    if not card_info.empty:
                        cost = int(card_info['Ink_Cost'].iloc[0])
                        card_type = card_info['Card_Type'].iloc[0]
                        costs_info[card_name] = {'cost': cost, 'type': card_type}
                        
                        if cost not in cards_by_cost:
                            cards_by_cost[cost] = []
                        cards_by_cost[cost].append(card_name)
            except Exception as e:
                # If we can't load the card data, just use a flat list
                log_message(f"Warning: Could not organize cards by cost: {e}")
                cards_by_cost = {0: list(card_counts.keys())}  # Put all cards in cost 0
            
            # Add a header
            best_deck_widget.insert(tk.END, "=== EVOLVED DECK ===\n\n")
            
            # Format the deck list by mana cost
            if cards_by_cost and any(cost != 0 for cost in cards_by_cost.keys()):
                best_deck_widget.insert(tk.END, "--- By Mana Cost ---\n")
                for cost in sorted(cards_by_cost.keys()):
                    if cost == 0 and not cards_by_cost[cost]:  # Skip empty cost categories
                        continue
                    best_deck_widget.insert(tk.END, f"\n{cost} Ink:\n")
                    for card_name in sorted(cards_by_cost[cost]):
                        count = card_counts[card_name]
                        best_deck_widget.insert(tk.END, f"  {count}x {card_name}\n")
            else:
                # If we couldn't organize by cost, show flat list
                for card_name, count in sorted(card_counts.items()):
                    best_deck_widget.insert(tk.END, f"{count}x {card_name}\n")
            
            # Add a separator
            best_deck_widget.insert(tk.END, "\n----------------------\n")
            
            # Display card type summary if we have the data
            if costs_info:
                card_types = {}
                for card, info in costs_info.items():
                    card_type = info['type']
                    if card_type not in card_types:
                        card_types[card_type] = 0
                    card_types[card_type] += card_counts[card]
                
                best_deck_widget.insert(tk.END, "\n--- Card Types ---\n")
                for card_type, count in sorted(card_types.items()):
                    best_deck_widget.insert(tk.END, f"{card_type}: {count}\n")
            
            # Add a separator before performance data
            best_deck_widget.insert(tk.END, "\n----------------------\n")
            
            # Add performance information if available
            if detailed_results:
                best_deck_widget.insert(tk.END, "\n--- Performance ---\n")
                total_matches = 0
                total_wins = 0
                
                for deck_name, win_rate in sorted(detailed_results.items(), key=lambda x: x[1], reverse=True):
                    # Assuming we simulated 100 games per deck to get win rates
                    matches = 100
                    wins = int(win_rate * matches)
                    total_matches += matches
                    total_wins += wins
                    best_deck_widget.insert(tk.END, f"vs {deck_name}: {win_rate:.1%} ({wins}/{matches})\n")
                
                if total_matches > 0:
                    overall_win_rate = total_wins / total_matches
                    best_deck_widget.insert(tk.END, f"\nOverall: {overall_win_rate:.1%} ({total_wins}/{total_matches})\n")
            
            # Update the deck stats label
            update_deck_stats_label(deck_list, detailed_results, ga_stats)
            
        best_deck_widget.config(state=tk.DISABLED)
        
    def update_deck_stats_label(deck_list, detailed_results=None, ga_stats=None):
        """Update the deck statistics summary"""
        stats_text = []
        
        if deck_list:
            unique_cards = len(set(deck_list))
            total_cards = len(deck_list)
            stats_text.append(f"Cards: {total_cards} total, {unique_cards} unique")
        
        if detailed_results:
            win_rates = list(detailed_results.values())
            avg_win_rate = sum(win_rates) / len(win_rates) if win_rates else 0
            stats_text.append(f"Average Win Rate: {avg_win_rate:.1%}")
        
        if ga_stats:
            stats_text.append(f"Generations: {ga_stats.get('generations', 'N/A')}")
            stats_text.append(f"Final Fitness: {ga_stats.get('best_fitness', 0):.4f}")
            stats_text.append(f"Runtime: {ga_stats.get('runtime', 0):.1f}s")
        
        deck_stats_label.config(text="   |   ".join(stats_text) if stats_text else "")
        
    def copy_deck_to_clipboard():
        """Copy the current deck list to clipboard"""
        text = best_deck_widget.get(1.0, tk.END)
        root.clipboard_clear()
        root.clipboard_append(text)
        ui_manager.show_info("Copy Complete", "Deck list copied to clipboard")
        
    def update_deck_analysis_display(analysis_report):
        deck_analysis_widget.config(state=tk.NORMAL)
        deck_analysis_widget.delete('1.0', tk.END)
        if analysis_report:
            deck_analysis_widget.insert(tk.END, analysis_report)
        deck_analysis_widget.config(state=tk.DISABLED)

    def update_ui(ga_object):
        """Update UI elements based on the current state of the GA object"""
        ga_instance = ga_object.ga_instance
        best_solution, best_fitness, _ = ga_instance.best_solution()
        
        # Get the generation information
        current_generation = ga_instance.generations_completed
        
        # Create GA stats dictionary for UI update
        ga_stats = {
            'generations': current_generation,
            'max_generations': NUM_GENERATIONS,
            'best_fitness': best_fitness,
            'fitness_history': ga_object.fitness_history if hasattr(ga_object, 'fitness_history') else None
        }
        
        # Use the deck_generator from the passed ga_object to map IDs to names
        deck_names = [ga_object.deck_generator.id_to_card[gene] for gene in best_solution]
        
        # Pass detailed results if available
        detailed_results = ga_object.best_solution_detailed_results if hasattr(ga_object, 'best_solution_detailed_results') else None
        update_best_deck_display(deck_names, detailed_results, ga_stats)
        
        # Update deck analysis report if available
        if hasattr(ga_object, 'get_deck_report') and ga_object.best_solution:
            update_deck_analysis_display(ga_object.get_deck_report())

    def handle_generation_update(ga_object):
        """Callback for generation updates - updates deck display"""
        # The callback now receives the entire GeneticAlgorithm object
        root.after(0, lambda: update_ui(ga_object))

    def handle_progress_update(progress_data):
        """Function to handle detailed progress updates"""
        root.after(0, lambda: update_progress_display(progress_data))

    def update_progress_display(progress_data):
        """Update UI with detailed progress information"""
        gen = progress_data['generation']
        max_gen = progress_data['max_generation']
        best_fitness = progress_data['best_fitness']
        
        # Update basic progress information
        gen_label.config(text=f"Generation: {gen} / {max_gen}")
        fitness_label.config(text=f"Best Fitness: {best_fitness:.4f}")
        progress_bar['value'] = (gen / max_gen) * 100
        
        # Update time remaining
        if progress_data['estimated_time_remaining'] is not None:
            mins, secs = divmod(int(progress_data['estimated_time_remaining']), 60)
            time_str = f"{mins} min {secs} sec"
            time_label.config(text=f"Time Remaining: {time_str}")
        
        # Update trend information
        fitness_history = progress_data['fitness_history']
        if len(fitness_history) > 0:
            fitness_trend = ""
            if len(fitness_history) >= 5:
                recent = fitness_history[-5:]
                if all(recent[i] >= recent[i-1] for i in range(1, len(recent))):
                    fitness_trend = "↑ Improving"
                elif all(recent[i] <= recent[i-1] for i in range(1, len(recent))):
                    fitness_trend = "↓ Decreasing"
                elif recent[-1] > recent[-2]:
                    fitness_trend = "→ Stable with recent improvement"
                else:
                    fitness_trend = "→ Stable"
            progress_details_label.config(text=f"Trend: {fitness_trend}")
            
            # Update fitness history graph
            update_fitness_graph(fitness_history)

    def update_fitness_graph(fitness_history):
        """Update the fitness history graph with latest data"""
        # Clear previous plot
        ax.clear()
        
        # Plot new data
        generations = list(range(1, len(fitness_history) + 1))
        ax.plot(generations, fitness_history, 'b-', marker='o', markersize=3)
        
        # Set titles and labels
        ax.set_title('Fitness History')
        ax.set_xlabel('Generation')
        ax.set_ylabel('Fitness')
        
        # Add grid for better readability
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Redraw canvas
        canvas.draw()

    # --- Evolution Logic ---
    def refresh_meta_deck_list():
        """Refresh the meta deck dropdown with available files"""
        try:
            ui_manager.show_busy_cursor()
            
            db_manager = CardDatabaseManager(
                card_dataset_path=CARD_DATASET_PATH,
                meta_decks_dir=META_DECKS_DIR
            )
            
            # Get available meta deck files
            available_files = db_manager.get_available_meta_deck_files()
            
            # Add "Latest" as the first option
            dropdown_options = ["Latest"] + available_files
            meta_deck_dropdown['values'] = dropdown_options
            
            # Set to Latest if not already set
            if not meta_deck_var.get() or meta_deck_var.get() not in dropdown_options:
                meta_deck_var.set("Latest")
                
            if not available_files:
                log_message("No meta deck files found in the meta decks directory.")
        except Exception as e:
            ui_manager.show_error("Error", f"Failed to refresh meta deck list: {e}")
        finally:
            ui_manager.restore_cursor()
    
    def get_legal_sets():
        """Get the set of legal sets based on UI settings"""
        if not rotation_var.get():
            return None  # No rotation, all sets legal
            
        # Validate date format
        if not ui_manager.validate_date_format(rotation_date_var.get()):
            ui_manager.show_error("Invalid Date", "Please enter a valid date in YYYY-MM-DD format.")
            return None
            
        try:
            # Parse the rotation date
            date_str = rotation_date_var.get()
            rotation_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            
            # Get legal sets for the rotation date
            db_manager = CardDatabaseManager(card_dataset_path=CARD_DATASET_PATH)
            return db_manager.get_rotation_sets(rotation_date)
        except Exception as e:
            ui_manager.show_error("Error", f"Failed to determine legal sets: {e}")
            return None
    
    def run_evolution_task():
        try:
            # Check if all required directories exist, create if needed
            os.makedirs(META_DECKS_DIR, exist_ok=True)
            
            # Disable the start button during evolution
            start_button.config(state=tk.DISABLED)
            ui_manager.show_busy_cursor()
            
            # Clear the log
            log_widget.config(state=tk.NORMAL)
            log_widget.delete('1.0', tk.END)
            log_widget.config(state=tk.DISABLED)

            log_message("--- Lorcana Deck Evolution Engine ---")
            log_message("Initializing components...")
            start_time = time.time()
            
            # Initialize card database manager
            db_manager = CardDatabaseManager(
                card_dataset_path=CARD_DATASET_PATH,
                meta_decks_dir=META_DECKS_DIR
            )
            
            # Get legal sets based on rotation settings
            legal_sets = get_legal_sets()
            if legal_sets is not None:
                log_message(f"Set rotation enabled. Using {len(legal_sets)} legal sets.")
                for set_name in sorted(legal_sets):
                    log_message(f"  - {set_name}")
            
            # Initialize deck generator with filtered card pool
            deck_generator = DeckGenerator(
                card_dataset_path=CARD_DATASET_PATH,
                legal_sets=legal_sets
            )
            log_message(f"Deck Generator initialized with {len(deck_generator.unique_card_names)} unique cards.")

            # Load meta decks based on selection
            meta_deck_selection = meta_deck_var.get()
            if meta_deck_selection == "Latest":
                meta_deck_path = db_manager.get_latest_meta_deck_file()
                log_message(f"Loading latest meta decks...")
            else:
                meta_deck_path = os.path.join(META_DECKS_DIR, meta_deck_selection)
                log_message(f"Loading meta decks from {meta_deck_selection}...")
                
            meta_decks_names = db_manager.load_meta_decks(meta_deck_path)
            if meta_decks_names:
                log_message(f"Successfully loaded {len(meta_decks_names)} meta decks.")
            else:
                log_message("No meta decks found. Using an empty list.")
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
                progress_callback=handle_progress_update,
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
            
            # Create GA stats dictionary
            ga_stats = {
                'generations': NUM_GENERATIONS,
                'best_fitness': best_fitness,
                'runtime': end_time - start_time,
                'fitness_history': ga.fitness_history if hasattr(ga, 'fitness_history') else None
            }
            
            # Update the best deck display with detailed stats
            if ga.best_solution:
                best_solution = ga.best_solution
                deck_names = [ga.deck_generator.id_to_card[gene] for gene in best_solution]
                update_best_deck_display(deck_names, ga.best_solution_detailed_results, ga_stats)
            
            # Switch to best deck tab first (then user can explore analysis tab after)
            notebook.select(deck_frame)

        except FileNotFoundError:
            ui_manager.show_error("File Not Found", f"Card dataset not found at '{CARD_DATASET_PATH}'.")
            log_message(f"ERROR: Card dataset not found at '{CARD_DATASET_PATH}'.")
        except Exception as e:
            ui_manager.show_error("Error", f"An unexpected error occurred: {e}")
            log_message(f"An unexpected error occurred: {e}")
        finally:
            start_button.config(state=tk.NORMAL)
            ui_manager.restore_cursor()

    def start_evolution_thread():
        # Confirm before starting a potentially lengthy process
        if ui_manager.confirm_action("Confirm Start", "Starting the evolution process may take some time. Continue?"):
            thread = threading.Thread(target=run_evolution_task, daemon=True)
            thread.start()
            
    # Initialize the meta deck dropdown when the app starts
    refresh_meta_deck_list()

    start_button.config(command=start_evolution_thread)
    root.mainloop()

if __name__ == '__main__':
    main()