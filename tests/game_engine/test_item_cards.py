import unittest
from unittest.mock import Mock, MagicMock

from src.game_engine.game_engine import GameState, Player, Card
from src.abilities.create_abilities_database import ParsedAbility


class TestItemCards(unittest.TestCase):
    def setUp(self):
        """Set up a basic game state for testing item card interactions."""
        self.player1 = Player(player_id=1, deck=[])
        self.player2 = Player(player_id=2, deck=[])
        self.game = GameState(player1=self.player1, player2=self.player2)
        self.player1.game = self.game
        self.player2.game = self.game
        self.game.effect_resolver = Mock()

        # Mock the game state to control player turn
        self.game.current_player_id = 1

    def test_play_item_card(self):
        """Test that a player can play an item card from their hand."""
        # 1. Setup
        # Create an item card (e.g., Magic Mirror)
        item_card_data = {
            'Name': 'Magic Mirror',
            'Cost': 2,
            'Type': 'Item',
            'Inkable': True,
            'Body Text': 'You may pay 2 ink to draw a card.'
        }
        item_card = Card(item_card_data, owner_player_id=self.player1.player_id)
        item_card.abilities = [ParsedAbility(trigger={'primary_trigger': 'OnPlay'}, effect='None', target='None', value=None)] # Simplified

        # Put the card in player's hand and give them enough ink
        self.player1.hand = [item_card]
        self.player1.inkwell = [Mock(spec=Card, is_exerted=False) for _ in range(5)]

        # 2. Action
        self.player1.play_card(item_card, self.game)

        # 3. Assert
        self.assertIn(item_card, self.player1.play_area)
        self.assertNotIn(item_card, self.player1.hand)
        self.assertEqual(self.player1.get_available_ink(), 3, "Ink should be spent correctly")

        # Assert that the OnPlay effect was resolved
        self.game.effect_resolver.resolve_effect.assert_called_once_with(
            item_card.abilities[0],
            source_card=item_card,
            source_player=self.player1,
            chosen_targets=None
        )
        self.assertEqual(item_card.location, 'play_area')


if __name__ == '__main__':
    unittest.main()
