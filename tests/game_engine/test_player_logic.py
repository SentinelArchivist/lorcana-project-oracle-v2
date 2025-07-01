import unittest
from unittest.mock import patch

from src.game_engine.game_engine import GameState, Player, Card, Deck
from src.game_engine.player_logic import run_main_phase, get_possible_actions, evaluate_actions, ChallengeAction

def create_mock_card_data(name: str, **kwargs) -> dict:
    """Creates a dictionary for card data with sensible defaults."""
    data = {
        'Name': name,
        'Cost': 1,
        'Inkable': False,
        'Type': 'Character',
        'Strength': 1,
        'Willpower': 1,
        'Lore': 1,
        'Abilities': []
    }
    data.update(kwargs)
    return data

class TestNewPlayerLogic(unittest.TestCase):
    def setUp(self):
        """Set up a basic game state for testing."""
        self.player1 = Player(player_id=1, deck=Deck([]))
        self.player2 = Player(player_id=2, deck=Deck([]))
        self.game = GameState(self.player1, self.player2)
        self.game.turn_number = 3 # Give characters time to be ready

    def test_challenge_evaluation_favorable_trade(self):
        """AI should choose a challenge that banishes a high-value target, even if it loses its character."""
        attacker_data = create_mock_card_data("Attacker", Strength=3, Willpower=3, Lore=1, Cost=3)
        attacker = Card(attacker_data, self.player1.player_id)
        attacker.turn_played = 1
        self.player1.play_area.append(attacker)

        defender_data = create_mock_card_data("Defender", Strength=2, Willpower=2, Lore=3, Cost=4)
        defender = Card(defender_data, self.player2.player_id)
        defender.is_exerted = True
        self.player2.play_area.append(defender)

        actions = get_possible_actions(self.game, self.player1, has_inked=True)
        challenge_actions = [a for a in actions if isinstance(a, ChallengeAction)]
        self.assertEqual(len(challenge_actions), 1)

        evaluate_actions(challenge_actions, self.game, self.player1)
        self.assertGreater(challenge_actions[0].score, 0)

    def test_challenge_evaluation_unfavorable_trade(self):
        """AI should avoid a challenge where it loses its character for no gain."""
        attacker_data = create_mock_card_data("Attacker", Strength=1, Willpower=1, Lore=1, Cost=1)
        attacker = Card(attacker_data, self.player1.player_id)
        attacker.turn_played = 1
        self.player1.play_area.append(attacker)

        defender_data = create_mock_card_data("Defender", Strength=5, Willpower=5, Lore=2, Cost=5)
        defender = Card(defender_data, self.player2.player_id)
        defender.is_exerted = True
        self.player2.play_area.append(defender)

        actions = get_possible_actions(self.game, self.player1, has_inked=True)
        challenge_actions = [a for a in actions if isinstance(a, ChallengeAction)]
        self.assertEqual(len(challenge_actions), 1)

        evaluate_actions(challenge_actions, self.game, self.player1)
        self.assertLess(challenge_actions[0].score, 0)

    def test_quest_action_is_preferred_over_bad_trade(self):
        """If the only challenge is a bad trade, AI should quest instead."""
        character_data = create_mock_card_data("Quester", Strength=1, Willpower=1, Lore=2, Cost=1)
        character = Card(character_data, self.player1.player_id)
        character.turn_played = 1
        self.player1.play_area.append(character)

        defender_data = create_mock_card_data("Defender", Strength=5, Willpower=5, Lore=2, Cost=5)
        defender = Card(defender_data, self.player2.player_id)
        defender.is_exerted = True
        self.player2.play_area.append(defender)

        # This side effect simulates the real method's behavior of exerting the character
        def quest_side_effect(character_to_quest, turn_number, support_target):
            character_to_quest.is_exerted = True
            return True

        with patch.object(GameState, 'challenge') as mock_challenge, \
             patch.object(Player, 'quest', side_effect=quest_side_effect) as mock_quest:
            run_main_phase(self.game, self.player1)
            # The AI should have chosen to quest, with the correct arguments
            mock_quest.assert_called_once_with(character, self.game.turn_number, None)
            mock_challenge.assert_not_called()

    def test_ai_performs_multiple_actions_in_one_turn(self):
        """AI should be able to ink, play a card, and quest in the same turn."""
        ink_card_data = create_mock_card_data("Inky", Cost=3, Inkable=True)
        ink_card = Card(ink_card_data, self.player1.player_id)
        play_card_data = create_mock_card_data("New Guy", Type="Character", Cost=1, Strength=1, Willpower=1, Lore=1)
        play_card = Card(play_card_data, self.player1.player_id)
        self.player1.hand = [ink_card, play_card]

        quest_char_data = create_mock_card_data("Old Guy", Type="Character", Cost=1, Strength=1, Willpower=1, Lore=1)
        quest_char = Card(quest_char_data, self.player1.player_id)
        quest_char.turn_played = 1
        self.player1.play_area.append(quest_char)

        ink_source_data = create_mock_card_data("Ink Source")
        self.player1.inkwell.append(Card(ink_source_data, self.player1.player_id))

        initial_lore = self.player1.lore
        run_main_phase(self.game, self.player1)

        self.assertEqual(len(self.player1.inkwell), 2)
        self.assertNotIn(ink_card, self.player1.hand)

        self.assertEqual(len(self.player1.play_area), 2)
        new_guy_in_play = any(c.name == "New Guy" for c in self.player1.play_area)
        self.assertTrue(new_guy_in_play)
        self.assertNotIn(play_card, self.player1.hand)

        self.assertEqual(self.player1.lore, initial_lore + 1)
        self.assertTrue(quest_char.is_exerted)

if __name__ == '__main__':
    unittest.main()
