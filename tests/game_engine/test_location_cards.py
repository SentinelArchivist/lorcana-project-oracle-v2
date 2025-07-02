import unittest
from unittest.mock import Mock, MagicMock

from src.game_engine.game_engine import GameState, Player, Card
from src.abilities.create_abilities_database import ParsedAbility


class TestLocationCards(unittest.TestCase):
    def setUp(self):
        """Set up a basic game state for testing location card interactions."""
        self.player1 = Player(player_id=1, deck=[])
        self.player2 = Player(player_id=2, deck=[])
        self.game = GameState(player1=self.player1, player2=self.player2)
        self.player1.game = self.game
        self.player2.game = self.game
        self.game.effect_resolver = Mock()

        # Mock the game state to control player turn
        self.game.current_player_id = 1
        self.game.turn_number = 1

    def test_play_location_card(self):
        """Test that a player can play a location card from their hand."""
        # 1. Setup
        location_card_data = {
            'Name': 'McDucks Manor',
            'Cost': 3,
            'Type': 'Location',
            'Inkable': False,
            'Body Text': 'Your characters here get +1 lore.'
        }
        location_card = Card(location_card_data, owner_player_id=self.player1.player_id)

        # Put the card in player's hand and give them enough ink
        self.player1.hand = [location_card]
        self.player1.inkwell = [Mock(spec=Card, is_exerted=False) for _ in range(3)]

        # 2. Action
        self.player1.play_card(location_card, self.game)

        # 3. Assert
        self.assertIn(location_card, self.player1.locations)
        self.assertNotIn(location_card, self.player1.hand)
        self.assertEqual(self.player1.get_available_ink(), 0, "Ink should be spent correctly")
        self.assertEqual(location_card.location, 'play_area')


if __name__ == '__main__':
    unittest.main()
