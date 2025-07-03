# Project Oracle Troubleshooting & Recovery Plan

## 1. Status: Root Cause Re-evaluation - Data Type Mismatch

- **Summary:** The previous diagnosis of a simulation timeout was incorrect. The implementation of a global turn limit did not resolve the core issue. The application still fails with a critical runtime error: `unhashable type: 'numpy.ndarray'`.
- **Conclusion:** The true root cause is a fundamental data type mismanagement issue. Somewhere within the genetic algorithm's execution loop, a mutable `numpy.ndarray` is being used in a context that requires a hashable type (e.g., as a dictionary key or a set element). This is a direct violation of Python's data model and is the definitive cause of the crash. All previous hypotheses are now considered invalid.

## 2. New Strategy: Test-Driven Bug Isolation

- **Objective:** To definitively locate and fix the source of the unhashable `numpy.ndarray`. The current approach of debugging through the UI is inefficient and obscures the problem. We will pivot to a rigorous, test-driven development (TDD) methodology.
- **Core Plan:**
    1.  **Create an Isolated Integration Test:** Develop a new test case that replicates the GA setup from `main.py` but runs without the UI. This test will call `ga.run()` directly and is expected to fail with the `unhashable type` error, providing a fast and reliable reproduction environment.
    2.  **Pinpoint the Failure:** With a reproducible test, use targeted debugging within the `pygad` callbacks (`_crossover_func`, `_mutation_func`, `_fitness_function_wrapper`) to trace the data types being passed between our code and the `pygad` library.
    3.  **Implement and Verify the Fix:** Once the exact line causing the type error is identified, apply the correct data type conversion (e.g., to a `tuple`). The fix is validated when the new integration test passes.

## 3. Recovery and Optimization Plan

### Phase 1: Core Stability - Resolving the Crash
- **Objective:** Eradicate the `unhashable type: 'numpy.ndarray'` error using a rigorous, test-driven approach.
- **Tasks:**
    1.  **1.1. TDD Crash Reproduction:** Create a new integration test (`tests/test_ga_integration.py`) that isolates the genetic algorithm from the UI and reliably reproduces the crash.
    2.  **1.2. Root Cause Fix:** Use the failing test to debug and pinpoint the exact location where a NumPy array is used improperly. Implement a robust fix by ensuring any data structure used as a dictionary key or set element is explicitly converted to a hashable `tuple` at the boundary between PyGAD and our custom functions.
    3.  **1.3. Validation and UI Check:** Confirm the fix by ensuring the integration test passes. Run the full application to verify the backend is stable and that the UI now receives updates correctly.
    4.  **1.4. Cleanup:** Remove the temporary integration test file.

### Phase 2: Performance Optimization
- **Objective:** Address critical performance bottlenecks to ensure the evolution process completes within the 5-10 minute target.
- **Tasks:**
    1.  **2.1. Optimize Fitness Calculation:** Refactor the `FitnessCalculator` to eliminate slow, repetitive `pandas.DataFrame` filtering inside the simulation loop. This will be achieved by pre-computing a card data lookup dictionary for near-instantaneous access.
    2.  **2.2. Profile and Tune Simulation Loop:** After the primary bottleneck is resolved, profile a full generation run to identify any secondary performance issues, likely within the AI's action enumeration (`get_possible_actions`).

### Phase 3: System Robustness and Correctness
- **Objective:** Enhance the long-term stability and logical correctness of the simulation AI.
- **Tasks:**
    1.  **3.1. Harden AI Loop Prevention:** Refactor the infinite loop safeguard in `player_logic.py`. Replace the fragile `repr(action)` check with a robust, hashable tuple composed of the action's essential attributes.
    2.  **3.2. Review Simulation Parameters:** Validate that the `max_turns` parameter is set to a value that balances meaningful game simulation with efficient execution time.

### Phase 4: Finalization and Handoff
- **Objective:** Verify the completed work and prepare for user review.
- **Tasks:**
    1.  **4.1. Full System Validation:** Execute the entire program, confirming it runs to completion within the target timeframe and produces a valid, sensible result.
    2.  **4.2. Code Commit:** Commit all changes with a comprehensive message detailing the fixes and enhancements.
    3.  **4.3. User Handoff:** Notify you that the program is ready for final testing.

## 4. UI Status

- **Analysis:** The UI's failure to update remains a symptom, not a cause. It is a direct result of the backend crash.
- **Action:** No action is needed on the UI code itself. It is expected to function correctly once the backend is stable.

---

# Architectural Analysis (Systematic Review)

*This section documents a full, systematic review of the codebase, file by file, to build a comprehensive understanding of the system architecture, data flow, and component responsibilities. This analysis is performed without any code modifications.*

## 1. `README.md`

