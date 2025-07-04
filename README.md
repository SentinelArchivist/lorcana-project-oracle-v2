# Project Oracle: Disney Lorcana TCG Deck Optimizer

Project Oracle is a comprehensive desktop application designed to analyze the Disney Lorcana TCG metagame, accurately simulate game outcomes, and leverage genetic algorithms to generate and test optimized deck concepts. The application features a user-friendly interface with real-time feedback, detailed analytics, and comprehensive deck explanations.

## Key Features

- **Advanced Game Simulation Engine**: A faithful reproduction of the Disney Lorcana TCG rules with support for all card types, keywords, and complex card interactions
- **Genetic Algorithm Optimization**: Evolves deck concepts over many generations to find the best possible combinations against the current meta
- **Real-time Evolution Feedback**: Visual progress indicators showing generation count, fitness trends, and estimated time remaining
- **Card Database Management**: Supports set rotation and expansion filtering to maintain Standard format compliance
- **Meta-Deck Gauntlet**: Tests evolved decks against a collection of current top-performing meta decks
- **Deck Analytics**: Provides insights into card synergies, strategic patterns, and matchup performance
- **Deck Explanations**: Auto-generates human-readable explanations of evolved decks, including strategy, key cards, and notable synergies
- **User-Friendly Interface**: Clean, intuitive interface with customizable parameters and detailed result displays

## Project Structure

```
lorcana-project-oracle-v2/
├── data/
│   ├── raw/                # Raw, original data files (e.g., manual decklists)
│   └── processed/          # Processed, cleaned, and generated data files
├── docs/                   # Project planning, specifications, and guides
├── src/
│   ├── abilities/          # Module for parsing and managing card abilities
│   ├── data_processing/    # Scripts for collecting and validating data
│   ├── game_engine/        # Core game simulation logic
│   │   ├── effect_resolver.py   # Resolves card effects and abilities
│   │   ├── game_state.py        # Main game state management
│   │   ├── player_logic.py      # AI decision-making logic
│   │   └── trigger_bag.py       # Manages simultaneous trigger resolution
│   ├── card_database_manager.py # Card database and meta-deck management
│   ├── deck_analyzer.py         # Analyzes deck synergies and strategies
│   ├── deck_generator.py        # Creates decks based on genetic algorithm outputs
│   ├── fitness_calculator.py    # Evaluates deck performance
│   ├── genetic_algorithm.py     # Core evolution algorithm implementation
│   └── ui_utils.py              # UI helper functions and components
├── tests/                  # Unit and integration tests
├── .gitignore              # Specifies intentionally untracked files to ignore
├── main.py                 # Main application entry point
└── requirements.txt        # Project dependencies
```

## Setup and Usage

### Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/SentinelArchivist/lorcana-project-oracle-v2.git
    cd lorcana-project-oracle-v2
    ```

2.  **Create a Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run Data Pipelines:**
    To generate the required data, run the data processing scripts:
    ```bash
    python src/data_processing/collect_card_data.py
    python src/data_processing/parse_validate_decks.py
    ```

### Running the Application

1.  **Launch the Application:**
    ```bash
    python main.py
    ```

2.  **Configure Evolution Settings:**
    - Select the number of generations to run
    - Choose meta-deck file to test against
    - Enable set rotation if desired
    - Adjust additional parameters as needed

3.  **Start the Evolution:**
    Click the "Start Evolution" button to begin the genetic algorithm process.

4.  **Monitor Progress:**
    The interface will display real-time progress including:
    - Current generation / total generations
    - Best fitness score achieved
    - Estimated time remaining
    - Evolution trend graph

5.  **Review Results:**
    Upon completion, you can:
    - View the optimized deck list with card costs and types
    - See detailed matchup performance against meta decks
    - Read the generated deck explanation with strategy insights
    - Copy the deck list to clipboard for sharing

### Advanced Usage

- **Set Rotation:** Enable or disable standard format rotation to filter available cards
- **Custom Meta Decks:** Place your own meta deck CSV files in the `data/raw/meta_decks` directory
- **Performance Tuning:** Adjust simulation depth vs. speed for your hardware capabilities

## Technical Details

### Core Technologies
- **Python**: The application is built using Python 3.8+
- **Tkinter**: Used for the user interface components
- **Matplotlib**: Integrated for data visualization and evolution trends
- **Pandas**: Handles all data processing and manipulation
- **Pygad**: Foundation for the genetic algorithm implementation

### Game Engine Features
- Full implementation of all card types: Characters, Items, Actions, Locations
- Support for keywords: Rush, Ward, Vanish, Evasive, Sing Together, and more
- Complex targeting rules and conditional effects
- "The Bag" system for proper simultaneous trigger resolution

### Machine Learning Approach
- Multi-objective fitness function balancing win rate and strategic factors
- Adaptive crossover and mutation rates
- Comprehensive deck analysis using both rule-based and statistical methods

## License

This project is provided for educational and research purposes. Disney Lorcana is a trademark of Disney/Ravensburger, and this project is not affiliated with or endorsed by the official game publishers.
