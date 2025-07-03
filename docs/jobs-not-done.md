# Project Oracle: Master Task List

This document outlines the systematic plan to bring Project Oracle to a state of completion, ensuring it is robust, bug-free, and fulfills its primary goal of evolving meta-competitive Lorcana decks. All tasks will be executed following a strict Test-Driven Development (TDD) methodology.

---

## Phase 1: Foundational Stability & TDD Reinforcement

**Objective:** To build a comprehensive test suite that validates all core components, eradicates known bugs, and provides a stable foundation for future development.

- [x] **Task 1.1: Establish Comprehensive Test Suite**
    - [x] Unit Tests for `DeckGenerator`: Verify legality of generated decks (ink rules, 4-copy limit, 60-card size).
    - [x] Unit Tests for `game_engine` Core:
        - [x] `Card`: Validated initialization, damage, keywords, and modifiers.
        - [x] `Player`: Validated initialization, drawing, inking, questing, and ink availability.
        - [x] `GameState`: Validated initialization, turn progression, and beginning phase (ready/draw).
    - [x] Integration Test for Data Pipeline: Create a test to run `collect_card_data.py` and `parse_validate_decks.py` in sequence, ensuring the processed data is valid.
    - [x] **Critical:** Integration Test for `unhashable type` bug: Write a dedicated test that simulates the conditions of the historical `numpy.ndarray` hashing error to prove the tuple-based fix in `DeckGenerator.get_deck_inks` is permanently effective.

- [ ] **Task 1.2: Validate and Harden the Ability Parser**
    - [ ] Create a validation suite for `create_abilities_database.py`.
    - [ ] Manually verify the parsed output for a representative sample of cards with complex and unique abilities.
    - [ ] Implement logging for unparsed or partially parsed ability text to identify and remedy gaps in the `ABILITY_GRAMMAR`.

- [ ] **Task 1.3: Git Checkpoint: Foundational Stability**
    - [ ] Once all tests in Phase 1 are passing, commit the changes to establish a verified, stable baseline.

---

## Phase 2: Simulation Fidelity & Performance

**Objective:** To ensure the game simulation is an accurate and high-performance representation of a real Lorcana game, capable of handling complex card effects.

- [ ] **Task 2.1: Implement the `EffectResolver` System**
    - [ ] Design and build a robust `EffectResolver` class, guided by TDD.
    - [ ] Implement logic to interpret the structured JSON from the abilities database and apply effects to the `GameState`.
    - [ ] Write individual unit tests for every known effect type (e.g., 'DrawCard', 'DealDamage', 'ModifyStrength').

- [ ] **Task 2.2: Enhance AI Heuristics**
    - [ ] Expand the `evaluate_actions` function in `player_logic.py` with more sophisticated scoring.
    - [ ] Incorporate heuristics for board state analysis, removal prioritization, and card advantage.

- [ ] **Task 2.3: Performance Profiling and Optimization**
    - [ ] Use `cProfile` or a similar tool to identify performance bottlenecks within the `FitnessCalculator` and game simulation loop.
    - [ ] Implement targeted optimizations (e.g., memoization, algorithmic improvements) to ensure simulations run within an acceptable timeframe.

- [ ] **Task 2.4: Git Checkpoint: Simulation Fidelity**
    - [ ] Commit changes after the `EffectResolver` is complete and the simulation is both accurate and performant.

---

## Phase 3: Metagame Alignment & Fitness Function Tuning

**Objective:** To align the genetic algorithm's evolutionary pressure with the primary goal of defeating top-tier meta decks.

- [ ] **Task 3.1: Integrate and Validate Meta Decks**
    - [ ] Curate and update the decklists in `data/raw/human_decks` to reflect the current Lorcana metagame.
    - [ ] Ensure `parse_validate_decks.py` processes them correctly.
    - [ ] Configure `FitnessCalculator` to use these decks as the exclusive opponents for evolving solutions.

- [ ] **Task 3.2: Refine the Fitness Function**
    - [ ] Evolve the fitness calculation beyond a simple win rate.
    - [ ] Implement a scoring system that rewards a high win rate across a *diverse* set of meta archetypes.
    - [ ] Experiment with incorporating secondary metrics like average lore differential or win speed, keeping the 4-20 turn limit in mind.

- [ ] **Task 3.3: Git Checkpoint: Meta-Aligned**
    - [ ] Commit changes once the fitness function is fully tuned to the project's primary objective.

---

## Phase 4: Full Evolution & Final Validation

**Objective:** To execute the full genetic algorithm run, analyze the results, and deliver the final, optimized deck.

- [ ] **Task 4.1: Execute Full Genetic Algorithm Run**
    - [ ] Configure `main.py` with optimized parameters for a full-scale evolution (e.g., large population, high generation count).
    - [ ] Run the evolution process, monitoring for stability and performance.

- [ ] **Task 4.2: Analyze and Validate Evolved Deck**
    - [ ] Perform a qualitative analysis of the best-evolved deck. Assess its strategy and coherence.
    - [ ] Run a final validation gauntlet: simulate the evolved deck against the meta decks 100s of times to confirm its high fitness score and favorable matchups.

- [ ] **Task 4.3: Final Documentation**
    - [ ] Update `README.md` with final instructions on how to run the entire data-to-evolution pipeline.
    - [ ] Ensure all code is clean, documented, and adheres to the Single Responsibility Principle.

- [ ] **Task 4.4: Git Checkpoint: Project Complete**
    - [ ] Make the final commit for the completed, verified, and documented project.
