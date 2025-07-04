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
    Main function to create and run the UI - Compact design that fits entirely in window.
    """
    root = tk.Tk()
    root.title("Project Oracle - Lorcana Deck Evolution")
    root.geometry("1200x800")
    root.minsize(1000, 700)
    
    # Initialize UI Manager
    ui_manager = UIManager(root)
    
    # Main container - NO SCROLLING, everything fits in window
    main_frame = ttk.Frame(root)
    main_frame.pack(fill="both", expand=True, padx=10, pady=5)
    
    # === COMPACT TOP SECTION ===
    # Title and main controls in one compact row
    header_frame = ttk.Frame(main_frame)
    header_frame.pack(fill="x", pady=(0, 5))
    
    # Title (smaller)
    ttk.Label(header_frame, text="Project Oracle - Lorcana Deck Evolution", font=('Arial', 10, 'bold')).pack(side="left")
    
    # Exit button
    exit_button = ttk.Button(header_frame, text="Exit", command=root.quit)
    exit_button.pack(side="right")
    
    # === COMPACT CONFIGURATION ===
    config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding=5)
    config_frame.pack(fill="x", pady=(0, 5))
    
    # Single compact row with all controls
    controls_row = ttk.Frame(config_frame)
    controls_row.pack(fill="x")
    
    # Meta decks (compact)
    ttk.Label(controls_row, text="Meta Decks:").pack(side="left")
    meta_deck_var = tk.StringVar(value="Latest")
    meta_deck_dropdown = ttk.Combobox(controls_row, textvariable=meta_deck_var, state="readonly", width=20)
    meta_deck_dropdown.pack(side="left", padx=2)
    refresh_meta_button = ttk.Button(controls_row, text="Refresh")
    refresh_meta_button.pack(side="left", padx=2)
    
    # Set rotation (compact)
    rotation_var = tk.BooleanVar(value=False)
    rotation_checkbox = ttk.Checkbutton(controls_row, text="Enable", variable=rotation_var)
    rotation_checkbox.pack(side="left", padx=(10, 2))
    ttk.Label(controls_row, text="Date:").pack(side="left")
    rotation_date_var = tk.StringVar(value=datetime.date.today().strftime("%Y-%m-%d"))
    date_entry = ttk.Entry(controls_row, textvariable=rotation_date_var, width=10)
    date_entry.pack(side="left", padx=2)
    
    # Start button
    start_button = ttk.Button(controls_row, text="Start Evolution", style="Accent.TButton")
    start_button.pack(side="left", padx=(10, 0))
    
    # === COMPACT PROGRESS SECTION ===
    progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding=3)
    progress_frame.pack(fill="x", pady=(0, 3))
    
    # Single row with all progress info
    progress_info = ttk.Frame(progress_frame)
    progress_info.pack(fill="x")
    
    gen_label = ttk.Label(progress_info, text="Generation: 0 / 0", font=('Arial', 8))
    gen_label.pack(side="left")
    
    fitness_label = ttk.Label(progress_info, text="Best Fitness: N/A", font=('Arial', 8))
    fitness_label.pack(side="left", padx=10)
    
    time_label = ttk.Label(progress_info, text="Time Remaining: N/A", font=('Arial', 8))
    time_label.pack(side="right")
    
    # Compact progress bar
    progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
    progress_bar.pack(fill="x", pady=2)
    
    # === SPLIT LAYOUT: GRAPH LEFT, RESULTS RIGHT ===
    content_frame = ttk.Frame(main_frame)
    content_frame.pack(fill="both", expand=True)
    
    # Left side: Tiny fitness graph
    graph_frame = ttk.LabelFrame(content_frame, text="Fitness", padding=2)
    graph_frame.pack(side="left", fill="y", padx=(0, 3))
    graph_frame.pack_propagate(False)  # Prevent expansion
    graph_frame.configure(width=250, height=200)  # Fixed small size
    
    # Create tiny fitness graph
    fig = plt.figure(figsize=(3, 2), facecolor='white')
    ax = fig.add_subplot(111)
    ax.set_title('Fitness', fontsize=7, pad=1)
    ax.tick_params(axis='both', which='major', labelsize=5)
    ax.grid(True, alpha=0.2)
    
    # Minimal layout adjustments
    fig.subplots_adjust(left=0.15, right=0.95, top=0.9, bottom=0.15)
    
    canvas = FigureCanvasTkAgg(fig, master=graph_frame)
    canvas.get_tk_widget().pack(fill="both", expand=True)
    
    # Right side: Compact results
    results_frame = ttk.LabelFrame(content_frame, text="Results", padding=3)
    results_frame.pack(side="right", fill="both", expand=True)
    
    # Compact notebook for results
    notebook = ttk.Notebook(results_frame)
    notebook.pack(fill="both", expand=True)
    
    # Evolution Log tab
    log_frame = ttk.Frame(notebook)
    log_widget = scrolledtext.ScrolledText(log_frame, height=12, wrap=tk.WORD, font=('Arial', 8))
    log_widget.pack(fill="both", expand=True, padx=2, pady=2)
    notebook.add(log_frame, text="Log")
    
    # Best Deck tab
    deck_frame = ttk.Frame(notebook)
    
    # Compact deck header
    deck_header = ttk.Frame(deck_frame)
    deck_header.pack(fill="x", padx=2, pady=2)
    ttk.Label(deck_header, text="Evolved Deck", font=('Arial', 9, 'bold')).pack(side="left")
    copy_button = ttk.Button(deck_header, text="Copy")
    copy_button.pack(side="right")
    
    # Deck stats (compact)
    deck_stats_label = ttk.Label(deck_frame, text="", font=('Arial', 7))
    deck_stats_label.pack(padx=2, pady=1)
    
    # Deck content (more lines to fit properly)
    best_deck_widget = scrolledtext.ScrolledText(deck_frame, height=12, wrap=tk.WORD, font=('Arial', 8))
    best_deck_widget.pack(fill="both", expand=True, padx=2, pady=2)
    notebook.add(deck_frame, text="Deck")
    
    # Deck Analysis tab
    analysis_frame = ttk.Frame(notebook)
    deck_analysis_widget = scrolledtext.ScrolledText(analysis_frame, height=12, wrap=tk.WORD, font=('Arial', 8))
    deck_analysis_widget.pack(fill="both", expand=True, padx=2, pady=2)
    notebook.add(analysis_frame, text="Analysis")
    
    # === HELPER FUNCTIONS ===
    def start_evolution_thread():
        """Start the evolution process in a separate thread"""
        if ui_manager.confirm_action("Confirm Start", "Starting the evolution process may take some time. Continue?"):
            thread = threading.Thread(target=run_evolution_task, daemon=True)
            thread.start()
    
    def copy_deck_to_clipboard():
        """Copy the current deck list to clipboard"""
        try:
            deck_content = best_deck_widget.get('1.0', tk.END).strip()
            if deck_content:
                root.clipboard_clear()
                root.clipboard_append(deck_content)
                ui_manager.show_info("Copied", "Deck list copied to clipboard!")
            else:
                ui_manager.show_warning("No Deck", "No deck available to copy.")
        except Exception as e:
            ui_manager.show_error("Error", f"Failed to copy deck: {e}")
    
    # Configure button commands
    start_button.configure(command=start_evolution_thread)
    refresh_meta_button.configure(command=lambda: refresh_meta_deck_list())
    copy_button.configure(command=copy_deck_to_clipboard)
    
    # Add date validation
    def validate_date_entry(event=None):
        if not ui_manager.validate_date_format(rotation_date_var.get()):
            ui_manager.show_error("Invalid Date", "Please enter a valid date in YYYY-MM-DD format.")
            rotation_date_entry.focus_set()
            return False
        return True
    
    date_entry.bind("<FocusOut>", validate_date_entry)

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
        """Refresh the meta deck dropdown with available deck names from markdown file"""
        try:
            ui_manager.show_busy_cursor()
            
            db_manager = CardDatabaseManager(
                card_dataset_path=CARD_DATASET_PATH,
                meta_decks_dir=META_DECKS_DIR
            )
            
            # Get the canonical meta deck file path
            meta_deck_path = db_manager.get_latest_meta_deck_file()
            
            if meta_deck_path and meta_deck_path.endswith('.md'):
                # Parse deck names from markdown file
                deck_names = db_manager.get_meta_deck_names(meta_deck_path)
                if deck_names:
                    dropdown_options = ["All Decks"] + deck_names
                else:
                    dropdown_options = ["All Decks"]
            else:
                # Fallback to old CSV-based system
                available_files = db_manager.get_available_meta_deck_files()
                dropdown_options = ["Latest"] + available_files
            
            meta_deck_dropdown['values'] = dropdown_options
            
            # Set to first option if not already set
            if not meta_deck_var.get() or meta_deck_var.get() not in dropdown_options:
                meta_deck_var.set(dropdown_options[0] if dropdown_options else "All Decks")
                
            if not dropdown_options or len(dropdown_options) <= 1:
                log_message("No meta decks found - check data/raw/meta-decks.md file.")
            else:
                log_message(f"Loaded {len(dropdown_options)-1} meta decks from canonical source.")
                
        except Exception as e:
            log_message(f"Error refreshing meta deck list: {str(e)}")
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
            if meta_deck_selection == "All Decks" or meta_deck_selection == "Latest":
                # Use canonical meta deck file for all decks or legacy "Latest" option
                meta_deck_path = db_manager.get_latest_meta_deck_file()
                log_message(f"Loading all meta decks from canonical source...")
            else:
                # Individual deck selection - still use canonical file but filter later
                meta_deck_path = db_manager.get_latest_meta_deck_file()
                log_message(f"Loading specific meta deck: {meta_deck_selection}...")
                
            meta_decks_names = db_manager.load_meta_decks(meta_deck_path)
            
            # If a specific deck was selected (not "All Decks"), filter to just that deck
            if meta_deck_selection != "All Decks" and meta_deck_selection != "Latest" and meta_decks_names:
                # Find the specific deck by name
                deck_names = db_manager.get_meta_deck_names(meta_deck_path)
                if meta_deck_selection in deck_names:
                    deck_index = deck_names.index(meta_deck_selection)
                    if deck_index < len(meta_decks_names):
                        meta_decks_names = [meta_decks_names[deck_index]]
                        log_message(f"Using specific deck: {meta_deck_selection}")
                    else:
                        log_message(f"Deck '{meta_deck_selection}' not found, using all decks.")
                else:
                    log_message(f"Deck '{meta_deck_selection}' not found, using all decks.")
            
            if meta_decks_names:
                log_message(f"Successfully loaded {len(meta_decks_names)} meta deck(s).")
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
            result = ga.run()
            if result is None:
                # Handle the case where ga.run() returns None
                log_message("Error: Genetic algorithm returned None")
                best_solution, best_fitness = None, 0
            else:
                best_solution, best_fitness = result

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

    # Initialize the meta deck dropdown when the app starts
    refresh_meta_deck_list()

    start_button.config(command=start_evolution_thread)
    root.mainloop()

if __name__ == '__main__':
    main()