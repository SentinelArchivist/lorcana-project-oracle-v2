# Project Oracle: Development Plan

This document outlines the step-by-step plan to complete Project Oracle, building upon the completed data acquisition stages (1a and 1b).

### Current Status
- **Master Card Dataset:** `lorcana_card_master_dataset.csv` is complete and contains all official card data.
- **Validated Metagame Decks:** `lorcana_metagame_decks.csv` is complete and contains validated decklists for our gauntlet.
- **Project Specification:** `project-oracle-devspec.md` defines the end-to-end goals.
- **Rules Engine Blueprint:** `programmers-guide-simulating-lorcana.md` provides the detailed logic for game mechanics.

---

## Stage 1 (Continued): Data Refinement - The Abilities Engine

*The most critical prerequisite for the simulation engine is translating raw card text into a structured, machine-readable format. This is the bridge from data to logic.*

**Task 1.1: Design the Abilities Data Structure**
- **Action:** Create a new Python script (`create_abilities_database.py`).
- **Details:** This script will read `lorcana_card_master_dataset.csv`. It will define the final structure for our abilities data (e.g., a list of dictionaries or a dedicated class). The primary goal is to parse the `Abilities_JSON` column and the `Body_Text` for every card and prepare for manual translation.

**Task 1.2: Implement the Manual Translation & Parsing**
- **Action:** Add logic to `create_abilities_database.py` to systematically iterate through each card with abilities.
- **Details:** The script will implement a parser based on the grammar defined in `programmers-guide-simulating-lorcana.md`. It will translate the text into a structured format with fields like `Trigger`, `Effect`, `Target`, and `Value`.
- **Output:** A new file, `lorcana_abilities_master.json`, containing a structured representation of every card's abilities.

## Stage 2: The Game Logic Engine (The Rules Master)

*With structured ability data, we can now build the core simulator.* 

**Task 2.1: Create Core Game State Classes**
- **Action:** Create a new Python file (`game_engine.py`).
- **Details:** Define the core Python classes: `Card`, `Deck`, `Player`, and `GameState`. These classes will hold all the necessary attributes defined in the project spec (e.g., lore, hand, inkwell, characters in play).

**Task 2.2: Implement the Turn Structure and Game Loop**
- **Action:** Add functions to `game_engine.py` to manage the game flow.
- **Details:** Code the main game loop, including the turn phases: Ready, Set, Draw, and Main. Implement the logic for checking win/loss conditions (20 lore or empty deck).

**Task 2.3: Implement Core Card Actions**
- **Action:** Add methods to the `Player` and `GameState` classes for all fundamental actions.
- **Details:** Implement `play_card()`, `ink_card()`, `quest()`, `challenge()`, and `activate_ability()`. The `activate_ability()` method will be the most complex, as it will read from our `lorcana_abilities_master.json` to execute the correct effects.

**Task 2.4: Develop the Heuristic-Based Player 'Brain'**
- **Action:** Create a new file (`player_logic.py`) and import it into `game_engine.py`.
- **Details:** Implement the heuristic AI for decision-making as outlined in the devspec. This includes functions for choosing what to ink, evaluating board state, and selecting the optimal action (quest vs. challenge vs. playing a card).

**Task 2.5: Implement Action & Song Card Logic**
- **Action:** Enhance the `play_card` method in `game_engine.py`.
- **Details:** Add logic to differentiate between card types (Character, Action, Item). Actions should be moved to the discard pile immediately after their effect is resolved. Implement the 'Singer' keyword, allowing characters to be exerted to play a Song card for free instead of paying its ink cost.

**Task 2.6: Implement Core Keyword Abilities**
- **Action:** Update the `challenge` method in `game_engine.py` and related AI logic.
- **Details:** Integrate the passive combat-related keywords from `lorcana_abilities_master.json`. This includes `Bodyguard` (must be challenged first), `Support` (adds strength to another character when questing), `Challenger +X` (gains strength when challenging), and `Resist +X` (reduces damage taken).

**Task 2.7: Enhance AI Heuristics & Action Loop**
- **Action:** Refactor the `run_main_phase` function in `player_logic.py`.
- **Details:** Replace the rigid, one-action-per-turn logic with a flexible loop that continues as long as the AI has available ink and actions. The AI should be able to play a card, challenge, quest, and sing a song all in the same turn. Improve heuristics to make smarter decisions, such as evaluating trades (e.g., is it worth it to banish my character to banish a higher-value target?) and recognizing when to use `Bodyguard` characters defensively.

## Stage 3: The Deck Generator and Genetic Algorithm (The Breeder)

*With a functional game engine, we can now automate deck testing and evolution.*

**Task 3.1: Implement the Deck Generator**
- **Action:** Create a new file (`deck_generator.py`).
- **Details:** Write a function that creates an initial population of random, but legal (60 cards, 2 inks, max 4 copies) decks using the `lorcana_card_master_dataset.csv`.

**Task 3.2: Build the Fitness Function**
- **Action:** Create a new file (`evolution.py`).
- **Details:** Write the core fitness function. This function will take a single decklist, simulate a small number of games against each of the pillar decks from `lorcana_metagame_decks.csv` using the `game_engine`, and return the overall win rate.

**Task 3.3: Implement the Genetic Algorithm**
- **Action:** Use the `PyGAD` library within `evolution.py`.
- **Details:** Configure the genetic algorithm with the fitness function. Implement the custom crossover logic that respects the two-ink-color rule and the mutation logic.

## Stage 4: User Interface and Final Integration

*The final stage is to present the results to the user.*

**Task 4.1: Design the Simple UI**
- **Action:** Create a main application file (`main.py`).
- **Details:** Use `PySimpleGUI` to build the simple user interface described in the devspec. This includes a start/stop button, a log area, and a display for the best decklist.

**Task 4.2: Integrate All Components**
- **Action:** In `main.py`, wire the UI to the backend logic.
- **Details:** The 'Start' button will trigger the `evolution.py` script, which in turn uses the `game_engine.py` to evaluate decks. The UI will be updated in real-time with the progress and the best deck found so far.

**Task 4.3: Final Output Display**
- **Action:** Add logic to `main.py` to format and display the final results.
- **Details:** When the evolution process is complete, the UI will display the champion decklist, its overall win rate, and its performance against each of the pillar meta decks.
