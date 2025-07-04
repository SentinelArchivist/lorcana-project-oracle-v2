import unittest
import sys
import os
from unittest.mock import MagicMock, patch, call
import json

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from src.game_engine.game_engine import GameState, Player, Card, Deck

# --- Test Fixtures ---

def create_mock_card_data(name: str, unique_id: str, **kwargs) -> dict:
    """Helper function to create mock card data for tests."""
    data = {
        'Name': name, 'Unique_ID': unique_id, 'Cost': 3, 'Inkable': True,
        'Strength': 2, 'Willpower': 4, 'Lore': 1, 'Type': 'Character',
        'schema_abilities': []
    }
    if 'Abilities' in kwargs:
        kwargs['schema_abilities'] = kwargs.pop('Abilities')
    data.update(kwargs)
    return data

def create_mock_deck(player_id: int, num_cards: int = 60) -> Deck:
    cards = [Card(create_mock_card_data(f"Card {i}", f"P{player_id}-{i}", Inkable=(i % 2 == 0)), player_id) for i in range(num_cards)]
    return Deck(cards)

# --- Test Cases ---

class TestKeywords(unittest.TestCase):
    def setUp(self):
        """Set up a basic game state for each test."""
        self.p1_deck = Deck([Card(create_mock_card_data(f"P1-Card{i}", f"p1c{i}"), 1) for i in range(20)])
        self.p2_deck = Deck([Card(create_mock_card_data(f"P2-Card{i}", f"p2c{i}"), 2) for i in range(20)])
        self.game = GameState(self.p1_deck, self.p2_deck)
        self.player1 = self.game.players[1]
        self.player2 = self.game.players[2]
        self.game.turn_number = 2  # Avoid turn 1 draw skip

    def test_challenge_with_challenger(self):
        """Verify Challenger keyword adds strength to attacker."""
        ability = {'trigger': 'Passive', 'effect': 'GainKeyword', 'target': 'Self', 'value': {'keyword': 'Challenger', 'amount': 2}, 'notes': ''}
        attacker = Card(create_mock_card_data("Attacker", "a-1", Strength=2, Willpower=3, Abilities=[ability]), 1)
        defender = Card(create_mock_card_data("Defender", "d-1", Strength=1, Willpower=5), 2)
        self.player1.play_area.append(attacker)
        self.player2.play_area.append(defender)
        attacker.turn_played = 1
        defender.is_exerted = True

        self.game.challenge(attacker, defender)
        self.assertEqual(defender.damage_counters, 4, "Defender should take 4 damage (2 base + 2 Challenger).")

    def test_challenge_with_resist(self):
        """Verify Resist keyword reduces damage taken."""
        ability = {'trigger': 'Passive', 'effect': 'GainKeyword', 'target': 'Self', 'value': {'keyword': 'Resist', 'amount': 1}, 'notes': ''}
        attacker = Card(create_mock_card_data("Attacker", "a-1", Strength=3, Willpower=3), 1)
        defender = Card(create_mock_card_data("Defender", "d-1", Strength=1, Willpower=5, Abilities=[ability]), 2)
        self.player1.play_area.append(attacker)
        self.player2.play_area.append(defender)
        attacker.turn_played = 1
        defender.is_exerted = True

        self.game.challenge(attacker, defender)
        self.assertEqual(defender.damage_counters, 2, "Defender should take 2 damage (3 base - 1 Resist).")

    def test_challenge_bodyguard_rule(self):
        """Verify Bodyguard rule is enforced."""
        ability = {'trigger': 'Passive', 'effect': 'GainKeyword', 'target': 'Self', 'value': {'keyword': 'Bodyguard'}, 'notes': ''}
        attacker = Card(create_mock_card_data("Attacker", "a-1", Strength=1, Willpower=1), 1)
        non_bodyguard = Card(create_mock_card_data("Target", "t-1", Strength=1, Willpower=2), 2)
        bodyguard = Card(create_mock_card_data("Bodyguard", "bg-1", Strength=1, Willpower=3, Abilities=[ability]), 2)
        self.player1.play_area.append(attacker)
        self.player2.play_area.extend([non_bodyguard, bodyguard])
        attacker.turn_played = 1
        non_bodyguard.is_exerted = True
        bodyguard.is_exerted = True

        # Trying to challenge the non-bodyguard should fail
        with self.assertRaises(ValueError, msg="Challenge should fail against non-bodyguard."):
            self.game.challenge(attacker, non_bodyguard)

        # Challenging the bodyguard should succeed
        self.assertTrue(self.game.challenge(attacker, bodyguard), "Challenge should succeed against bodyguard.")

    def test_quest_with_support(self):
        """Verify Support keyword grants temporary strength."""
        ability = {'trigger': 'Passive', 'effect': 'GainKeyword', 'target': 'Self', 'value': {'keyword': 'Support'}, 'notes': ''}
        supporter = Card(create_mock_card_data("Supporter", "sup-1", Strength=2, Willpower=2, Abilities=[ability]), 1)
        recipient = Card(create_mock_card_data("Recipient", "rec-1", Strength=3, Willpower=3), 1)
        self.player1.play_area.extend([supporter, recipient])
        supporter.turn_played = 1
        recipient.turn_played = 1

        self.player1.quest(supporter, self.game.turn_number, support_target=recipient)
        
        # Check temporary strength mod
        self.assertEqual(self.player1.temporary_strength_mods.get(recipient.unique_id, 0), 2, "Recipient should get +2 strength.")

        # Verify the bonus applies in a challenge
        defender = Card(create_mock_card_data("Defender", "d-1", Strength=1, Willpower=6), 2)
        self.player2.play_area.append(defender)
        defender.is_exerted = True
        self.game.challenge(recipient, defender)
        self.assertEqual(defender.damage_counters, 5, "Defender should take 5 damage (3 base + 2 Support).")

    def test_support_bonus_is_temporary(self):
        """Verify Support bonus is cleared at the end of the turn."""
        ability = {'trigger': 'Passive', 'effect': 'GainKeyword', 'target': 'Self', 'value': {'keyword': 'Support'}, 'notes': ''}
        supporter = Card(create_mock_card_data("Supporter", "sup-1", Strength=2, Willpower=2, Abilities=[ability]), 1)
        recipient = Card(create_mock_card_data("Recipient", "rec-1", Strength=3, Willpower=3), 1)
        self.player1.play_area.extend([supporter, recipient])
        supporter.turn_played = 1
        recipient.turn_played = 1

        self.player1.quest(supporter, self.game.turn_number, support_target=recipient)
        self.assertNotEqual(self.player1.temporary_strength_mods, {}, "Bonus should exist during the turn.")

        self.game.end_turn()
        self.assertEqual(self.player1.temporary_strength_mods, {}, "Bonus should be cleared after the turn ends.")


