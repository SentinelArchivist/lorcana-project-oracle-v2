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

    @safe_operation(log_level='error')
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
        # Use optimization config values if not specified
        if games_per_matchup is None:
            games_per_matchup = self.config.game_sample_size
        if max_turns is None:
            max_turns = self.config.max_turns_per_game
            
        logger.debug(f"Calculating fitness with {games_per_matchup} games per matchup, {max_turns} max turns")
        
        # Create a frozen version of the deck for cache lookups (if caching enabled)
        if self.config.cache_enabled:
            # Sort the candidate deck to ensure consistent cache lookups
            frozen_candidate = tuple(sorted(candidate_deck))

        total_wins = 0
        total_games = 0
        detailed_results = {}

        if not self.meta_decks:
            logger.warning("No meta decks provided for fitness calculation")
            return 0.0, {}

        # Check if we should use parallel processing
        if self.config.parallel_simulation and len(self.meta_decks) > 1:
            return self._calculate_fitness_parallel(candidate_deck, games_per_matchup, max_turns)
        else:
            return self._calculate_fitness_sequential(candidate_deck, games_per_matchup, max_turns)
    
    @safe_operation(log_level='error')
    def _calculate_fitness_sequential(self, candidate_deck: list[str], games_per_matchup: int, max_turns: int) -> tuple[float, dict[str, float]]:
        """
        Sequential implementation of fitness calculation.
        """
        total_wins = 0
        total_games = 0
        detailed_results = {}
        
        # Check if this exact deck has been cached
        if self.config.cache_enabled:
            frozen_candidate = tuple(sorted(candidate_deck))
            cached_result = self._check_cache(frozen_candidate)
            if cached_result is not None:
                logger.debug(f"Cache hit for deck calculation (hit rate: {self.cache_hits/(self.cache_hits+self.cache_misses):.2f})")
                return cached_result

        for i, meta_deck in enumerate(self.meta_decks):
            matchup_wins = 0
            
            # Early termination check
            continue_simulation = True
            early_termination_threshold = games_per_matchup * self.config.early_termination_threshold
            early_termination_counter = 0
            
            for j in range(games_per_matchup):
                # Check for early termination if enabled
                if self.config.early_termination and j > games_per_matchup // 2:
                    if matchup_wins >= early_termination_threshold or early_termination_counter >= early_termination_threshold:
                        # Extrapolate results and break
                        ratio_completed = j / games_per_matchup
                        matchup_wins = int(matchup_wins / ratio_completed)
                        logger.debug(f"Early termination for meta deck {i+1} at {j}/{games_per_matchup} games")
                        break
                
                goes_first = j % 2 == 0
                winner = self.simulate_game(candidate_deck, meta_deck, goes_first, max_turns=max_turns)
                if winner == "player1":
                    matchup_wins += 1
                else:
                    early_termination_counter += 1
            
            total_wins += matchup_wins
            total_games += games_per_matchup

            # For now, we'll identify meta decks by their index.
            meta_deck_name = f"Meta Deck {i + 1}"
            detailed_results[meta_deck_name] = matchup_wins / games_per_matchup if games_per_matchup > 0 else 0.0

        overall_win_rate = total_wins / total_games if total_games > 0 else 0.0
        
        # Cache the result if caching is enabled
        if self.config.cache_enabled:
            self._update_cache(frozen_candidate, (overall_win_rate, detailed_results.copy()))
            
        return overall_win_rate, detailed_results
    
    @safe_operation(log_level='error')
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
        matchup_wins = 0
        
        # Early termination check
        early_termination_threshold = games_per_matchup * self.config.early_termination_threshold
        early_termination_counter = 0
        
        for j in range(games_per_matchup):
            # Check for early termination if enabled
            if self.config.early_termination and j > games_per_matchup // 2:
                if matchup_wins >= early_termination_threshold or early_termination_counter >= early_termination_threshold:
                    # Extrapolate results
                    ratio_completed = j / games_per_matchup
                    matchup_wins = int(matchup_wins / ratio_completed)
                    return matchup_wins, games_per_matchup
            
            goes_first = j % 2 == 0
            winner = self.simulate_game(candidate_deck, meta_deck, goes_first, max_turns=max_turns)
            if winner == "player1":
                matchup_wins += 1
            else:
                early_termination_counter += 1
                
        return matchup_wins, games_per_matchup
    
    @safe_operation(log_level='debug')
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
        # Determine if we should enable detailed logging for this simulation
        if not self.config.detailed_logging:
            # Temporarily set logger level to reduce noise during simulation
            original_level = logger.level
            logger.setLevel('WARNING')  # Only show warnings and errors during simulation
            
        try:
            # Create players with card data
            player1 = Player(player_id=1, deck_list=deck1_list, card_data=self.deck_generator.card_df)
            player2 = Player(player_id=2, deck_list=deck2_list, card_data=self.deck_generator.card_df)

            if goes_first:
                game_state = GameState(player1, player2)
            else:
                game_state = GameState(player2, player1)

            winner_obj = game_state.run_game(max_turns=max_turns)

            if winner_obj is None:
                # Handle draws or unresolved games
                return random.choice(["player1", "player2"])
            
            if winner_obj.player_id == player1.player_id:
                return "player1"
            else:
                return "player2"
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
