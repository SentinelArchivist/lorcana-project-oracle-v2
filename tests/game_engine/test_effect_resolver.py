import unittest
from unittest.mock import Mock, MagicMock

# Imports from the main source code
from src.game_engine.game_engine import GameState, Player, Card
from src.abilities.create_abilities_database import ParsedAbility
from src.game_engine.effect_resolver import EffectResolver


class TestEffectResolver(unittest.TestCase):
    def setUp(self):
        """Set up a basic game state for testing."""
        self.game = Mock(spec=GameState)
        self.player1 = Mock(spec=Player)
        self.player1.player_id = 1
        self.player2 = Mock(spec=Player)
        self.player2.player_id = 2
        self.game.players = [self.player1, self.player2]
        self.player1.opponent = self.player2
        self.player2.opponent = self.player1

        self.resolver = EffectResolver(self.game)

    def test_resolver_initialization(self):
        """Test that the EffectResolver initializes correctly."""
        self.assertIsNotNone(self.resolver)
        self.assertEqual(self.resolver.game, self.game)

    def test_resolve_deal_damage_calls_take_damage(self):
        """Test that resolving 'DealDamage' calls the take_damage method on the target."""
        # 1. Setup
        source_card = Mock(spec=Card)
        target_card = Mock(spec=Card)
        target_card.take_damage = MagicMock()  # Mock the method we expect to be called

        ability = ParsedAbility(
            trigger={'type': 'OnPlay'},
            effect='DealDamage',
            target='ChosenCharacter',
            value=3
        )

        # 2. Action
        # We pass the chosen target directly to the resolver
        self.resolver.resolve_ability(ability, source_card, chosen_targets=[target_card])

        # 3. Assert
        # Check that the take_damage method was called on the target with the correct value
        target_card.take_damage.assert_called_once_with(3)

    def test_resolve_draw_card_calls_draw_cards(self):
        """Test that resolving 'DrawCard' calls the draw_cards method on the target player."""
        # 1. Setup
        source_card = Mock(spec=Card)
        source_card.owner_player_id = self.player1.player_id

        target_player = self.player1
        target_player.draw_cards = MagicMock()

        ability = ParsedAbility(
            trigger={'type': 'OnPlay'},
            effect='DrawCard',
            target='Self',  # 'Self' should resolve to the player who owns the source_card
            value=2
        )

        # Mock the game state to return the correct player
        self.game.get_player = MagicMock(return_value=target_player)

        # 2. Action
        self.resolver.resolve_ability(ability, source_card)

        # 3. Assert
        # Check that the draw_cards method was called on the target player with the correct value
        self.game.get_player.assert_called_once_with(self.player1.player_id)
        target_player.draw_cards.assert_called_once_with(2)

    def test_get_targets_self(self):
        """Test that _get_targets correctly resolves 'Self' to the source card's owner."""
        # 1. Setup
        source_card = Mock(spec=Card)
        source_card.owner_player_id = self.player1.player_id

        # Mock the game state to return the correct player
        self.game.get_player = MagicMock(return_value=self.player1)

        ability = Mock(spec=ParsedAbility)

        # 2. Action
        targets = self.resolver._get_targets('Self', source_card, ability)

        # 3. Assert
        self.game.get_player.assert_called_once_with(self.player1.player_id)
        self.assertEqual(targets, [self.player1])

    def test_resolve_banish_calls_banish_character(self):
        """Test that resolving 'Banish' calls the banish_character method on the target's owner."""
        # 1. Setup
        source_card = Mock(spec=Card)
        target_card = Mock(spec=Card)
        target_card.owner_player_id = self.player2.player_id

        # The player who owns the character to be banished
        owner_player = self.player2
        owner_player.banish_character = MagicMock()

        ability = ParsedAbility(
            trigger={'type': 'OnPlay'},
            effect='Banish',
            target='ChosenCharacter',
            value=None
        )

        # Mock the game to return the correct owner
        self.game.get_player = MagicMock(return_value=owner_player)

        # 2. Action
        self.resolver.resolve_ability(ability, source_card, chosen_targets=[target_card])

        # 3. Assert
        self.game.get_player.assert_called_once_with(self.player2.player_id)
        owner_player.banish_character.assert_called_once_with(target_card)

    def test_resolve_gain_strength_adds_modifier(self):
        """Test that resolving 'GainStrength' adds a modifier to the target card's strength_modifiers list."""
        # 1. Setup
        source_card = Mock(spec=Card)
        source_card.owner_player_id = self.player1.player_id
        target_card = Mock(spec=Card)
        target_card.strength_modifiers = []  # Ensure it starts empty

        ability = ParsedAbility(
            trigger={'type': 'OnPlay'},
            effect='GainStrength',
            target='ChosenCharacter',
            value=2,
            duration='start_of_turn'  # e.g., until the start of your next turn
        )

        # 2. Action
        self.resolver.resolve_ability(ability, source_card, chosen_targets=[target_card])

        # 3. Assert
        self.assertEqual(len(target_card.strength_modifiers), 1)
        modifier = target_card.strength_modifiers[0]
        self.assertEqual(modifier['value'], 2)
        self.assertEqual(modifier['duration'], 'start_of_turn')
        self.assertIn('player_id', modifier)

    def test_resolve_return_to_hand_calls_return_to_hand(self):
        """Test that resolving 'ReturnToHand' calls the return_to_hand method on the target's owner."""
        # 1. Setup
        source_card = Mock(spec=Card)
        target_card = Mock(spec=Card)
        target_card.owner_player_id = self.player2.player_id

        owner_player = self.player2
        owner_player.return_to_hand = MagicMock()

        ability = ParsedAbility(
            trigger={'type': 'OnPlay'},
            effect='ReturnToHand',
            target='ChosenCharacter',
            value=None
        )

        self.game.get_player = MagicMock(return_value=owner_player)

        # 2. Action
        self.resolver.resolve_ability(ability, source_card, chosen_targets=[target_card])

        # 3. Assert
        self.game.get_player.assert_called_once_with(self.player2.player_id)
        owner_player.return_to_hand.assert_called_once_with(target_card)

    def test_resolve_gain_keyword_adds_modifier(self):
        """Test that resolving 'GainKeyword' adds a modifier to the target card's keyword_modifiers list."""
        # 1. Setup
        source_card = Mock(spec=Card)
        source_card.owner_player_id = self.player1.player_id
        target_card = Mock(spec=Card)
        target_card.keyword_modifiers = []  # Ensure it starts empty

        ability = ParsedAbility(
            trigger={'type': 'OnPlay'},
            effect='GainKeyword',
            target='ChosenCharacter',
            value='Evasive',
            duration='start_of_turn'
        )

        # 2. Action
        self.resolver.resolve_ability(ability, source_card, chosen_targets=[target_card])

        # 3. Assert
        self.assertEqual(len(target_card.keyword_modifiers), 1)
        modifier = target_card.keyword_modifiers[0]
        self.assertEqual(modifier['keyword'], 'Evasive')
        self.assertEqual(modifier['duration'], 'start_of_turn')
        self.assertEqual(modifier['player_id'], self.player1.player_id)


if __name__ == '__main__':
    unittest.main()
