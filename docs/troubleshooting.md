# Project Oracle Troubleshooting Plan

This document outlines the investigation and resolution plan for the critical failures discovered during the test run on 2025-07-02.

## 1. Initial Analysis (Failed)

- **Symptom:** The evolution log shows an `unexpected error occurred: unhashable type: 'numpy.ndarray'`. This halts the genetic algorithm before the first generation completes.
- **Hypothesis:** The `DeckGenerator.get_deck_inks` method was using a mutable `numpy.ndarray` deck as a key for its memoization cache.
- **Action Taken:** A fix was implemented to convert the NumPy array to an immutable tuple before using it as a cache key.
- **Result:** **FAILURE.** The exact same error persists, indicating the fix was either incorrect, incomplete, or the problem exists in multiple locations.

## 2. Deeper Investigation: Full Codebase Audit

- **Objective:** Achieve >99.999% confidence in the fix by performing a comprehensive audit of the entire codebase. We will not attempt another fix until all potential sources of the error are identified and understood.
- **Error Type:** `unhashable type: 'numpy.ndarray'`. This occurs when a mutable NumPy array is used as a dictionary key or a set element.
- **Audit Plan:**
    1.  **File-by-File Review:** Systematically review every function in `src/genetic_algorithm.py` and `src/deck_generator.py` that accepts a `deck` or `solution` as an argument.
    2.  **Trace Data Flow:** For each function, trace the `deck` variable to see if it is used in any hashing context (dictionary key, set element).
    3.  **Identify All Violations:** Compile a definitive list of every location where the `numpy.ndarray` to `tuple` conversion is required.
    4.  **Holistic Fix:** Implement all required conversions in a single, comprehensive commit.

## 3. Known Issues & Hypotheses (Post-Audit)

- **True Root Cause Identified:** The error originates in `DeckGenerator.generate_initial_population`. This function uses a `set` to ensure deck uniqueness. It calls `generate_deck()`, which was returning a mutable `list`. The subsequent attempt to add this list to the set (`population.add(...)`) caused the `unhashable type` error. The error was not in the GA loop itself, but in the initial data creation.
- **Holistic Fix Implemented:**
    1.  `DeckGenerator.generate_deck` was refactored to return a `tuple` (an immutable, hashable type) instead of a `list`.
    2.  `DeckGenerator.generate_initial_population` was updated to directly add the returned tuple to the `population` set, removing the redundant and erroneous `tuple(sorted(deck))` conversion.
    3.  This ensures data type consistency from the point of creation, resolving the architectural flaw.

## 4. Final Validation Plan

- **Action:** After the comprehensive fix is applied, run the application.
- **Expected Outcome:** The evolution process will run to completion without errors. The UI will display real-time updates for the generation count, fitness score, progress bar, and the best decklist. The final performance breakdown will be displayed in the log upon completion.
    2.  Modify the function to convert the input `numpy.ndarray` into an immutable `tuple` before using it as a dictionary key or set element.
    3.  Review other methods in `DeckGenerator` and `GeneticAlgorithm` for similar data handling errors.

## 2. Secondary Issue: Unresponsive User Interface

- **Symptoms:**
    - Generation counter remains at `0/0`.
    - Best Fitness score remains `N/A`.
    - Progress bar does not update.
    - "Best Deck So Far" window is blank.
- **Root Cause Analysis:** These are not separate bugs, but direct consequences of the core runtime crash. The `pygad` instance fails during the first generation, so the `_on_generation` callback is never triggered. Without this callback, the UI never receives any data to update its state.
- **Action Plan:**
    1.  No direct action is required for the UI.
    2.  Confirm that the UI becomes fully responsive after the core runtime crash is resolved.

## 3. Validation

- **Action:** After implementing the fix, run the application again.
- **Expected Outcome:** The evolution process will run to completion without errors. The UI will display real-time updates for the generation count, fitness score, progress bar, and the best decklist. The final performance breakdown will be displayed in the log upon completion.
