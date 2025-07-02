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

**[x]Task 1.1: Design the Abilities Data Structure**
- **Action:** Create a new Python script (`create_abilities_database.py`).
- **Details:** This script will read `lorcana_card_master_dataset.csv`. It will define the final structure for our abilities data (e.g., a list of dictionaries or a dedicated class). The primary goal is to parse the `Abilities_JSON` column and the `Body_Text` for every card and prepare for manual translation.

**[x] Task 1.2: Implement the Manual Translation & Parsing**
- **Action:** Add logic to `create_abilities_database.py` to systematically iterate through each card with abilities.
- **Details:** The script will implement a parser based on the grammar defined in `programmers-guide-simulating-lorcana.md`. It will translate the text into a structured format with fields like `Trigger`, `Effect`, `Target`, and `Value`.
- **Output:** A new file, `lorcana_abilities_master.json`, containing a structured representation of every card's abilities.

## Stage 2: The Game Logic Engine (The Rules Master)

*With structured ability data, we can now build the core simulator.* 

**[x] Task 2.1: Create Core Game State Classes**
- **Action:** Create a new Python file (`game_engine.py`).
- **Details:** Define the core Python classes: `Card`, `Deck`, `Player`, and `GameState`. These classes will hold all the necessary attributes defined in the project spec (e.g., lore, hand, inkwell, characters in play).

**[x] Task 2.2: Implement the Turn Structure and Game Loop**
- **Action:** Add functions to `game_engine.py` to manage the game flow.
- **Details:** Code the main game loop, including the turn phases: Ready, Set, Draw, and Main. Implement the logic for checking win/loss conditions (20 lore or empty deck).

**[x] Task 2.3: Implement Core Card Actions**
- **Action:** Add methods to the `Player` and `GameState` classes for all fundamental actions.
- **Details:** Implement `play_card()`, `ink_card()`, `quest()`, `challenge()`, and `activate_ability()`. The `activate_ability()` method will be the most complex, as it will read from our `lorcana_abilities_master.json` to execute the correct effects.

**[x] Task 2.4: Develop the Heuristic-Based Player 'Brain'**
- **Action:** Create a new file (`player_logic.py`) and import it into `game_engine.py`.
- **Details:** Implement the heuristic AI for decision-making as outlined in the devspec. This includes functions for choosing what to ink, evaluating board state, and selecting the optimal action (quest vs. challenge vs. playing a card).

**[x] Task 2.5: Implement Action & Song Card Logic**
- **Action:** Enhance the `play_card` method in `game_engine.py`.
- **Details:** Add logic to differentiate between card types (Character, Action, Item). Actions should be moved to the discard pile immediately after their effect is resolved. Implement and test 'Banish' effect, 'GainStrength' (stat modifier) effect, and 'ReturnToHand' effect. Implement the 'Singer' keyword, allowing characters to be exerted to play a Song card for free instead of paying its ink cost.

**[x] Task 2.6: Implement Core Keyword Abilities**
- **Action:** Update the `challenge` method in `game_engine.py` and related AI logic.
- **Details:** Integrate the passive combat-related keywords from `lorcana_abilities_master.json`. This includes `Bodyguard` (must be challenged first), `Support` (adds strength to another character when questing), `Challenger +X` (gains strength when challenging), and `Resist +X` (reduces damage taken). Setup for implementing `GainKeyword` effect.

**[x] Task 2.7: Enhance AI Heuristics & Action Loop**
- **Action:** Refactor the `run_main_phase` function in `player_logic.py`.
- **Details:** Replace the rigid, one-action-per-turn logic with a flexible loop that continues as long as the AI has available ink and actions. The AI should be able to play a card, challenge, quest, and sing a song all in the same turn. Improve heuristics to make smarter decisions, such as evaluating trades (e.g., is it worth it to banish my character to banish a higher-value target?) and recognizing when to use `Bodyguard` characters defensively.


**[x] Task 2.8: Full-Spectrum Ability Parser**
- **Action:** Overhaul `create_abilities_database.py`.
- **Details:** We must be able to parse the vast majority of card text into structured `(Trigger, Effect, Target, Value)` tuples. This is the highest priority task.

**[x] Task 2.9: Generic Effect Resolver**
- **Action:** Create a system in `game_engine.py` that can take a parsed ability from any card and execute it.
- **Details:** This means implementing effects like `DealDamage`, `Heal`, `SearchDeck`, `ModifyStrength`, etc.

**[x] Task 2.10: Implement Item & Location Cards**
- **Action:** Add the logic for playing and interacting with these card types to the game engine.

**- [x] Task 2.11: Implement all remaining keywords**
- **Action:** Implement and test all remaining keywords (`Evasive`, `Rush`, `Ward`, `Reckless`, `Shift`, `Bodyguard`, `Challenger`, `Resist`, `Singer`, `Support`, `Vanish`).
- **Details:** This involved updating the game engine, AI logic, and creating comprehensive unit tests to ensure each keyword functions correctly according to the game rules. All tests pass.

