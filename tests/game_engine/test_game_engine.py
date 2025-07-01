import unittest
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from game_engine.game_engine import Card, Deck, Player, GameState

# --- Test Fixtures ---

def create_mock_card_data(name: str, unique_id: str, **kwargs) -> dict:
    data = { 'Name': name, 'Unique_ID': unique_id, 'Cost': 3, 'Inkable': True, 'Strength': 2, 'Willpower': 4, 'Lore': 1 }
    data.update(kwargs)
    return data

def create_mock_deck(player_id: int, num_cards: int = 60) -> Deck:
    cards = [Card(create_mock_card_data(f"Card {i}", f"P{player_id}-{i}", Inkable=(i % 2 == 0)), player_id) for i in range(num_cards)]
    return Deck(cards)

# --- Test Cases ---

class TestPlayerActions(unittest.TestCase):
    """Test suite for all core player actions."""
    def setUp(self):
        p1_deck = create_mock_deck(player_id=1)
        p2_deck = create_mock_deck(player_id=2)
        self.player1 = Player(player_id=1, deck=p1_deck)
        self.player2 = Player(player_id=2, deck=p2_deck)
        self.player1.draw_initial_hand()
        self.player2.draw_initial_hand()
        self.game = GameState(self.player1, self.player2)

    def test_ink_card(self):
        inkable_card = next(c for c in self.player1.hand if c.inkable)
        non_inkable_card = next(c for c in self.player1.hand if not c.inkable)
        
        self.assertTrue(self.player1.ink_card(inkable_card))
        self.assertEqual(len(self.player1.inkwell), 1)
        self.assertEqual(self.player1.inkwell[0].location, 'inkwell')
        self.assertTrue(self.player1.inkwell[0].is_exerted)
        
        self.assertFalse(self.player1.ink_card(non_inkable_card))
        self.assertEqual(len(self.player1.inkwell), 1)

    def test_play_card(self):
        # Setup: Give player 1 some ink
        for _ in range(3):
            self.player1.inkwell.append(self.player1.deck.draw())
        self.game._ready_phase() # Ready the ink
        
        card_to_play = Card(create_mock_card_data("Playable Card", "PC-1", Cost=3), 1)
        self.player1.hand.append(card_to_play)

        self.assertEqual(self.player1.get_available_ink(), 3)
        self.assertTrue(self.player1.play_card(card_to_play, self.game.turn_number))
        self.assertEqual(len(self.player1.play_area), 1)
        self.assertEqual(self.player1.play_area[0].turn_played, self.game.turn_number)
        self.assertEqual(self.player1.get_available_ink(), 0)

    def test_play_card_insufficient_ink(self):
        card_to_play = Card(create_mock_card_data("Expensive Card", "EC-1", Cost=5), 1)
        self.player1.hand.append(card_to_play)
        self.assertFalse(self.player1.play_card(card_to_play, self.game.turn_number))
        self.assertEqual(len(self.player1.play_area), 0)

    def test_quest(self):
        character = Card(create_mock_card_data("Quester", "Q-1", Lore=2), 1)
        self.player1.play_area.append(character)
        character.turn_played = 0 # Mark as having been played on a previous turn

        self.assertTrue(self.player1.quest(character, self.game.turn_number))
        self.assertEqual(self.player1.lore, 2)
        self.assertTrue(character.is_exerted)

    def test_quest_fail_ink_not_dry(self):
        character = Card(create_mock_card_data("New Character", "NC-1", Lore=1), 1)
        self.player1.play_area.append(character)
        character.turn_played = self.game.turn_number # Just played this turn

        self.assertFalse(self.player1.quest(character, self.game.turn_number))
        self.assertEqual(self.player1.lore, 0)

    def test_challenge(self):
        attacker = Card(create_mock_card_data("Attacker", "A-1", Strength=3, Willpower=3), 1)
        defender = Card(create_mock_card_data("Defender", "D-1", Strength=2, Willpower=4), 2)
        
        self.player1.play_area.append(attacker)
        attacker.turn_played = 0 # Ink is dry
        self.player2.play_area.append(defender)
        defender.is_exerted = True # Can be challenged

        self.assertTrue(self.game.challenge(attacker, defender))
        self.assertTrue(attacker.is_exerted)
        self.assertEqual(attacker.damage_counters, 2)
        self.assertEqual(defender.damage_counters, 3)
        self.assertIn(attacker, self.player1.play_area)
        self.assertIn(defender, self.player2.play_area)

    def test_challenge_banishes_defender(self):
        attacker = Card(create_mock_card_data("Strong Attacker", "SA-1", Strength=5, Willpower=3), 1)
        defender = Card(create_mock_card_data("Weak Defender", "WD-1", Strength=2, Willpower=4), 2)

        self.player1.play_area.append(attacker)
        attacker.turn_played = 0
        self.player2.play_area.append(defender)
        defender.is_exerted = True

        self.game.challenge(attacker, defender)
        self.assertEqual(defender.damage_counters, 5)
        self.assertNotIn(defender, self.player2.play_area)
        self.assertIn(defender, self.player2.discard_pile)

if __name__ == '__main__':
    unittest.main()
