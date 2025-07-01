# Project Oracle: Disney Lorcana TCG Deck Optimizer

This project is a desktop application designed to analyze the Disney Lorcana TCG metagame, simulate game outcomes, and use a genetic algorithm to generate and test new, high-potential deck concepts.

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
│   ├── genetic_algorithm/  # Deck generation and evolution logic
│   └── ui/                 # User interface components
├── tests/                  # Unit and integration tests
├── .gitignore              # Specifies intentionally untracked files to ignore
├── main.py                 # Main application entry point
└── requirements.txt        # Project dependencies
```

## Setup and Usage

1.  **Create a Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run Data Pipelines:**
    To generate the required data, run the data processing scripts:
    ```bash
    python src/data_processing/collect_card_data.py
    python src/data_processing/parse_validate_decks.py
    ```

4.  **Run the Application:**
    ```bash
    python main.py
    ```