class TestPlayerActions(unittest.TestCase):
    """Test suite for all core player actions."""
    def setUp(self):
        p1_deck = create_mock_deck(player_id=1)
        p2_deck = create_mock_deck(player_id=2)
        self.game = GameState(p1_deck, p2_deck)
        self.player1 = self.game.players[1]
        self.player2 = self.game.players[2]
        self.player1.draw_initial_hand()
        self.player2.draw_initial_hand()

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
        self.player1.play_card(card_to_play, self.game)
        self.assertIn(card_to_play, self.player1.play_area)
        self.assertNotIn(card_to_play, self.player1.hand)
        self.assertEqual(self.player1.get_available_ink(), 0)

    def test_play_card_insufficient_ink(self):
        card_to_play = Card(create_mock_card_data("Expensive Card", "EC-1", Cost=5), 1)
        self.player1.hand.append(card_to_play)
        with self.assertRaises(ValueError):
            self.player1.play_card(card_to_play, self.game)
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

    def test_game_over_draw(self):
        """Verify a player loses if they must draw from an empty deck."""
        # It's player 1's turn, but not their first turn.
        self.game.turn_number = 2
        self.player1.deck.cards = []
        self.game._draw_phase() # Player 1 tries to draw
        self.assertEqual(self.game.winner, 2, "Player 2 should win if Player 1 decks out.")

    def test_play_action_card(self):
        """Verify playing an Action card moves it to discard."""
        action_card = Card(create_mock_card_data("Action Card", "ac-1", Type='Action', Cost=1), 1)
        self.player1.hand.append(action_card)
        # Give player ink
        ink = Card(create_mock_card_data("Ink", "i-1", Inkable=True), 1)
        self.player1.hand.append(ink)
        self.player1.ink_card(ink)
        self.game._ready_phase()

        self.player1.play_card(action_card, self.game)
        self.assertIn(action_card, self.player1.discard_pile)
        self.assertNotIn(action_card, self.player1.hand)
        self.assertNotIn(action_card, self.player1.play_area)

    def test_play_card_with_on_play_draw_effect(self):
        """Verify that playing a card with an ON_PLAY DrawCard effect works."""
        ability = {
            'trigger': 'ON_PLAY',
            'effect': 'DrawCard',
            'target': 'Self',
            'value': 1
        }
        action_card = Card(create_mock_card_data("Magic Mirror", "mm-1", Type='Action', Cost=1, Abilities=[ability]), 1)
        self.player1.hand.append(action_card)
        self.player1.inkwell.append(Card(create_mock_card_data("Ink Card", "ink-1"), 1))

        initial_hand_size = len(self.player1.hand)
        initial_deck_size = len(self.player1.deck.cards)

        self.player1.play_card(action_card, self.game)

        # Hand size should be the same (played 1, drew 1)
        self.assertEqual(len(self.player1.hand), initial_hand_size)
        # Deck size should decrease by 1
        self.assertEqual(len(self.player1.deck.cards), initial_deck_size - 1)
        # Action card should be in the discard pile
        self.assertIn(action_card, self.player1.discard_pile)

    def test_sing_song(self):
        """Verify a character with Singer can play a Song for free."""
        song_card = Card(create_mock_card_data("Test Song", "song-1", Type='Song', Cost=3), 1)
        singer_ability = {
            "trigger": "Passive", "effect": "GainKeyword", "target": "Self",
            "value": {"keyword": "Singer", "amount": 5}, "notes": "Singer 5"
        }
        singer_char = Card(create_mock_card_data("Singer Char", "singer-1", Abilities=[singer_ability]), 1)
        singer_char.turn_played = 0 # Ink is dry

        self.player1.hand.append(song_card)
        self.player1.play_area.append(singer_char)

        self.assertTrue(self.player1.sing_song(song_card, singer_char, self.game.turn_number))
        self.assertIn(song_card, self.player1.discard_pile)
        self.assertTrue(singer_char.is_exerted)
        self.assertEqual(self.player1.get_available_ink(), 0) # No ink should be spent

    def test_sing_song_invalid_cost(self):
        """Verify a Singer cannot sing a song that costs more than their value."""
        expensive_song = Card(create_mock_card_data("Expensive Song", "es-1", Type='Song', Cost=5), 1)
        singer_ability = {
            "trigger": "Passive", "effect": "GainKeyword", "target": "Self",
            "value": {"keyword": "Singer", "amount": 3}, "notes": "Singer 3"
        }
        singer_char = Card(create_mock_card_data("Weak Singer", "ws-1", Abilities=[singer_ability]), 1)
        singer_char.turn_played = 0

        self.player1.hand.append(expensive_song)
        self.player1.play_area.append(singer_char)

        self.assertFalse(self.player1.sing_song(expensive_song, singer_char, self.game.turn_number))
        self.assertIn(expensive_song, self.player1.hand)
        self.assertFalse(singer_char.is_exerted)

