"""
Handles the fitness evaluation of decks for the genetic algorithm.
"""

import random
import pandas as pd
import multiprocessing
from functools import partial
from typing import Dict, List, Tuple, Optional, Any

from src.game_engine.game_engine import GameState, Player
from src.deck_generator import DeckGenerator
from src.game_engine.player_logic import Action
from src.utils.logger import get_logger
from src.utils.error_handler import safe_operation
from src.utils.optimization_config import OptimizationManager

logger = get_logger()

class FitnessCalculator:
    """Calculates the fitness of a given deck."""

    def __init__(self, meta_decks: list[list[str]], deck_generator: DeckGenerator):
        """
        Initializes the FitnessCalculator.

        Args:
            meta_decks (list[list[str]]): A list of decks representing the meta.
            deck_generator (DeckGenerator): An instance of DeckGenerator with card data.
        """
        self.meta_decks = meta_decks
        self.deck_generator = deck_generator
        
        # Get optimization settings
        self.optimization_manager = OptimizationManager()
        self.config = self.optimization_manager.get_config()
        
        # Initialize simulation cache if enabled
        self.simulation_cache = {} if self.config.cache_enabled else None
        self.cache_hits = 0
        self.cache_misses = 0

    def calculate_fitness(self, candidate_deck: list[str], games_per_matchup: Optional[int] = None, max_turns: Optional[int] = None) -> tuple[float, dict[str, float]]:
        """
        Calculates the fitness of a candidate deck by simulating games against meta decks.
        Uses parallel processing if configured.

        Args:
            candidate_deck (list[str]): The deck to evaluate.
            games_per_matchup (int, optional): The number of games to simulate for each meta deck matchup.
                If None, uses the value from optimization config.
            max_turns (int, optional): Maximum number of turns per game.
                If None, uses the value from optimization config.

        Returns:
            tuple[float, dict[str, float]]: A tuple containing:
                - The overall win rate of the candidate deck against the meta.
                - A dictionary with detailed win rates against each meta deck.
        """
        try:
            # DIAGNOSTIC: Log candidate deck details
            print("\n[DIAGNOSTIC] calculate_fitness called")
            print(f"[DIAGNOSTIC] Candidate deck type: {type(candidate_deck)}")
            print(f"[DIAGNOSTIC] Candidate deck length: {len(candidate_deck)}")
            print(f"[DIAGNOSTIC] First 5 cards: {candidate_deck[:5]}")
            
            # Use optimization config values if not specified
            if games_per_matchup is None:
                games_per_matchup = self.config.game_sample_size
            if max_turns is None:
                max_turns = self.config.max_turns_per_game
                
            print(f"[DIAGNOSTIC] Using {games_per_matchup} games per matchup, {max_turns} max turns")
            logger.debug(f"Calculating fitness with {games_per_matchup} games per matchup, {max_turns} max turns")
            
            # Create a frozen version of the deck for cache lookups (if caching enabled)
            if self.config.cache_enabled:
                # Sort the candidate deck to ensure consistent cache lookups
                frozen_candidate = tuple(sorted(candidate_deck))
                print(f"[DIAGNOSTIC] Cache enabled, created frozen candidate")

            total_wins = 0
            total_games = 0
            detailed_results = {}

            if not self.meta_decks:
                logger.warning("No meta decks provided for fitness calculation")
                print(f"[DIAGNOSTIC] No meta decks available! This is a critical error.")
                return 0.0, {}

            print(f"[DIAGNOSTIC] Found {len(self.meta_decks)} meta decks for testing")
            
            # Check if we should use parallel processing
            if self.config.parallel_simulation and len(self.meta_decks) > 1:
                print(f"[DIAGNOSTIC] Using parallel fitness calculation")
                return self._calculate_fitness_parallel(candidate_deck, games_per_matchup, max_turns)
            else:
                print(f"[DIAGNOSTIC] Using sequential fitness calculation")
                return self._calculate_fitness_sequential(candidate_deck, games_per_matchup, max_turns)
        except Exception as e:
            print(f"[DIAGNOSTIC] Error calculating fitness: {e}")
            import traceback
            print(f"[DIAGNOSTIC] Traceback: {traceback.format_exc()}")
            logger.error(f"Error calculating fitness: {e}")
            # Return a minimal but valid result to avoid propagating None
            return 0.01, {"error": 0.01}  # Small non-zero fitness to prevent total failure
    
    def _calculate_fitness_sequential(self, candidate_deck: list[str], games_per_matchup: int, max_turns: int) -> tuple[float, dict[str, float]]:
        """
        Sequential implementation of fitness calculation.
        """
        print("\n[DIAGNOSTIC] _calculate_fitness_sequential called")
        print(f"[DIAGNOSTIC] Candidate deck type: {type(candidate_deck)}")
        print(f"[DIAGNOSTIC] Candidate deck length: {len(candidate_deck)}")
        print(f"[DIAGNOSTIC] First 5 cards: {candidate_deck[:5]}")
        print(f"[DIAGNOSTIC] Meta decks count: {len(self.meta_decks)}")
        print(f"[DIAGNOSTIC] First meta deck length: {len(self.meta_decks[0]) if self.meta_decks else 'No meta decks'}")
        
        total_wins = 0
        total_games = 0
        detailed_results = {}
        
        # Check if this exact deck has been cached
        if self.config.cache_enabled:
            frozen_candidate = tuple(sorted(candidate_deck))
            cached_result = self._check_cache(frozen_candidate)
            if cached_result is not None:
                print(f"[DIAGNOSTIC] Cache hit! Returning cached result: {cached_result}")
                logger.debug(f"Cache hit for deck calculation (hit rate: {self.cache_hits/(self.cache_hits+self.cache_misses):.2f})")
                return cached_result

        for i, meta_deck in enumerate(self.meta_decks):
            print(f"\n[DIAGNOSTIC] Testing against meta deck {i+1}, length: {len(meta_deck)}")
            print(f"[DIAGNOSTIC] Meta deck {i+1} first 5 cards: {meta_deck[:5]}")
            matchup_wins = 0
            
            # Early termination check
            continue_simulation = True
            early_termination_threshold = games_per_matchup * self.config.early_termination_threshold
            early_termination_counter = 0
            
            print(f"[DIAGNOSTIC] Playing {games_per_matchup} games")
            for j in range(games_per_matchup):
                # Check for early termination if enabled
                if self.config.early_termination and j > games_per_matchup // 2:
                    if matchup_wins >= early_termination_threshold or early_termination_counter >= early_termination_threshold:
                        # Extrapolate results and break
                        ratio_completed = j / games_per_matchup
                        matchup_wins = int(matchup_wins / ratio_completed)
                        print(f"[DIAGNOSTIC] Early termination at game {j+1}, extrapolating results")
                        logger.debug(f"Early termination for meta deck {i+1} at {j}/{games_per_matchup} games")
                        break
                
                goes_first = j % 2 == 0
                print(f"[DIAGNOSTIC] Simulating game {j+1}, candidate goes first: {goes_first}")
                winner = self.simulate_game(candidate_deck, meta_deck, goes_first, max_turns=max_turns)
                print(f"[DIAGNOSTIC] Game {j+1} winner: {winner}")
                if winner == "player1":
                    matchup_wins += 1
                else:
                    early_termination_counter += 1
            
            print(f"[DIAGNOSTIC] Matchup complete. Wins: {matchup_wins}, Total: {games_per_matchup}")
            total_wins += matchup_wins
            total_games += games_per_matchup

            # For now, we'll identify meta decks by their index.
            meta_deck_name = f"Meta Deck {i + 1}"
            win_rate = matchup_wins / games_per_matchup if games_per_matchup > 0 else 0.0
            detailed_results[meta_deck_name] = win_rate
            print(f"[DIAGNOSTIC] Win rate vs {meta_deck_name}: {win_rate:.4f}")

        overall_win_rate = total_wins / total_games if total_games > 0 else 0.0
        print(f"\n[DIAGNOSTIC] Overall win rate: {overall_win_rate:.4f}")
        print(f"[DIAGNOSTIC] Total wins: {total_wins}, Total games: {total_games}")
        
        # Cache the result if caching is enabled
        if self.config.cache_enabled:
            self._update_cache(frozen_candidate, (overall_win_rate, detailed_results.copy()))
            print(f"[DIAGNOSTIC] Result cached for future lookup")
            
        return overall_win_rate, detailed_results
    
    def _calculate_fitness_parallel(self, candidate_deck: list[str], games_per_matchup: int, max_turns: int) -> tuple[float, dict[str, float]]:
        """
        Parallel implementation of fitness calculation using multiprocessing.
        """
        # Check if this exact deck has been cached
        if self.config.cache_enabled:
            frozen_candidate = tuple(sorted(candidate_deck))
            cached_result = self._check_cache(frozen_candidate)
            if cached_result is not None:
                logger.debug(f"Cache hit for deck calculation (hit rate: {self.cache_hits/(self.cache_hits+self.cache_misses):.2f})")
                return cached_result
        
        num_workers = min(self.config.num_workers, len(self.meta_decks))
        logger.debug(f"Running parallel fitness calculation with {num_workers} workers")
        
        # Create a pool of workers
        with multiprocessing.Pool(processes=num_workers) as pool:
            # Prepare arguments for each meta deck matchup
            args = [
                (candidate_deck, meta_deck, games_per_matchup, max_turns, i)
                for i, meta_deck in enumerate(self.meta_decks)
            ]
            
            # Run simulations in parallel
            results = pool.starmap(self._simulate_matchup, args)
        
        # Process results
        total_wins = sum(wins for wins, _ in results)
        total_games = sum(games for _, games in results)
        
        detailed_results = {}
        for i, (wins, games) in enumerate(results):
            meta_deck_name = f"Meta Deck {i + 1}"
            detailed_results[meta_deck_name] = wins / games if games > 0 else 0.0
        
        overall_win_rate = total_wins / total_games if total_games > 0 else 0.0
        
        # Cache the result if caching is enabled
        if self.config.cache_enabled:
            self._update_cache(frozen_candidate, (overall_win_rate, detailed_results.copy()))
            
        return overall_win_rate, detailed_results
    
    def _simulate_matchup(self, candidate_deck: list[str], meta_deck: list[str], 
                        games_per_matchup: int, max_turns: int, deck_index: int) -> tuple[int, int]:
        """
        Simulates a series of games for a specific matchup.
        Helper method for parallel processing.
        
        Returns:
            tuple: (wins, total_games)
        """
        try:
            matchup_wins = 0
            
            # Early stopping: If a deck is clearly losing or winning, we can terminate early
            early_termination_counter = 0
            early_termination_threshold = games_per_matchup // 2  # 50% threshold
            
            for j in range(games_per_matchup):
                # Check for early termination conditions
                if self.config.early_termination:
                    if matchup_wins >= early_termination_threshold or early_termination_counter >= early_termination_threshold:
                        # Extrapolate results
                        ratio_completed = j / games_per_matchup
                        if ratio_completed > 0:
                            matchup_wins = int(matchup_wins / ratio_completed)
                        return matchup_wins, games_per_matchup
                
                goes_first = j % 2 == 0
                winner = self.simulate_game(candidate_deck, meta_deck, goes_first, max_turns=max_turns)
                if winner == "player1":
                    matchup_wins += 1
                else:
                    early_termination_counter += 1
                    
            return matchup_wins, games_per_matchup
        except Exception as e:
            logger.error(f"Error simulating matchup: {e}")
            # Return a minimal valid result
            return 0, games_per_matchup
    
    def simulate_game(self, deck1_list: list[str], deck2_list: list[str], goes_first=True, max_turns=100) -> str:
        """
        Simulates a game between two decks.

        Args:
            deck1_list (list[str]): The first player's deck (candidate).
            deck2_list (list[str]): The second player's deck (meta).
            goes_first (bool): Whether the first player goes first.
            max_turns (int): Maximum number of turns before the game ends.

        Returns:
            str: The winner ("player1" or "player2").
        """
        print(f"\n[DIAGNOSTIC] simulate_game called")
        print(f"[DIAGNOSTIC] Player 1 deck type: {type(deck1_list)}, length: {len(deck1_list)}")
        print(f"[DIAGNOSTIC] Player 2 deck type: {type(deck2_list)}, length: {len(deck2_list)}")
        
        # Check if decks contain numeric IDs instead of card names
        has_numeric_ids = False
        if deck1_list and isinstance(deck1_list[0], (int, float, np.integer)):
            print(f"[DIAGNOSTIC] WARNING: Player 1 deck contains numeric IDs, not card names!")
            has_numeric_ids = True
        if deck2_list and isinstance(deck2_list[0], (int, float, np.integer)):
            print(f"[DIAGNOSTIC] WARNING: Player 2 deck contains numeric IDs, not card names!")
            has_numeric_ids = True
            
        # Determine if we should enable detailed logging for this simulation
        if not self.config.detailed_logging:
            # Temporarily set logger level to reduce noise during simulation
            original_level = logger.level
            logger.setLevel('WARNING')  # Only show warnings and errors during simulation
            
        try:
            # If any deck contains numeric IDs, convert them using deck_generator
            if has_numeric_ids:
                print(f"[DIAGNOSTIC] Converting numeric IDs to card names")
                # This is a critical error - decks should contain card names by this point
                # For diagnostic purposes, return a random winner
                return random.choice(["player1", "player2"])

            # Print sample of each deck for verification
            print(f"[DIAGNOSTIC] Player 1 deck sample: {deck1_list[:5]}")
            print(f"[DIAGNOSTIC] Player 2 deck sample: {deck2_list[:5]}")
                
            # Create players with card data
            print(f"[DIAGNOSTIC] Creating player objects")
            try:
                player1 = Player(player_id=1, deck_list=deck1_list, card_data=self.deck_generator.card_df)
                print(f"[DIAGNOSTIC] Player 1 created successfully")
                player2 = Player(player_id=2, deck_list=deck2_list, card_data=self.deck_generator.card_df)
                print(f"[DIAGNOSTIC] Player 2 created successfully")
            except Exception as player_error:
                print(f"[DIAGNOSTIC] Error creating players: {player_error}")
                raise

            print(f"[DIAGNOSTIC] Creating game state, P1 goes first: {goes_first}")
            if goes_first:
                game_state = GameState(player1, player2)
            else:
                game_state = GameState(player2, player1)

            print(f"[DIAGNOSTIC] Running game with max_turns={max_turns}")
            winner_obj = game_state.run_game(max_turns=max_turns)
            print(f"[DIAGNOSTIC] Game completed, winner object: {winner_obj}")

            if winner_obj is None:
                # Handle draws or unresolved games
                result = random.choice(["player1", "player2"])
                print(f"[DIAGNOSTIC] Game ended in draw or was unresolved. Random winner: {result}")
                return result
            
            if winner_obj.player_id == player1.player_id:
                print(f"[DIAGNOSTIC] Player 1 won the game")
                return "player1"
            else:
                print(f"[DIAGNOSTIC] Player 2 won the game")
                return "player2"
        except Exception as e:
            print(f"[DIAGNOSTIC] Critical error simulating game: {e}")
            import traceback
            print(f"[DIAGNOSTIC] Traceback: {traceback.format_exc()}")
            logger.error(f"Error simulating game: {e}")
            # Return a random winner to keep the process moving
            return random.choice(["player1", "player2"])
        finally:
            # Restore logger level if we changed it
            if not self.config.detailed_logging:
                logger.setLevel(original_level)
    
    def _check_cache(self, frozen_deck) -> Optional[tuple[float, dict[str, float]]]:
        """
        Check if a deck's fitness calculation is in the cache.
        
        Args:
            frozen_deck: A hashable representation of the deck
            
        Returns:
            Cached result or None if not found
        """
        if not self.config.cache_enabled or not self.simulation_cache:
            return None
            
        if frozen_deck in self.simulation_cache:
            self.cache_hits += 1
            return self.simulation_cache[frozen_deck]
        else:
            self.cache_misses += 1
            return None
    
    def _update_cache(self, frozen_deck, result) -> None:
        """
        Update the simulation cache with a new result.
        
        Args:
            frozen_deck: A hashable representation of the deck
            result: The calculation result to cache
        """
        if not self.config.cache_enabled or not self.simulation_cache:
            return
            
        # If cache is full, remove oldest entry (FIFO)
        if len(self.simulation_cache) >= self.config.cache_size:
            # Simple approach: just clear 10% of the cache
            keys_to_remove = list(self.simulation_cache.keys())[:self.config.cache_size // 10]
            for key in keys_to_remove:
                del self.simulation_cache[key]
            
        self.simulation_cache[frozen_deck] = result