- **Purpose**: Provides a high-level overview of the project, its structure, and setup instructions.
- **Key Takeaways**:
    - **Core Functionality**: The application is a "Disney Lorcana TCG Deck Optimizer" that uses a genetic algorithm to discover high-performing decks.
    - **Architecture**: The project follows a clear, modular structure:
        - `data/`: Contains raw and processed datasets.
        - `docs/`: Project documentation and specifications.
        - `src/`: Core application source code, further divided into modules for abilities, data processing, game engine, genetic algorithm, and UI.
        - `tests/`: Unit and integration tests, mirroring the `src` structure.
        - `main.py`: The main entry point for the application.
        - `requirements.txt`: Lists all Python dependencies.
    - **Critical Dependency**: There is a mandatory, multi-step data processing pipeline (`collect_card_data.py`, `parse_validate_decks.py`) that must be run before the main application can be launched. This implies a dependency on the state of the `data/processed/` directory. Any issues with these scripts or their output will prevent the application from running correctly.
- **Potential Failure Points**:
    - Failure to run the data processing scripts in the correct order will lead to runtime errors (e.g., `FileNotFoundError`).
    - Out-of-date or incorrect dependencies in `requirements.txt` could cause unexpected behavior.

## 2. `requirements.txt`

- **Purpose**: Defines the core Python dependencies required for the project.
- **Key Takeaways**:
    - **`pandas`**: The primary library for data manipulation. It is expected to be used extensively for loading, cleaning, and querying the card dataset. The `DataFrame` is the central data structure for card information.
    - **`requests`**: An HTTP client library. Its presence strongly implies that the data collection process (`src/data_processing/collect_card_data.py`) connects to an external web service or API to fetch card data. This introduces an external dependency and potential points of failure related to network connectivity, API changes, or rate limiting.
    - **`PyGAD`**: The core genetic algorithm library. This is the engine that drives the deck evolution. All custom logic for crossover, mutation, and fitness evaluation is written to conform to the `PyGAD` API. Understanding its data flow, particularly its use of `numpy.ndarray` for representing solutions (decks), is critical to solving the primary `unhashable type` error.
- **Potential Failure Points**:
    - **`pandas`**: Inefficient `DataFrame` operations could lead to performance bottlenecks, especially during deck generation or fitness evaluation.
    - **`requests`**: The external data source could become unavailable, or its API could change, breaking the data collection pipeline.
    - **`PyGAD`**: The interaction between our custom functions and the `PyGAD` engine is the most complex part of the system and the source of the most critical bugs. Data types must be managed carefully at the boundary between our code and the library.

## 3. `main.py`

- **Purpose**: The main entry point and central orchestrator of the application. It is responsible for building the `tkinter` UI, initializing all backend components, and managing the interaction between them.
- **Key Takeaways**:
    - **Architecture**: The application uses a multi-threaded design. The main thread runs the `tkinter` event loop for the UI, while a separate background thread (`threading.Thread`) executes the computationally expensive genetic algorithm (`run_evolution_task`). This is a critical design choice to ensure the UI remains responsive.
    - **Component Initialization**: The `run_evolution_task` function defines the core logic flow:
        1.  Initializes `DeckGenerator`.
        2.  Initializes `FitnessCalculator`, which depends on the `DeckGenerator`.
        3.  Initializes `GeneticAlgorithm`, which depends on the previous two components.
        4.  Calls the blocking `ga.run()` method to start the evolution.
    - **UI Updates & Callbacks**: UI updates are handled in a thread-safe manner. The `GeneticAlgorithm` is configured with an `on_generation` callback (`handle_generation_update`). This callback, executed by `PyGAD` in the background thread, uses `root.after(0, ...)` to schedule the actual UI update function (`update_ui`) to run on the main UI thread. This is the correct pattern for `tkinter` and prevents race conditions.
    - **Data Flow**: The `on_generation` callback passes the entire `GeneticAlgorithm` instance to the UI update logic. This gives the UI access to not only the raw `pygad` results but also helper components like the `DeckGenerator` to map card IDs to human-readable names for display.
- **Potential Failure Points**:
    - **Threading**: While the current implementation is sound, any future changes involving shared state between the threads must be handled with extreme care to avoid race conditions or deadlocks.
    - **GA Hang**: The `ga.run()` call is blocking. If this function hangs (as has been observed), the background thread will stall indefinitely, UI updates will cease, and the application will appear frozen. The root cause of any hang must be within the code executed by `ga.run()` (i.e., the fitness, crossover, or mutation functions).
    - **Error Propagation**: The `try...except` block in `run_evolution_task` is the final safety net. An unhandled exception within the GA thread will be caught here and displayed in the UI log. This is the point where the `unhashable type` error would ultimately be reported to the user.

## 4. `src/deck_generator.py`

