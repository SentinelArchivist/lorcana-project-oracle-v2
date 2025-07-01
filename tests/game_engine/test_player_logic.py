import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from game_engine.game_engine import Card, Deck, Player, GameState
from game_engine import player_logic

# --- Test Fixtures ---
def create_mock_card_data(name: str, unique_id: str, **kwargs) -> dict:
    data = { 'Name': name, 'Unique_ID': unique_id, 'Cost': 3, 'Inkable': True, 'Strength': 2, 'Willpower': 4, 'Lore': 1 }
    data.update(kwargs)
    return data

class TestPlayerLogic(unittest.TestCase):
    """Test suite for the AI player's decision-making heuristics."""
    def setUp(self):
        # Player 1 will be the AI
        p1_deck = Deck([])
        self.player1 = Player(player_id=1, deck=p1_deck)
        
        # Player 2 is the opponent
        p2_deck = Deck([])
        self.player2 = Player(player_id=2, deck=p2_deck)
        
        self.game = GameState(self.player1, self.player2)

    def test_choose_card_to_ink(self):
        """Verify the AI inks the highest-cost inkable card."""
        self.player1.hand = [
            Card(create_mock_card_data("Low Cost", "L-1", Cost=1, Inkable=True), 1),
            Card(create_mock_card_data("High Cost", "H-1", Cost=5, Inkable=True), 1),
            Card(create_mock_card_data("Non-Inkable", "NI-1", Cost=4, Inkable=False), 1),
        ]
        
        card_to_ink = player_logic.choose_card_to_ink(self.player1)
        self.assertIsNotNone(card_to_ink)
        self.assertEqual(card_to_ink.name, "High Cost")

    def test_run_main_phase_challenge_priority(self):
        """Verify the AI prioritizes challenging over questing."""
        # Setup: P1 can challenge an opponent's exerted character.
        p1_char = Card(create_mock_card_data("P1 Char", "P1C-1", Strength=2, Willpower=2, Lore=1), 1)
        p1_char.turn_played = 0 # Ink is dry
        self.player1.play_area.append(p1_char)
        
        p2_char = Card(create_mock_card_data("P2 Char", "P2C-1", Strength=1, Willpower=1, Lore=1), 2)
        p2_char.is_exerted = True
        self.player2.play_area.append(p2_char)

        player_logic.run_main_phase(self.game, self.player1)

        # Verification: AI should have challenged.
        self.assertTrue(p1_char.is_exerted, "AI character should be exerted from challenging.")
        self.assertEqual(self.player1.lore, 0, "AI should have challenged, not quested.")
        self.assertEqual(p2_char.damage_counters, 2, "Opponent's character should have taken damage.")

    def test_run_main_phase_quests_when_no_challenge(self):
        """Verify the AI quests when there are no valid challenges."""
        # Setup: P1 has a ready character, but no valid targets to challenge.
        p1_char = Card(create_mock_card_data("Quester", "Q-1", Strength=1, Willpower=1, Lore=2), 1)
        p1_char.turn_played = 0 # Ink dry
        self.player1.play_area.append(p1_char)
        
        p2_char = Card(create_mock_card_data("Ready P2", "RP2-1", Strength=1, Willpower=1, Lore=1), 2)
        self.player2.play_area.append(p2_char) # Opponent is not exerted

        player_logic.run_main_phase(self.game, self.player1)

        # Verification: AI should have quested.
        self.assertEqual(self.player1.lore, 2, "AI should have quested as there were no challenges.")
        self.assertTrue(p1_char.is_exerted, "AI character should be exerted from questing.")

if __name__ == '__main__':
    unittest.main()
