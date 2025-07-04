import unittest
from unittest.mock import Mock, MagicMock

# Imports from the main source code
from src.game_engine.game_engine import GameState, Player, Card
from src.game_engine.effect_resolver import EffectResolver


class TestEffectResolver(unittest.TestCase):
    def setUp(self):
        """Set up a basic game state for testing."""
        self.game = Mock(spec=GameState)
        self.player1 = Mock(spec=Player)
        self.player1.player_id = 1
        self.player2 = Mock(spec=Player)
        self.player2.player_id = 2
        self.game.players = {1: self.player1, 2: self.player2}
        self.player1.opponent = self.player2
        self.player2.opponent = self.player1

        # Pass the Card and Player classes to the resolver
        self.resolver = EffectResolver(self.game, Card, Player)

    def test_resolver_initialization(self):
        """Test that the EffectResolver initializes correctly."""
        self.assertIsNotNone(self.resolver)
        self.assertEqual(self.resolver.game, self.game)
        self.assertEqual(self.resolver.Card, Card)
        self.assertEqual(self.resolver.Player, Player)

    def test_resolve_deal_damage_calls_take_damage(self):
        """Test that resolving 'DealDamage' calls the take_damage method on the target."""
        # 1. Setup
        source_card = Mock(spec=Card)
        target_card = Mock(spec=Card)
        target_card.take_damage = MagicMock()

        schema_ability = {
            "effect": "DealDamage",
            "value": 3,
            "target": "ChosenCharacter"
        }

        # 2. Action
        self.resolver.resolve_effect(schema_ability, source_card, chosen_targets=[target_card])

        # 3. Assert
        target_card.take_damage.assert_called_once_with(3)

    def test_resolve_draw_card_calls_draw_cards(self):
        """Test that resolving 'DrawCard' calls the draw_cards method on the target player."""
        # 1. Setup
        source_card = Mock(spec=Card)
        source_card.owner_player_id = self.player1.player_id

        target_player = self.player1
        target_player.draw_cards = MagicMock()

        schema_ability = {
            "effect": "DrawCard",
            "value": 2,
            "target": "Self"
        }

        # Mock the game state to return the correct player
        self.game.get_player = MagicMock(return_value=target_player)

        # 2. Action
        self.resolver.resolve_effect(schema_ability, source_card)

        # 3. Assert
        self.game.get_player.assert_called_once_with(self.player1.player_id)
        target_player.draw_cards.assert_called_once_with(2)

    def test_get_targets_self(self):
        """Test that _get_targets correctly resolves 'Self' to the source card's owner."""
        # 1. Setup
        source_card = Mock(spec=Card)
        source_card.owner_player_id = self.player1.player_id
        effect_schema = {'target': 'Self'}

        # Mock the game state to return the correct player
        self.game.get_player = MagicMock(return_value=self.player1)

        # 2. Action
        targets = self.resolver._get_targets(effect_schema, source_card)

        # 3. Assert
        self.game.get_player.assert_called_once_with(self.player1.player_id)
        self.assertEqual(targets, [self.player1])

    def test_resolve_banish_calls_banish_character(self):
        """Test that resolving 'Banish' calls the banish_character method on the target's owner."""
        # 1. Setup
        source_card = Mock(spec=Card)
        target_card = Mock(spec=Card)
        target_card.owner_player_id = self.player2.player_id

        owner_player = self.player2
        owner_player.banish_character = MagicMock()
        self.game.get_player = MagicMock(return_value=owner_player)

        schema_ability = {
            "effect": "Banish",
            "target": "ChosenCharacter"
        }

        # 2. Action
        self.resolver.resolve_effect(schema_ability, source_card, chosen_targets=[target_card])

        # 3. Assert
        self.game.get_player.assert_called_once_with(self.player2.player_id)
        owner_player.banish_character.assert_called_once_with(target_card)

    def test_resolve_gain_strength_adds_modifier(self):
        """Test that resolving 'GainStrength' adds a modifier to the target card's strength_modifiers list."""
        # 1. Setup
        source_card = Mock(spec=Card)
        source_card.owner_player_id = self.player1.player_id
        target_card = Mock(spec=Card)
        target_card.strength_modifiers = []

        schema_ability = {
            "effect": "GainStrength",
            "value": 2,
            "target": "ChosenCharacter",
            "duration": "start_of_turn"
        }

        # 2. Action
        self.resolver.resolve_effect(schema_ability, source_card, chosen_targets=[target_card])

        # 3. Assert
        self.assertEqual(len(target_card.strength_modifiers), 1)
        modifier = target_card.strength_modifiers[0]
        self.assertEqual(modifier['strength'], 2)
        self.assertEqual(modifier['duration'], 'start_of_turn')
        self.assertEqual(modifier['player_id'], self.player1.player_id)

    def test_resolve_return_to_hand_calls_return_to_hand(self):
        """Test that resolving 'ReturnToHand' calls the return_to_hand method on the target's owner."""
        # 1. Setup
        source_card = Mock(spec=Card)
        target_card = Mock(spec=Card)
        target_card.owner_player_id = self.player2.player_id

        owner_player = self.player2
        owner_player.return_to_hand = MagicMock()
        self.game.get_player = MagicMock(return_value=owner_player)

        schema_ability = {
            "effect": "ReturnToHand",
            "target": "ChosenCharacter"
        }

        # 2. Action
        self.resolver.resolve_effect(schema_ability, source_card, chosen_targets=[target_card])

        # 3. Assert
        self.game.get_player.assert_called_once_with(self.player2.player_id)
        owner_player.return_to_hand.assert_called_once_with(target_card)

    def test_resolve_gain_keyword_adds_modifier(self):
        """Test that resolving 'GainKeyword' adds a modifier to the target card's keyword_modifiers list."""
        # 1. Setup
        source_card = Mock(spec=Card)
        source_card.owner_player_id = self.player1.player_id
        target_card = Mock(spec=Card)
        target_card.keyword_modifiers = []

        schema_ability = {
            "effect": "GainKeyword",
            "value": "Evasive",
            "target": "ChosenCharacter",
            "duration": "start_of_turn"
        }

        # 2. Action
        self.resolver.resolve_effect(schema_ability, source_card, chosen_targets=[target_card])

        # 3. Assert
        self.assertEqual(len(target_card.keyword_modifiers), 1)
        modifier = target_card.keyword_modifiers[0]
        self.assertEqual(modifier['keyword'], 'Evasive')
        self.assertEqual(modifier['duration'], 'start_of_turn')
        self.assertEqual(modifier['player_id'], self.player1.player_id)

    def test_resolve_add_keyword_effect(self):
        """Test that resolving ADD_KEYWORD adds the keyword to the card's keyword set."""
        # 1. Setup
        source_card = Mock(spec=Card)
        target_card = Mock(spec=Card)
        target_card.keywords = set()

        schema_ability = {
            "effect": "ADD_KEYWORD",
            "value": "Evasive",
            "target": "ChosenCharacter"
        }

        # 2. Action
        self.resolver.resolve_effect(schema_ability, source_card, chosen_targets=[target_card])

        # 3. Assert
        self.assertIn("Evasive", target_card.keywords)

    def test_resolve_add_keyword_with_value_effect(self):
        """Test ADD_KEYWORD for keywords with numeric values (e.g., Resist +1)."""
        # 1. Setup
        source_card = Mock(spec=Card)
        target_card = Mock(spec=Card)
        target_card.keywords = set()

        schema_ability = {
            "effect": "ADD_KEYWORD",
            "value": "Resist +1",
            "target": "ChosenCharacter"
        }

        # 2. Action
        self.resolver.resolve_effect(schema_ability, source_card, chosen_targets=[target_card])

        # 3. Assert
        self.assertIn("Resist +1", target_card.keywords)

    def test_resolve_set_shift_cost_effect(self):
        """Test that SET_SHIFT_COST adds 'Shift X' to the card's keywords."""
        # 1. Setup
        source_card = Mock(spec=Card)
        target_card = Mock(spec=Card)
        target_card.keywords = set()

        schema_ability = {
            "effect": "SET_SHIFT_COST",
            "value": 2,
            "target": "Self"
        }

        self.resolver._get_targets = MagicMock(return_value=[target_card])

        # 2. Action
        self.resolver.resolve_effect(schema_ability, source_card)

        # 3. Assert
        self.assertIn("Shift 2", target_card.keywords)
        self.resolver._get_targets.assert_called_once_with(schema_ability, source_card, None)

    def test_resolve_singer_effect(self):
        """Test that SINGER adds 'Singer X' to the card's keywords."""
        # 1. Setup
        source_card = Mock(spec=Card)
        target_card = Mock(spec=Card)
        target_card.keywords = set()

        schema_ability = {
            "effect": "SINGER",
            "value": 4,
            "target": "Self"
        }

        self.resolver._get_targets = MagicMock(return_value=[target_card])

        # 2. Action
        self.resolver.resolve_effect(schema_ability, source_card)

        # 3. Assert
        self.assertIn("Singer 4", target_card.keywords)
        self.resolver._get_targets.assert_called_once_with(schema_ability, source_card, None)


if __name__ == '__main__':
    unittest.main()