class TestEffectResolverIntegration(unittest.TestCase):
    def setUp(self):
        self.p1_deck = create_mock_deck(1)
        self.p2_deck = create_mock_deck(2)
        self.game = GameState(self.p1_deck, self.p2_deck)
        self.player1 = self.game.players[1]
        self.player2 = self.game.players[2]
        self.game.turn_number = 2

    def test_play_card_with_on_play_effect(self):
        """
        Integration test: Playing a card with an ON_PLAY effect should
        trigger the effect resolver and modify the game state.
        """
        # 1. Setup
        on_play_ability = {
            "trigger": "ON_PLAY",
            "effect": "ADD_KEYWORD",
            "value": "Evasive",
            "target": "ChosenCharacter"
        }
        schema_abilities_str = json.dumps([on_play_ability])

        ability_card_data = create_mock_card_data(
            "Fairy Godmother", "fg-1", Cost=1,
            schema_abilities=schema_abilities_str
        )
        ability_card = Card(ability_card_data, 1)
        self.player1.hand.append(ability_card)

        target_character = Card(create_mock_card_data("Cinderella", "c-1"), 2)
        self.player2.play_area.append(target_character)
        self.assertEqual(target_character.keywords, set())

        ink_card = Card(create_mock_card_data("Ink", "ink-1"), 1)
        self.player1.inkwell.append(ink_card)

        # 2. Action
        self.player1.play_card(ability_card, self.game, chosen_targets=[target_character])

        # 3. Assert
        self.assertIn(ability_card, self.player1.play_area)
        self.assertIn("Evasive", target_character.keywords)


if __name__ == '__main__':
    unittest.main()