**[x] Task 2.12: AI Integration of New Mechanics**
- **Action:** Teach the AI in `player_logic.py` how to use Items, Locations, and the full suite of abilities.
- **Details:** The action-enumeration and heuristic-evaluation functions were expanded to support new card types and abilities.
- **Sub-tasks:**
  - **[x] Enhance `ParsedAbility` for Costs:** Updated the `ParsedAbility` class to include a `cost` attribute, enabling representation of activated ability costs (e.g., exerting).
  - **[x] AI Evaluation for Item Cards:** Implemented heuristics in `evaluate_actions` for the AI to score `PlayCardAction` for Items based on their `OnPlay` abilities (e.g., card draw).
  - **[x] AI Evaluation for Location Cards:** Implemented heuristics in `evaluate_actions` for the AI to score `PlayCardAction` for Locations, valuing their passive lore generation and willpower.
  - **[x] AI Usage of Activated Abilities:** Confirmed the AI's `get_possible_actions` can generate `ActivateAbilityAction` for non-character cards (like Items) and that `evaluate_actions` scores them appropriately.

**[x] Task 2.13: Upgrade AI heuristics for advanced strategy and synergy**
- **Action:** Improve the AI's strategic thinking.
- **Details:** It needs to understand board state, resource planning, and how to leverage its specific cards and their synergies.
- **Sub-tasks:**
  - **[x] Implement Foundational Keyword Scoring:** AI scores cards with valuable keywords (Evasive, Ward, Resist, Challenger) higher.
  - **[x] Expand Keyword-Based Scoring:** Add nuanced scoring for `Support`, `Singer`, and `Vanish`.
  - **[ ] Future: Implement synergy-based scoring (e.g., tribal bonuses).**

## Stage 3: The Deck Generator and Genetic Algorithm (The Breeder)

*With a functional game engine, we can now automate deck testing and evolution.*

**[x] Task 3.1: Implement the Deck Generator**
- **Action:** Create a new file (`deck_generator.py`).
- **Details:** Write a function that creates an initial population of quasi-random, but legal and "resembling the meta competitive decks in terms of makeup" (60 cards, 2 inks, max 4 copies per card, most cards have 4 copies, etc.) decks using the `lorcana_card_master_dataset.csv`. The program should generate enough decks to fulfill the application's goals, but few enough that the program will ultimately be able to complete a full run in a few minutes tops.

**[x] Task 3.2: Implement and Test the Fitness Function**
- **Action:** Create the `FitnessCalculator` to evaluate deck strength through simulation.
- **Details:** The calculator will simulate a candidate deck against a gauntlet of meta decks and return a win rate as its fitness score. This is the core of the genetic algorithm's evaluation phase.
- **Sub-tasks:**
  - **[x] Create `FitnessCalculator` class and test suite.**
  - **[x] Integrate `DeckGenerator` to create `Player` objects for simulation.**
  - **[x] Implement game simulation logic using the `GameState` engine.**
  - **[x] Fix simulation loop and all integration bugs.**
  - **[x] Verify all `test_evolution.py` tests pass.**

**[x] Task 3.3: Implement the Genetic Algorithm**
- **Action:** Integrate the `pygad` library to drive the deck evolution process.
- **Details:** Use the `FitnessCalculator` as the fitness function. Define a gene space that represents a 60-card deck and implement custom crossover and mutation operators that respect the deck-building rules (ink colors, max copies). The entire GA was refactored to use integer-based card IDs for compatibility with `pygad`, a core architectural decision.
- **Sub-tasks:**
  - **[x] Create `GeneticAlgorithm` class and initial test suite (TDD setup).**
  - **[x] Implement initialization logic and verify with tests.**
  - **[x] Refactor GA to use integer-based card IDs.**
  - **[x] Integrate `FitnessCalculator` as the fitness function wrapper.**
  - **[x] Implement custom crossover logic ensuring deck legality.**
  - **[x] Implement custom mutation logic ensuring deck legality.**
  - **[x] Configure and run the GA instance, resolving all `pygad` integration issues.**
  - **[x] Create `main.py` script to run the full evolution process.**

## Stage 4: User Interface and Final Integration

*The final stage is to present the results to the user.*

**[x] Task 4.1: Design the Simple UI**
- **Action:** Create a main application file (`main.py`).
- **Details:** Use `tkinter` to build the simple user interface described in the devspec. This includes a start/stop button, a log area, a progress bar, an accurate estimated time to completion,and a display for the best decklist so far with relevant stats.

**[x] Task 4.2: Integrate All Components**
- **Action:** In `main.py`, wire the UI to the backend logic.
- **Details:** The 'Start' button will trigger the `evolution.py` script, which in turn uses the `game_engine.py` to evaluate decks. The UI will be updated in real-time with the progress and the best deck found so far.

**[x] Task 4.3: Final Output Display**
- **Action:** Add logic to `main.py` to format and display the final results.
- **Details:** When the evolution process is complete, the UI will display the champion decklist, its overall win rate, and its performance against each of the pillar meta decks. Make sure it includes a full decklist along with the win rate against each pillar meta deck.
