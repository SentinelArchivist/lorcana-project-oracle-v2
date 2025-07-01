import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from game_engine.game_engine import Card, Deck, Player, GameState, ParsedAbility
from game_engine import player_logic

# --- Test Fixtures ---
def create_mock_card_data(name: str, unique_id: str, **kwargs) -> dict:
    data = { 'Name': name, 'Unique_ID': unique_id, 'Cost': 3, 'Inkable': True, 'Strength': 2, 'Willpower': 4, 'Lore': 1 }
    data.update(kwargs)
    return data

class TestAIKeywordLogic(unittest.TestCase):
    def setUp(self):
        """Set up a basic game state for each test."""
        # Use a fresh set of players and game for each test to ensure isolation
        p1_deck = Deck([Card(create_mock_card_data(f"P1-Card{i}", f"p1c{i}"), 1) for i in range(20)])
        p2_deck = Deck([Card(create_mock_card_data(f"P2-Card{i}", f"p2c{i}"), 2) for i in range(20)])
        self.player1 = Player(1, p1_deck)
        self.player2 = Player(2, p2_deck)
        self.game = GameState(self.player1, self.player2)
        self.game.turn_number = 2 # Avoid turn 1 draw skip

    def test_ai_prioritizes_bodyguard(self):
        """Verify AI correctly challenges a Bodyguard character."""
        ability = {'trigger': 'Passive', 'effect': 'GainKeyword', 'target': 'Self', 'value': {'keyword': 'Bodyguard'}, 'notes': ''}
        challenger = Card(create_mock_card_data("Challenger", "c-1", Strength=3, Willpower=2), 1)
        non_bodyguard = Card(create_mock_card_data("Normal", "n-1", Strength=1, Willpower=1), 2)
        bodyguard = Card(create_mock_card_data("Bodyguard", "bg-1", Strength=3, Willpower=3, Abilities=[ability]), 2)
        
        self.player1.play_area.append(challenger)
        self.player2.play_area.extend([non_bodyguard, bodyguard])
        challenger.turn_played = 1
        non_bodyguard.is_exerted = True
        bodyguard.is_exerted = True

        player_logic.run_main_phase(self.game, self.player1)

        self.assertIn(bodyguard, self.player2.discard_pile, "Bodyguard should have been challenged and banished.")
        self.assertNotIn(non_bodyguard, self.player2.discard_pile, "Non-bodyguard should not have been challenged.")

    def test_ai_uses_support(self):
        """Verify AI quests with Support and applies bonus correctly."""
        ability = {'trigger': 'Passive', 'effect': 'GainKeyword', 'target': 'Self', 'value': {'keyword': 'Support'}, 'notes': ''}
        supporter = Card(create_mock_card_data("Supporter", "sup-1", Strength=2, Willpower=2, Abilities=[ability]), 1)
        recipient = Card(create_mock_card_data("Recipient", "rec-1", Strength=3, Willpower=3), 1)
        self.player1.play_area.extend([supporter, recipient])
        supporter.turn_played = 1
        recipient.turn_played = 1

        # AI should quest with both, and the supporter should target the recipient
        player_logic.run_main_phase(self.game, self.player1)

        self.assertTrue(supporter.is_exerted, "Supporter should have quested.")
        self.assertEqual(self.player1.temporary_strength_mods.get(recipient.unique_id, 0), 2, "Recipient should have received the support bonus.")


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

    def test_run_main_phase_sings_song(self):
        """Verify the AI chooses to sing a song if it's a good option."""
        # Setup: P1 has a singer and a song in hand.
        song_card = Card(create_mock_card_data("My Song", "song-1", Type='Song', Cost=2, Inkable=False), 1)
        singer_ability = {
            "trigger": "Passive", "effect": "GainKeyword", "target": "Self",
            "value": {"keyword": "Singer", "amount": 3}, "notes": "Singer 3"
        }
        singer_char = Card(create_mock_card_data("Ariel", "ariel-1", Abilities=[singer_ability]), 1)
        singer_char.turn_played = 0 # Ink dry
        
        self.player1.hand.append(song_card)
        self.player1.play_area.append(singer_char)

        player_logic.run_main_phase(self.game, self.player1)

        # Verification: AI should have sung the song.
        self.assertTrue(singer_char.is_exerted, "Singer should be exerted from singing.")
        self.assertIn(song_card, self.player1.discard_pile, "Song should be in the discard pile.")
        self.assertNotIn(song_card, self.player1.hand, "Song should not be in hand.")

if __name__ == '__main__':
    unittest.main()
