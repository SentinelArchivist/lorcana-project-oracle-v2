# Project Oracle Troubleshooting Plan

This document outlines the investigation and resolution plan for the critical failures discovered during the test run on 2025-07-02.

## 1. Core Issue: Runtime Crash

- **Symptom:** The evolution log shows an `unexpected error occurred: unhashable type: 'numpy.ndarray'`. This halts the genetic algorithm before the first generation completes.
- **Root Cause Analysis:** The error `unhashable type: 'numpy.ndarray'` occurs when a mutable object (like a NumPy array) is used as a key in a dictionary or as an element in a set. In our architecture, decks are passed as NumPy arrays. A function is attempting to use this array in a hashing context.
- **Hypothesis:** The most likely culprit is the `DeckGenerator.get_deck_inks` method, which is called from within the `_crossover_func` and likely uses a dictionary or set for memoization or lookup, using the deck itself as a key.
- **Action Plan:**
    1.  Inspect the implementation of `DeckGenerator.get_deck_inks` to confirm this hypothesis.
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
