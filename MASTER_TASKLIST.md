# Project Oracle: Master Task List

This document outlines the remaining tasks required to bring Project Oracle to full functional completion. It is organized into sequential stages, from critical bug fixes to final deployment.

---

## Stage 1: Critical Bug Fixes & Core Logic Refinement
*This stage addresses the most significant known issue that impacts the validity of the GA's results and performs minor code cleanup.*

- [x] **Task 1.1: Standardize the Meta-Deck Gauntlet**
  - [x] Modify the GA initialization process (likely in `main.py` or `src/genetic_algorithm.py`) to load the pre-processed `data/processed/lorcana_metagame_decks.csv` file.
  - [x] Ensure the loaded CSV data is correctly parsed into the list-of-lists format required by the `FitnessCalculator`.
  - [x] Remove the current logic that generates random meta decks on every run.
  - [x] Add a unit test to `tests/test_evolution.py` to confirm that the `FitnessCalculator` is initialized with the correct, static meta-deck data from the CSV.

- [x] **Task 1.2: Refactor Challenge Target Validation**
  - [x] Locate the duplicated code for validating challenge targets within the `src/game_engine/` directory.
  - [x] Create a new private helper method within the appropriate class (e.g., `GameState` or `Player`) to encapsulate this logic.
  - [x] Update all original call sites to use the new, single helper method.

---

## Stage 2: Feature Enhancements & AI Improvements
*This stage focuses on implementing planned features from the project documentation to improve the simulation's fidelity and the AI's intelligence.*

- [x] **Task 2.1: Implement Advanced Targeting Logic**
  - [x] Analyze the `TODO` in the `_get_targets` method within `src/game_engine/effect_resolver.py`.
  - [x] Design and implement the logic required to handle more complex, conditional targeting (e.g., "choose a character with cost 3 or less," "choose an exerted character").
  - [x] Add new, specific unit tests to `tests/test_game_engine.py` to validate the new targeting capabilities.

- [x] **Task 2.2: Implement Advanced AI Heuristics**
  - [x] Research and design a system for quantifying card synergy within a deck or hand. This may involve pre-calculating synergy scores or evaluating them at runtime.
  - [x] Implement the composite board state evaluation function described in the programmer's guide (section 5.2), incorporating lore delta, potential lore, board presence, and card advantage factors.
  - [x] Enhance the inkwell choice heuristic to better evaluate cards based on cost vs. turn number, redundancy, situational usefulness, and core win condition status.
  - [x] Implement limited lookahead analysis to anticipate opponent responses as outlined in section 5.3 of the guide.
  - [x] Integrate all these heuristics into the `Player`'s decision-making process in `src/game_engine/player_logic.py`.
  - [x] Add unit tests to verify that the AI makes different (and better) decisions with these enhancements.

- [ ] **Task 2.3: Implement Missing Card Types and Keywords**
  - [ ] **Location Cards**
    - [x] Complete the implementation of Location card type with move cost mechanics
    - [ ] Add passive lore gain at start of turn for Locations with lore value
    - [x] Implement location challenge mechanics (no return damage)
  - [ ] **Keywords**
    - [ ] Implement Rush keyword to bypass the "ink is dry" requirement for challenges
    - [ ] Complete Ward implementation with proper targeting restrictions
    - [ ] Implement Vanish keyword effects when targeted by opponents
    - [ ] Implement Sing Together mechanic to allow multiple characters to exert for a song
  - [ ] Add unit tests for each newly implemented card type and keyword

- [ ] **Task 2.3: Implement "The Bag" for Simultaneous Trigger Resolution**
  - [ ] Design and implement the mechanism for tracking and resolving simultaneous ability triggers as described in section 1.4 of the programmer's guide.
  - [ ] Modify the effect resolver to properly queue triggered abilities and resolve them according to active player priority.
  - [ ] Add unit tests to validate correct resolution order of simultaneous triggers.

- [ ] **Task 2.5: Add Deck Result Explanations**
  - [ ] Implement analytics to identify key synergies in generated decks
  - [ ] Create a system to explain card choices based on their performance in simulations
  - [ ] Generate a brief report highlighting strengths and strategic approach of evolved decks

- [ ] **Task 2.6: Handle Card Database Management**
  - [ ] Create a configurable system for handling meta-deck filenames with dates
  - [ ] Implement set rotation functionality to filter cards based on legality
  - [ ] Add an option to restrict card pools by expansion set
  - [ ] Ensure the card database stays up-to-date with the latest releases

---

## Stage 3: UI/UX Development & Refinement
*This stage focuses on ensuring the `tkinter` UI is robust, user-friendly, and provides adequate feedback.*

- [ ] **Task 3.1: Conduct Full UI Review and Testing**
  - [ ] Analyze the UI code within `main.py` to map out all components and user flows.
  - [ ] Run the application and manually test every UI element (buttons, input fields, display areas) for correct functionality and layout.
  - [ ] Document and fix any identified bugs, such as unresponsive elements or visual glitches.

- [ ] **Task 3.2: Implement Real-Time GA Progress Feedback**
  - [ ] Modify the GA `run` method to accept a callback function for reporting progress.
  - [ ] Update the UI to include a progress bar, a generation counter (`Gen X / Y`), and a display for the current best fitness score.
  - [ ] Run the GA in a separate thread from the main UI thread to prevent the application from freezing during the evolutionary process. Update the UI elements via the callback.

- [ ] **Task 3.3: Enhance Final Results Display**
  - [ ] Improve formatting and readability of the generated deck list.
  - [ ] Add basic statistics about the GA run (generations, fitness progression).
  - [ ] Include summary of matchup performance against meta decks.
  - [ ] Display the deck explanation generated in Task 2.5.
  - [ ] Add a "Copy to Clipboard" button for the decklist.

---

## Stage 4: Final Polish, Documentation & Deployment
*This final stage involves preparing the application for use.*

- [ ] **Task 4.1: Update All Project Documentation**
  - [ ] Review and update `README.md` to reflect all changes, ensuring the setup and usage instructions are accurate.
  - [ ] Mark all tasks in this `MASTER_TASKLIST.md` as complete.

- [ ] **Task 4.2: Final Code Cleanup and Optimization**
  - [ ] Remove any remaining debug print statements.
  - [ ] Consolidate and reduce code duplication.
  - [ ] Standardize error handling patterns.
  - [ ] Ensure consistent naming conventions.
  - [ ] Optimize simulation performance for MacBook Air M4 target
  - [ ] Implement parallel processing for fitness calculations where possible
  - [ ] Profile and optimize the most time-consuming operations
  - [ ] Add a configuration option to adjust simulation depth vs. speed tradeoffs