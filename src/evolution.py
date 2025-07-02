"""
Handles the fitness evaluation of decks for the genetic algorithm.
"""

import random
import pandas as pd

from src.game_engine.game_engine import GameState, Player, Deck, Card
from src.deck_generator import DeckGenerator


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

    def _create_player_from_deck_list(self, deck_list: list[str], player_id: int) -> Player:
        """Creates a Player object from a list of card names."""
        card_objects = []
        for card_name in deck_list:
            card_data_rows = self.deck_generator.card_df[self.deck_generator.card_df['Name'] == card_name]
            if not card_data_rows.empty:
                card_data = card_data_rows.iloc[0].to_dict()
                card_objects.append(Card(card_data, owner_player_id=player_id))
            else:
                # This can happen if a card name in a deck list isn't in the master dataset.
                # For now, we'll log a warning and skip it.
                print(f"Warning: Card '{card_name}' not found in dataset. Skipping.")
        
        deck = Deck(card_objects)
        return Player(player_id=player_id, deck=deck)

    def calculate_fitness(self, candidate_deck: list[str], games_per_matchup: int = 10) -> float:
        """
        Calculates the fitness of a candidate deck by simulating games against meta decks.

        Args:
            candidate_deck (list[str]): The deck to evaluate.
            games_per_matchup (int): The number of games to simulate for each meta deck matchup.

        Returns:
            float: The win rate of the candidate deck against the meta.
        """
        total_wins = 0
        total_games = 0

        if not self.meta_decks:
            return 0.0

        for meta_deck in self.meta_decks:
            for i in range(games_per_matchup):
                goes_first = i % 2 == 0
                winner = self.simulate_game(candidate_deck, meta_deck, goes_first)
                if winner == "player1":
                    total_wins += 1
                total_games += 1

        return total_wins / total_games if total_games > 0 else 0.0

    def simulate_game(self, deck1_list: list[str], deck2_list: list[str], goes_first: bool) -> str:
        """
        Simulates a single game between two decks using the game engine.

        Args:
            deck1_list (list[str]): The first player's deck as a list of names.
            deck2_list (list[str]): The second player's deck as a list of names.
            goes_first (bool): True if player 1 goes first, False otherwise.

        Returns:
            str: "player1" or "player2" indicating the winner.
        """
        player1 = self._create_player_from_deck_list(deck1_list, player_id=1)
        player2 = self._create_player_from_deck_list(deck2_list, player_id=2)

        if goes_first:
            game_state = GameState(player1, player2)
        else:
            game_state = GameState(player2, player1)

        winner_obj = game_state.run_game()

        if winner_obj is None:
            # Handle draws or unresolved games
            return random.choice(["player1", "player2"])
        
        if winner_obj.player_id == player1.player_id:
            return "player1"
        else:
            return "player2"
