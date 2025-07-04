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

- [ ] **Task 1.2: Refactor Challenge Target Validation**
  - [ ] Locate the duplicated code for validating challenge targets within the `src/game_engine/` directory.
  - [ ] Create a new private helper method within the appropriate class (e.g., `GameState` or `Player`) to encapsulate this logic.
  - [ ] Update all original call sites to use the new, single helper method.

---

## Stage 2: Feature Enhancements & AI Improvements
*This stage focuses on implementing planned features from the project documentation to improve the simulation's fidelity and the AI's intelligence.*

- [ ] **Task 2.1: Implement Advanced Targeting Logic**
  - [ ] Analyze the `TODO` in the `_get_targets` method within `src/game_engine/effect_resolver.py`.
  - [ ] Design and implement the logic required to handle more complex, conditional targeting (e.g., "choose a character with cost 3 or less," "choose an exerted character").
  - [ ] Add new, specific unit tests to `tests/test_game_engine.py` to validate the new targeting capabilities.

- [ ] **Task 2.2: Implement Advanced AI Heuristics (Synergy Scoring)**
  - [ ] Research and design a system for quantifying card synergy within a deck or hand. This may involve pre-calculating synergy scores or evaluating them at runtime.
  - [ ] Integrate the synergy scoring system into the `Player`'s decision-making process in `src/game_engine/player_logic.py`.
  - [ ] Add unit tests to `tests/test_game_engine.py` to verify that the AI makes different (and better) decisions when synergy is considered.

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
  - [ ] Design a clear and comprehensive view for the final, optimized deck.
  - [ ] Display the full 60-card list, the final fitness score, and the two ink colors.
  - [ ] Add a "Copy to Clipboard" button for the decklist.

---

## Stage 4: Final Polish, Documentation & Deployment
*This final stage involves preparing the application for release.*

- [ ] **Task 4.1: Update All Project Documentation**
  - [ ] Review and update `README.md` to reflect all changes, ensuring the setup and usage instructions are accurate.
  - [ ] Mark all tasks in this `MASTER_TASKLIST.md` as complete.

- [ ] **Task 4.2: Final Code Cleanup**
  - [ ] Perform a final pass through the entire codebase to remove any remaining debugging `print` statements, commented-out code, and unused imports.
  - [ ] Ensure all code adheres to a consistent formatting standard (e.g., Black).

- [ ] **Task 4.3: Package Application for Distribution**
  - [ ] Research and implement a packaging solution like `PyInstaller` or `cx_Freeze` to create a standalone executable.
  - [ ] Create executables for target operating systems (e.g., macOS, Windows).
  - [ ] Add a new "Installation" section to the `README.md` with instructions for downloading and running the packaged application.