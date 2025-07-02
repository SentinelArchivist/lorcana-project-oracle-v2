import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from src.game_engine.game_engine import GameState, Player, Card, Deck
from src.game_engine.player_logic import run_main_phase, get_possible_actions, evaluate_actions, ChallengeAction, PlayCardAction
from src.abilities.create_abilities_database import ParsedAbility

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

    def test_ai_chooses_to_activate_ability(self):
        """AI should choose to use a high-value activated ability like drawing a card."""
        # Create a character with an activated ability to draw a card
        ability_data = {"trigger": "Activated", "effect": "DrawCard", "target": "Player", "value": 1}
        char_data = create_mock_card_data("Wise Owl", Abilities=[ability_data])
        character = Card(char_data, self.player1.player_id)
        character.turn_played = 1
        self.player1.play_area.append(character)

        # Mock the relevant methods
        with patch.object(Player, 'activate_ability') as mock_activate_ability, \
             patch.object(Player, 'quest') as mock_quest:
            
            # Set a side effect for activate_ability to simulate exertion
            def activate_side_effect(char, index, turn):
                char.is_exerted = True
                return True
            mock_activate_ability.side_effect = activate_side_effect

            run_main_phase(self.game, self.player1)

            # Assert that the AI chose to activate the ability
            mock_activate_ability.assert_called_once_with(character, 0, self.game.turn_number)
            
            # Assert that the AI did not quest, since drawing a card is a higher priority
            mock_quest.assert_not_called()

    def test_ai_is_forced_to_challenge_with_reckless_character(self):
        """AI must challenge with a Reckless character if there is a valid target."""
        # Setup: A reckless character that could quest for a lot of lore
        reckless_char_data = create_mock_card_data("Reckless Attacker", Strength=1, Willpower=3, Lore=5, Keywords=['Reckless'])
        reckless_char = Card(reckless_char_data, self.player1.player_id)
        reckless_char.turn_played = 1
        self.player1.play_area.append(reckless_char)

        # A valid, but not particularly valuable, target
        defender_data = create_mock_card_data("Defender", Strength=1, Willpower=1, Lore=1)
        defender = Card(defender_data, self.player2.player_id)
        defender.is_exerted = True
        self.player2.play_area.append(defender)

        with patch.object(GameState, 'challenge') as mock_challenge, \
             patch.object(Player, 'quest') as mock_quest:

            # Simulate the challenge outcome
            def challenge_side_effect(attacker, defender):
                attacker.is_exerted = True
                return True, True # Both survive
            mock_challenge.side_effect = challenge_side_effect

            run_main_phase(self.game, self.player1)

            # Assert that the AI was forced to challenge
            mock_challenge.assert_called_once_with(reckless_char, defender)
            mock_quest.assert_not_called()

    def test_ai_considers_shift_action(self):
        """AI should generate a PlayCardAction with a shift_target if possible."""
        # 1. Setup
        # Player 1 has a character in play that can be shifted onto
        base_char_data = create_mock_card_data('Mickey Mouse, Friendly Face', Cost=1)
        base_char = Card(base_char_data, self.player1.player_id)
        self.player1.play_area.append(base_char)

        # Player 1 has a shift character in hand
        shift_char_data = create_mock_card_data('Mickey Mouse, Brave Little Tailor', Cost=7, Keywords=['Shift 5'])
        shift_char = Card(shift_char_data, self.player1.player_id)
        self.player1.hand.append(shift_char)

        # Player has enough ink for shift, but not full cost
        self.player1.inkwell = [Card(create_mock_card_data(f"Ink {i}", Inkable=True), self.player1.player_id) for i in range(6)]

        # 2. Action
        actions = get_possible_actions(self.game, self.player1, has_inked=True)

        # 3. Assert
        play_actions = [a for a in actions if isinstance(a, PlayCardAction)]

        # Debugging assertions to trace the logic
        self.assertTrue(shift_char.has_keyword('Shift'), "Card should have Shift keyword")
        shift_cost = shift_char.get_keyword_value('Shift')
        self.assertEqual(shift_cost, 5, "Shift cost should be 5")
        self.assertGreaterEqual(self.player1.get_available_ink(), shift_cost, "Player should have enough ink for shift")
        shift_targets = self.player1.get_possible_shift_targets(shift_char)
        self.assertEqual(len(shift_targets), 1, "Should find one valid shift target")
        self.assertIn(base_char, shift_targets, "The character in play should be a valid shift target")

        # Final assertion: The only valid play is the shift action
        self.assertEqual(len(play_actions), 1, "Should only find one possible play action")
        shift_action = play_actions[0]

        self.assertEqual(shift_action.card, shift_char, "The action should be for the shift character")
        self.assertEqual(shift_action.shift_target, base_char, "The action should target the base character for shifting")


if __name__ == '__main__':
    unittest.main()
