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
        """Test that _get_targets correctly resolves 'Self' to the source card itself."""
        # 1. Setup
        source_card = Mock(spec=Card)
        source_card.owner_player_id = self.player1.player_id
        effect_schema = {'target': 'Self'}

        # 2. Action
        targets = self.resolver._get_targets(effect_schema, source_card)

        # 3. Assert
        # Verify that the source card itself is returned, not the player
        # This matches the implementation where effects like DrawCard then
        # look up the owner of the card to apply the effect
        self.assertEqual(targets, [source_card])

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

    def test_get_targets_all_characters(self):
        """Test that _get_targets correctly resolves 'AllCharacters' to all characters in play."""
        # 1. Setup
        source_card = Mock(spec=Card)
        source_card.owner_player_id = self.player1.player_id

        # Setup mock play areas
        player1_character = Mock(spec=Card)
        player2_character = Mock(spec=Card)
        self.player1.play_area = [player1_character]
        self.player2.play_area = [player2_character]

        # Set up the game to return the appropriate players
        self.game.get_player = MagicMock(return_value=self.player1)
        self.game.get_opponent = MagicMock(return_value=self.player2)

        effect_schema = {'target': 'AllCharacters'}

        # 2. Action
        targets = self.resolver._get_targets(effect_schema, source_card)

        # 3. Assert
        self.assertEqual(len(targets), 2)
        self.assertIn(player1_character, targets)
        self.assertIn(player2_character, targets)

    def test_get_targets_opponent_characters(self):
        """Test that _get_targets correctly resolves 'OpponentCharacters' to opponent's characters."""
        # 1. Setup
        source_card = Mock(spec=Card)
        source_card.owner_player_id = self.player1.player_id

        # Setup mock play areas
        player1_character = Mock(spec=Card)
        player2_character = Mock(spec=Card)
        self.player1.play_area = [player1_character]
        self.player2.play_area = [player2_character]

        # Set up the game to return the appropriate players
        self.game.get_player = MagicMock(return_value=self.player1)
        self.game.get_opponent = MagicMock(return_value=self.player2)

        effect_schema = {'target': 'OpponentCharacters'}

        # 2. Action
        targets = self.resolver._get_targets(effect_schema, source_card)

        # 3. Assert
        self.assertEqual(len(targets), 1)
        self.assertIn(player2_character, targets)

    def test_get_targets_friendly_characters(self):
        """Test that _get_targets correctly resolves 'FriendlyCharacters' to controller's characters."""
        # 1. Setup
        source_card = Mock(spec=Card)
        source_card.owner_player_id = self.player1.player_id

        # Setup mock play areas
        player1_character = Mock(spec=Card)
        player2_character = Mock(spec=Card)
        self.player1.play_area = [player1_character]
        self.player2.play_area = [player2_character]

        # Set up the game to return the appropriate players
        self.game.get_player = MagicMock(return_value=self.player1)
        self.game.get_opponent = MagicMock(return_value=self.player2)

        effect_schema = {'target': 'FriendlyCharacters'}

        # 2. Action
        targets = self.resolver._get_targets(effect_schema, source_card)

        # 3. Assert
        self.assertEqual(len(targets), 1)
        self.assertIn(player1_character, targets)

    def test_get_targets_opponent(self):
        """Test that _get_targets correctly resolves 'Opponent' to the opponent player."""
        # 1. Setup
        source_card = Mock(spec=Card)
        source_card.owner_player_id = self.player1.player_id

        # Set up the game to return the appropriate players
        self.game.get_player = MagicMock(return_value=self.player1)
        self.game.get_opponent = MagicMock(return_value=self.player2)

        effect_schema = {'target': 'Opponent'}

        # 2. Action
        targets = self.resolver._get_targets(effect_schema, source_card)

        # 3. Assert
        self.assertEqual(len(targets), 1)
        self.assertEqual(targets[0], self.player2)

    def test_get_targets_controller(self):
        """Test that _get_targets correctly resolves 'Controller' to the controller player."""
        # 1. Setup
        source_card = Mock(spec=Card)
        source_card.owner_player_id = self.player1.player_id

        # Set up the game to return the appropriate players
        self.game.get_player = MagicMock(return_value=self.player1)
        self.game.get_opponent = MagicMock(return_value=self.player2)

        effect_schema = {'target': 'Controller'}

        # 2. Action
        targets = self.resolver._get_targets(effect_schema, source_card)

        # 3. Assert
        self.assertEqual(len(targets), 1)
        self.assertEqual(targets[0], self.player1)

    def test_get_targets_with_cost_filter(self):
        """Test filtering targets by cost."""
        # 1. Setup
        source_card = Mock(spec=Card)
        source_card.owner_player_id = self.player1.player_id

        # Create mock cards with different costs
        low_cost_card = Mock(spec=Card)
        low_cost_card.cost = 2
        high_cost_card = Mock(spec=Card)
        high_cost_card.cost = 5

        # Setup mock play area
        self.player2.play_area = [low_cost_card, high_cost_card]

        # Set up the game to return the appropriate players
        self.game.get_player = MagicMock(return_value=self.player1)
        self.game.get_opponent = MagicMock(return_value=self.player2)

        effect_schema = {'target': 'OpponentCharacters', 'cost_less_than': 3}

        # 2. Action
        targets = self.resolver._get_targets(effect_schema, source_card)

        # 3. Assert
        self.assertEqual(len(targets), 1)
        self.assertIn(low_cost_card, targets)
        self.assertNotIn(high_cost_card, targets)

    def test_get_targets_with_exerted_filter(self):
        """Test filtering targets by exerted status."""
        # 1. Setup
        source_card = Mock(spec=Card)
        source_card.owner_player_id = self.player1.player_id

        # Create mock cards with different exerted status
        exerted_card = Mock(spec=Card)
        exerted_card.is_exerted = True
        ready_card = Mock(spec=Card)
        ready_card.is_exerted = False

        # Setup mock play area
        self.player2.play_area = [exerted_card, ready_card]

        # Set up the game to return the appropriate players
        self.game.get_player = MagicMock(return_value=self.player1)
        self.game.get_opponent = MagicMock(return_value=self.player2)

        effect_schema = {'target': 'OpponentCharacters', 'is_exerted': True}

        # 2. Action
        targets = self.resolver._get_targets(effect_schema, source_card)

        # 3. Assert
        self.assertEqual(len(targets), 1)
        self.assertIn(exerted_card, targets)
        self.assertNotIn(ready_card, targets)

    def test_get_targets_with_keyword_filter(self):
        """Test filtering targets by keyword."""
        # 1. Setup
        source_card = Mock(spec=Card)
        source_card.owner_player_id = self.player1.player_id

        # Create mock cards with different keywords
        evasive_card = Mock(spec=Card)
        evasive_card.has_keyword = MagicMock(return_value=True)
        non_evasive_card = Mock(spec=Card)
        non_evasive_card.has_keyword = MagicMock(return_value=False)

        # Setup mock play area
        self.player2.play_area = [evasive_card, non_evasive_card]

        # Set up the game to return the appropriate players
        self.game.get_player = MagicMock(return_value=self.player1)
        self.game.get_opponent = MagicMock(return_value=self.player2)

        effect_schema = {'target': 'OpponentCharacters', 'has_keyword': 'Evasive'}

        # 2. Action
        targets = self.resolver._get_targets(effect_schema, source_card)

        # 3. Assert
        self.assertEqual(len(targets), 1)
        self.assertIn(evasive_card, targets)
        self.assertNotIn(non_evasive_card, targets)
        evasive_card.has_keyword.assert_called_once_with('Evasive')

    def test_get_targets_with_multiple_filters(self):
        """Test filtering targets by multiple criteria."""
        # 1. Setup
        source_card = Mock(spec=Card)
        source_card.owner_player_id = self.player1.player_id

        # Create mock cards with various properties
        card1 = Mock(spec=Card)
        card1.cost = 2
        card1.is_exerted = True
        card1.has_keyword = MagicMock(return_value=True)
        card1.card_type = 'Character'

        card2 = Mock(spec=Card)
        card2.cost = 2
        card2.is_exerted = False
        card2.has_keyword = MagicMock(return_value=True)
        card2.card_type = 'Character'

        card3 = Mock(spec=Card)
        card3.cost = 4
        card3.is_exerted = True
        card3.has_keyword = MagicMock(return_value=True)
        card3.card_type = 'Character'

        # Setup mock play area
        self.player2.play_area = [card1, card2, card3]

        # Set up the game to return the appropriate players
        self.game.get_player = MagicMock(return_value=self.player1)
        self.game.get_opponent = MagicMock(return_value=self.player2)

        effect_schema = {
            'target': 'OpponentCharacters', 
            'cost_less_than': 3, 
            'is_exerted': True,
            'has_keyword': 'Evasive',
            'card_type': 'Character'
        }

        # 2. Action
        targets = self.resolver._get_targets(effect_schema, source_card)

        # 3. Assert
        self.assertEqual(len(targets), 1)
        self.assertIn(card1, targets)
        self.assertNotIn(card2, targets)  # Not exerted
        self.assertNotIn(card3, targets)  # Cost too high


if __name__ == '__main__':
    unittest.main()
