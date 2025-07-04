import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.game_engine.advanced_heuristics import (
    evaluate_board_state,
    calculate_board_presence,
    evaluate_inkwell_candidate,
    perform_lookahead_analysis
)

class TestAdvancedHeuristics(unittest.TestCase):
    def setUp(self):
        # Create mock objects for testing
        self.mock_game = MagicMock()
        self.mock_player = MagicMock()
        self.mock_opponent = MagicMock()
        
        # Set up player and opponent with basic attributes
        self.mock_player.player_id = 1
        self.mock_player.lore = 10
        self.mock_player.hand = [MagicMock(), MagicMock()]
        self.mock_player.play_area = []
        self.mock_player.inkwell = [MagicMock(), MagicMock()]
        
        self.mock_opponent.player_id = 2
        self.mock_opponent.lore = 8
        self.mock_opponent.hand = [MagicMock()]
        self.mock_opponent.play_area = []
        self.mock_opponent.inkwell = [MagicMock(), MagicMock(), MagicMock()]
        
        # Set up game to return our mocked objects
        self.mock_game.get_player = lambda pid: self.mock_player if pid == 1 else self.mock_opponent
        self.mock_game.get_opponent = lambda pid: self.mock_opponent if pid == 1 else self.mock_player
        self.mock_game.turn_number = 3
        
        # Mock card templates
        self.mock_character = MagicMock()
        self.mock_character.card_type = 'Character'
        self.mock_character.is_exerted = False
        self.mock_character.strength = 3
        self.mock_character.willpower = 4
        self.mock_character.lore = 2
        self.mock_character.cost = 3
        self.mock_character.name = 'Test Character'
        self.mock_character.has_keyword = lambda keyword: keyword == 'Evasive'  # Has Evasive
        
        self.mock_item = MagicMock()
        self.mock_item.card_type = 'Item'
        self.mock_item.cost = 2
        self.mock_item.is_exerted = False
        
        self.mock_location = MagicMock()
        self.mock_location.card_type = 'Location'
        self.mock_location.cost = 4
        self.mock_location.lore = 2
        self.mock_location.is_exerted = False

    def test_evaluate_board_state(self):
        # Initial state - player should be ahead (higher lore, equal board)
        score = evaluate_board_state(self.mock_game, 1)
        self.assertGreater(score, 0, "Player should be ahead with more lore")
        
        # Add cards to both players' boards
        self.mock_player.play_area = [self.mock_character, self.mock_item]
        self.mock_opponent.play_area = [self.mock_character]  # Opponent has less board presence
        
        # Re-evaluate - player should be even more ahead now
        new_score = evaluate_board_state(self.mock_game, 1)
        self.assertGreater(new_score, score, "Score should increase with more board presence")
        
        # Test from opponent's perspective
        opponent_score = evaluate_board_state(self.mock_game, 2)
        self.assertLess(opponent_score, 0, "Opponent should be behind")
        self.assertAlmostEqual(opponent_score, -new_score, places=5, 
                             msg="Player and opponent scores should be opposites")

    def test_calculate_board_presence(self):
        # Test with empty board
        presence = calculate_board_presence([])
        self.assertEqual(presence, 0, "Empty board should have zero presence")
        
        # Test with one character
        presence = calculate_board_presence([self.mock_character])
        expected_value = (self.mock_character.strength + self.mock_character.willpower) * 1.3  # Evasive multiplier
        self.assertAlmostEqual(presence, expected_value, places=5, 
                             msg="Character presence calculation incorrect")
        
        # Test with mixed card types
        presence = calculate_board_presence([self.mock_character, self.mock_item, self.mock_location])
        # Character + Item (2.0) + Location with lore (2 * 3.0)
        expected_value = (3 + 4) * 1.3 + 2.0 + 2 * 3.0
        self.assertAlmostEqual(presence, expected_value, places=5, 
                             msg="Mixed card types presence calculation incorrect")

    def test_evaluate_inkwell_candidate(self):
        # High-cost card should be good for inking
        expensive_card = MagicMock()
        expensive_card.cost = 8  # Much higher than turn 3
        expensive_card.name = "Expensive Card"
        expensive_card.card_type = "Character"
        expensive_card.abilities = []
        expensive_card.has_keyword = lambda keyword: False
        
        score = evaluate_inkwell_candidate(expensive_card, self.mock_player, self.mock_game)
        self.assertGreater(score, 0, "High-cost card should be good for inking")
        
        # Key card with Shift should not be inked
        key_card = MagicMock()
        key_card.cost = 3
        key_card.name = "Key Card"
        key_card.card_type = "Character"
        key_card.lore = 4  # High lore
        key_card.strength = 5
        key_card.willpower = 6
        key_card.has_keyword = lambda keyword: keyword == "Shift"
        key_card.abilities = []
        
        score = evaluate_inkwell_candidate(key_card, self.mock_player, self.mock_game)
        self.assertLess(score, 0, "Key card should not be inked")

    def test_perform_lookahead_analysis(self):
        # Mock actions
        mock_action1 = MagicMock()
        mock_action1.card = self.mock_character
        
        mock_action2 = MagicMock()
        mock_action2.character = self.mock_character
        
        actions = [mock_action1, mock_action2]
        
        # Test lookahead analysis returns sorted actions
        result = perform_lookahead_analysis(self.mock_game, self.mock_player, actions)
        self.assertEqual(len(result), len(actions), "Should return same number of actions")
        
        # Result should be a list of (action, score) tuples sorted by score
        if len(result) >= 2:
            self.assertGreaterEqual(result[0][1], result[1][1], "Actions should be sorted by score")

if __name__ == '__main__':
    unittest.main()