- **Purpose**: This class is responsible for all aspects of deck creation. It loads the master card dataset, provides mappings between card names and integer IDs, and contains the logic to generate random, legal decks and initial populations.
- **Key Takeaways**:
    - **Performance Optimization**: The `__init__` method performs significant pre-computation. It creates a dictionary (`ink_pair_card_lists`) that maps every possible two-ink combination to a pre-filtered list of eligible cards. This avoids expensive `pandas` filtering during the deck generation loop, making the `generate_deck` method highly efficient. This is a strong architectural pattern.
    - **Single Responsibility Principle (SRP)**: The class is an excellent example of SRP. Its sole focus is generating valid decks. It has no knowledge of game rules, simulation, or fitness evaluation, making it a highly cohesive and decoupled module.
    - **Critical Type Conversion**: The `get_deck_inks` method contains the explicit `tuple(int(x) for x in deck)` conversion. This is the most important defensive programming measure against the `unhashable type: 'numpy.ndarray'` error, as this function is called from the fitness function, which is a direct callback from the `PyGAD` library. It ensures any array-like input from `PyGAD` is converted to a hashable tuple before being used as a dictionary key for memoization.
    - **Data Representation**: It establishes the canonical integer ID representation for cards (`card_to_id`, `id_to_card`) that is used throughout the backend, which is efficient for the genetic algorithm.
- **Potential Failure Points**:
    - **Data Schema Dependency**: The class is tightly coupled to the schema of the input CSV (`lorcana_card_master_dataset.csv`). Any changes to column names like 'Color' or 'Inkable' would break the initialization logic.
    - **Deck Uniqueness**: The `generate_initial_population` method relies on randomness and may struggle to generate a large number of *unique* decks if the underlying card pool is too small. This is handled gracefully with a warning.

## 5. `src/evolution.py` (FitnessCalculator)

- **Purpose**: This module's sole responsibility is to evaluate the "fitness" of a candidate deck. It does this by orchestrating game simulations between the candidate deck and a predefined set of meta decks, with the final fitness score being the overall win rate.
- **Key Takeaways**:
    - **SRP Adherence**: The `FitnessCalculator` class is another strong example of the Single Responsibility Principle. It is concerned only with calculating a fitness score, acting as a pure evaluation function. It is cleanly decoupled from deck generation and the GA's evolutionary mechanics.
    - **Game Engine Client**: This class is the primary client of the `game_engine`. It instantiates `Player` and `GameState` objects and calls `game_state.run_game()` to get a result. The validity of the entire project's output depends on the game engine being a correct and robust simulation of Lorcana.
    - **Circuit Breaker**: The `max_turns` parameter is passed down into the `simulate_game` call. This is a crucial circuit breaker to prevent infinite loops within a single game simulation from hanging the entire evolution process.
- **Potential Failure Points**:
    - **CRITICAL PERFORMANCE BOTTLENECK**: The `_create_player_from_deck_list` method contains a severe performance issue. It looks up card data by performing a `pandas` DataFrame filter (`df[df['Name'] == card_name]`) for every single card, in every deck, in every game simulated. This is an O(N) operation inside multiple nested loops, which will lead to extremely slow fitness calculations. The correct, performant approach would be to pre-process the card data into a dictionary keyed by card name during `__init__` for O(1) lookups.
    - **Game Logic Bugs**: The fitness score is a direct reflection of the game engine's output. Any bug in the game simulation will lead to an incorrect fitness landscape, causing the GA to optimize towards flawed strategies.
    - **Meta Deck Quality**: The quality and diversity of the `meta_decks` are paramount. If the meta is not representative of a challenging environment, the GA will produce decks that are not objectively powerful.

## 6. `src/genetic_algorithm.py`

- **Purpose**: This module is the master controller for the evolution process. It wraps the `PyGAD` library, configures it with all the necessary parameters, and provides the custom, domain-specific logic for crossover, mutation, and fitness evaluation.
- **Key Takeaways**:
    - **Facade Pattern**: The `GeneticAlgorithm` class is a textbook example of the Facade design pattern. It provides a simple, high-level interface (`run()`) to the rest of the application, hiding the complex setup and execution details of the underlying `pygad.GA` instance. This is excellent for decoupling the application from the `PyGAD` library.
    - **Custom Evolutionary Operators**: The core intelligence of the evolution lies in the custom `_crossover_func` and `_mutation_func`. These functions are essential because standard genetic operators would not respect the complex legality rules of a Lorcana deck (e.g., 2-ink limit, 4-copy limit). They ensure that all new decks generated during evolution are valid.
    - **Data Type Management**: This class is the primary interface with `PyGAD` and is therefore a critical location for managing data types. It correctly handles the `numpy.ndarray` objects that `PyGAD` uses for solutions (chromosomes), converting them to lists or tuples as needed before passing them to other components (like `get_deck_inks` or `calculate_fitness`). The `_fitness_function_wrapper` is a key part of this, translating the numpy array of card IDs into a list of card names for the `FitnessCalculator`.
    - **UI Callback Interface**: The `on_generation` callback is well-designed. It passes the entire `GeneticAlgorithm` instance (`self`) to the external callback function. This provides the UI with rich, contextual data for display, not just the raw `pygad` object.
