import unittest
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from game_engine.game_engine import Card, Deck, Player, GameState

# --- Test Fixtures ---

def create_mock_card_data(name: str, unique_id: str, **kwargs) -> dict:
    """Creates a dictionary of mock card data, allowing overrides."""
    data = {
        'Name': name,
        'Unique_ID': unique_id,
        'Cost': 3,
        'Inkable': True,
        'Strength': 2,
        'Willpower': 4,
        'Lore': 1
    }
    data.update(kwargs)
    return data

def create_mock_deck(player_id: int, num_cards: int = 60) -> Deck:
    """Creates a mock deck of cards for a given player."""
    cards = [Card(create_mock_card_data(f"Card {i}", f"P{player_id}-{i}"), player_id) for i in range(num_cards)]
    return Deck(cards)

# --- Test Cases ---

class TestGameEngineStateAndTurns(unittest.TestCase):
    """
    Test suite for the core classes and turn structure of the game engine.
    """
    def setUp(self):
        """Set up a fresh game state for each test."""
        p1_deck = create_mock_deck(player_id=1)
        p2_deck = create_mock_deck(player_id=2)
        self.player1 = Player(player_id=1, deck=p1_deck)
        self.player2 = Player(player_id=2, deck=p2_deck)
        self.player1.draw_initial_hand()
        self.player2.draw_initial_hand()
        self.game = GameState(self.player1, self.player2)

    def test_first_player_skips_first_draw(self):
        """Verify the first player does not draw a card on turn 1."""
        self.assertEqual(self.game.turn_number, 1)
        self.assertEqual(self.game.current_player_id, 1)
        self.assertEqual(len(self.player1.hand), 7)

        self.game.run_turn()

        self.assertEqual(len(self.player1.hand), 7, "Player 1 should not draw on turn 1.")

    def test_second_player_draws_on_first_turn(self):
        """Verify the second player draws a card on their first turn."""
        # Complete Player 1's first turn
        self.game.run_turn()
        self.game.end_turn()

        self.assertEqual(self.game.current_player_id, 2)
        self.assertEqual(len(self.player2.hand), 7)

        self.game.run_turn()

        self.assertEqual(len(self.player2.hand), 8, "Player 2 should draw on their first turn.")

    def test_ready_phase_readies_exerted_cards(self):
        """Verify that the ready phase correctly readies exerted cards."""
        # Manually exert a card for Player 1
        card_in_play = self.player1.deck.draw()
        card_in_play.location = 'play'
        card_in_play.is_exerted = True
        self.player1.play_area.append(card_in_play)

        self.assertTrue(self.player1.play_area[0].is_exerted)
        self.game.run_turn() # This runs the ready phase for player 1
        self.assertFalse(self.player1.play_area[0].is_exerted, "Card should be readied at the start of the turn.")

    def test_win_condition_by_lore(self):
        """Verify that the game correctly identifies a winner by lore count."""
        self.assertIsNone(self.game.winner)
        self.player1.lore = 19
        self.game.run_turn() # Player 1's turn, no win yet
        self.assertIsNone(self.game.winner)

        self.player1.lore = 20
        self.game.run_turn() # Check at start of next turn should find the winner
        self.assertEqual(self.game.winner, 1, "Player 1 should win by reaching 20 lore.")

    def test_loss_condition_by_deck_out(self):
        """Verify that a player loses if they must draw from an empty deck."""
        # Manually empty Player 2's deck
        self.player2.deck.cards = []
        self.assertTrue(self.player2.deck.is_empty())

        # Progress to Player 2's turn
        self.game.run_turn()
        self.game.end_turn()

        self.assertEqual(self.game.current_player_id, 2)
        self.assertIsNone(self.game.winner)

        self.game.run_turn() # Player 2 attempts to draw

        self.assertEqual(self.game.winner, 1, "Player 2 should lose by decking out, making Player 1 the winner.")

if __name__ == '__main__':
    unittest.main()