- **Potential Failure Points**:
    - **`PyGAD` API Adherence**: The custom functions must strictly adhere to the input/output specifications of the `PyGAD` API. Any mismatch in expected data types or array shapes (e.g., the previous bug where crossover returned a single offspring instead of a batch) will cause a crash.
    - **Operator Performance**: The custom crossover and mutation functions contain non-trivial logic. If they are not performant, they could slow down the evolution, although this is a lesser concern than the `FitnessCalculator` bottleneck.
    - **Hyperparameter Tuning**: The effectiveness of the GA is highly sensitive to the hyperparameters set here (`population_size`, `num_generations`, `num_parents_mating`, etc.). Poor tuning will lead to suboptimal results.

## 7. `src/game_engine/game_engine.py`

- **Purpose**: This is the foundational module for the entire project. It defines the core classes that model the game of Lorcana (`Card`, `Deck`, `Player`, `GameState`) and contains the logic to run a full game simulation from start to finish. The output of the entire evolutionary process is entirely dependent on the correctness and performance of this engine.
- **Key Takeaways**:
    - **Object-Oriented Design**: The engine uses a clean, object-oriented approach. `Card` objects are instantiated for every card in a deck, correctly encapsulating dynamic in-game state like damage and exertion. `Player` and `GameState` objects manage the overall flow and rules.
    - **Separation of Concerns (Engine vs. AI)**: The `GameState.run_turn` method makes a call to an external `player_logic.run_main_phase` function. This is a critical design choice that separates the *rules* of the game (enforced by `GameState`) from the *strategy* of how to play (decided by `player_logic`).
    - **Robust Turn Management**: The engine correctly implements the turn phases (Ready, Set, Draw, Main). The logic for readying cards and, crucially, clearing temporary, start-of-turn effects is present and appears correct. This is a common failure point in game simulators.
    - **Defensive Programming**: The `Card` class constructor is robust, safely handling malformed or missing data for keywords and abilities from the input dataset.
- **Potential Failure Points**:
    - **Engine Complexity**: This is by far the most complex module. The `Player` and `GameState` classes have many methods and a large amount of state to manage. A single logical error in one of the core actions (e.g., `play_card`, `challenge`) could invalidate all simulation results.
    - **Incomplete Ability/Effect System**: While keywords are handled, the system for resolving the wide variety of unique card abilities is not fully implemented here. A dedicated `EffectResolver` pattern is needed to handle the parsed ability data. Without it, the simulation is not a true representation of the game. This is the single biggest risk to the project's validity.
    - **AI Dependency**: The engine is a passive executor of the AI's decisions. It does not validate that the AI's chosen action is optimal, only that it is legal. If the `player_logic` module contains bugs or gets stuck in a loop, it will hang the entire simulation. The `max_turns` parameter in `run_game` is the only defense against this.

## 8. `src/game_engine/player_logic.py`

- **Purpose**: This module contains the AI's "brain." It is responsible for enumerating all possible legal moves a player can make in a given game state, evaluating those moves with a set of heuristics, and deciding which action to take.
- **Key Takeaways**:
    - **Command Pattern**: The logic is built on a classic Command design pattern. Each possible move is an `Action` object (`QuestAction`, `ChallengeAction`, etc.). This is a very clean and extensible architecture.
    - **Heuristic-Based Scoring**: The `evaluate_actions` function is the core of the AI. It assigns a simple numerical score to each possible action. The quality of the AI is entirely dependent on the sophistication of these heuristics.
    - **Dynamic Main Phase Loop**: The `run_main_phase` function uses a loop that repeatedly gets all possible actions, evaluates them, and executes the highest-scoring one. This allows the AI to take multiple actions per turn and is a robust way to handle the main phase.
    - **Loop Safeguards**: The AI includes two essential safeguards to prevent it from getting stuck in an infinite loop: a hard limit on the number of actions per turn, and a check to prevent executing the exact same action twice.
- **Potential Failure Points**:
    - **Heuristic Simplicity**: The current heuristics are very basic (e.g., questing is worth its lore value, challenging is a simple trade calculation). This will lead to suboptimal play and an inaccurate fitness landscape. This is not a bug, but a significant limitation.
    - **Performance**: The `get_possible_actions` function is called repeatedly within the main phase loop. In very complex board states, enumerating all possible actions could become a performance bottleneck, slowing down simulations.
    - **`repr()` Fragility**: The infinite loop prevention uses `repr(action)` to track executed actions. This is clever, but could be fragile if two distinct, valid actions can produce the same string representation.
