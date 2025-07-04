import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from src.game_engine.game_engine import GameState, Player, Card, Deck

# --- Test Fixtures ---

def create_mock_card_data(name: str, unique_id: str, **kwargs) -> dict:
    """Helper function to create mock card data for tests."""
    data = {
        'Name': name, 'Unique_ID': unique_id, 'Cost': 3, 'Inkable': True,
        'Strength': None, 'Willpower': None, 'Lore': 0, 'Type': 'Character',
        'schema_abilities': []
    }
    if 'Abilities' in kwargs:
        kwargs['schema_abilities'] = kwargs.pop('Abilities')
    data.update(kwargs)
    return data


class TestLocationCards(unittest.TestCase):
    def setUp(self):
        """Set up a basic game state for testing Location cards."""
        self.player1 = Player(player_id=1, initial_deck=Deck([]))
        self.player2 = Player(player_id=2, initial_deck=Deck([]))
        self.game = GameState(player1=self.player1, player2=self.player2)
        self.game.current_player_id = 1

    def test_location_passive_lore_gain(self):
        """Test that Location cards grant passive lore at the start of turn."""
        # 1. Setup
        # Create two location cards with different lore values
        location1_data = create_mock_card_data("Castle", "loc-1", Type='Location', Lore=2)
        location2_data = create_mock_card_data("Forest", "loc-2", Type='Location', Lore=1)
        
        location1 = Card(location1_data, owner_player_id=1)
        location2 = Card(location2_data, owner_player_id=1)
        
        # Add the location cards to Player 1's play area
        self.player1.play_area.extend([location1, location2])
        
        # Initial lore should be 0
        self.assertEqual(self.player1.lore, 0)
        
        # 2. Action
        # Simulate the start of turn set phase
        self.game._set_phase()
        
        # 3. Assert
        # Player should gain lore equal to the sum of location lore values (2+1=3)
        self.assertEqual(self.player1.lore, 3, "Player should gain lore from all Location cards.")
        
        # Locations in opponent's play area should not grant lore to the current player
        location3_data = create_mock_card_data("Enemy Castle", "loc-3", Type='Location', Lore=3)
        location3 = Card(location3_data, owner_player_id=2)
        self.player2.play_area.append(location3)
        
        # Reset lore and run set phase again
        self.player1.lore = 0
        self.game._set_phase()
        
        # Only player 1's locations should grant lore
        self.assertEqual(self.player1.lore, 3, "Only the current player's locations should grant lore.")


class TestSingTogether(unittest.TestCase):
    def setUp(self):
        """Set up a basic game state for testing the Sing Together mechanic."""
        self.player1 = Player(player_id=1, initial_deck=Deck([]))
        self.player2 = Player(player_id=2, initial_deck=Deck([]))
        self.game = GameState(player1=self.player1, player2=self.player2)
        self.game.turn_number = 2  # To ensure ink is dry
        
        # Create a song card that costs 5
        self.song_card = Card(create_mock_card_data("Epic Song", "song-1", Type='Song', Cost=5), 1)
        self.player1.hand.append(self.song_card)
        
        # Create two singer characters with different Singer values
        singer1_ability = {
            "trigger": "Passive", "effect": "GainKeyword", "target": "Self",
            "value": {"keyword": "Singer", "amount": 3}, "notes": "Singer 3"
        }
        singer2_ability = {
            "trigger": "Passive", "effect": "GainKeyword", "target": "Self",
            "value": {"keyword": "Singer", "amount": 2}, "notes": "Singer 2"
        }
        
        self.singer1 = Card(create_mock_card_data("Lead Singer", "singer-1", Abilities=[singer1_ability]), 1)
        self.singer2 = Card(create_mock_card_data("Backup Singer", "singer-2", Abilities=[singer2_ability]), 1)
        self.singer1.turn_played = 0  # Ink is dry
        self.singer2.turn_played = 0  # Ink is dry
        
        self.player1.play_area.extend([self.singer1, self.singer2])

    def test_sing_together_success(self):
        """Test that multiple characters can exert together to sing a song."""
        # Song costs 5, singer1 has Singer 3, singer2 has Singer 2, together they should be able to sing it
        result = self.player1.sing_song_together(self.song_card, [self.singer1, self.singer2], self.game.turn_number)
        
        # Verify the song was successfully played
        self.assertTrue(result, "Sing Together should succeed with sufficient combined Singer value.")
        self.assertIn(self.song_card, self.player1.discard_pile, "Song should move to discard pile.")
        self.assertNotIn(self.song_card, self.player1.hand, "Song should not remain in hand.")
        
        # Verify both singers were exerted
        self.assertTrue(self.singer1.is_exerted, "First singer should be exerted.")
        self.assertTrue(self.singer2.is_exerted, "Second singer should be exerted.")

    def test_sing_together_insufficient_value(self):
        """Test that Sing Together fails if combined Singer values are insufficient."""
        # Create a more expensive song that costs 6
        expensive_song = Card(create_mock_card_data("Expensive Song", "song-2", Type='Song', Cost=6), 1)
        self.player1.hand.append(expensive_song)
        
        # Singer1 (3) + Singer2 (2) = 5, which is less than song cost (6)
        result = self.player1.sing_song_together(expensive_song, [self.singer1, self.singer2], self.game.turn_number)
        
        # Verify the attempt failed
        self.assertFalse(result, "Sing Together should fail with insufficient combined Singer value.")
        self.assertIn(expensive_song, self.player1.hand, "Song should remain in hand.")
        self.assertNotIn(expensive_song, self.player1.discard_pile, "Song should not move to discard pile.")
        
        # Verify singers were not exerted
        self.assertFalse(self.singer1.is_exerted, "First singer should not be exerted.")
        self.assertFalse(self.singer2.is_exerted, "Second singer should not be exerted.")

    def test_sing_together_one_singer_exerted(self):
        """Test that Sing Together fails if one singer is already exerted."""
        # Exert one of the singers before attempting to sing
        self.singer1.is_exerted = True
        
        result = self.player1.sing_song_together(self.song_card, [self.singer1, self.singer2], self.game.turn_number)
        
        # Verify the attempt failed
        self.assertFalse(result, "Sing Together should fail if any singer is already exerted.")
        self.assertIn(self.song_card, self.player1.hand, "Song should remain in hand.")
        
        # Singer2 should not have been exerted
        self.assertFalse(self.singer2.is_exerted, "Second singer should not be exerted.")

    def test_sing_song_with_multiple_singers(self):
        """Test that the original sing_song method can be used with Sing Together."""
        # Reset from previous tests
        self.singer1.is_exerted = False
        self.singer2.is_exerted = False
        
        # Create a new song that costs exactly 3 (equal to singer1's value)
        perfect_song = Card(create_mock_card_data("Perfect Song", "song-3", Type='Song', Cost=3), 1)
        self.player1.hand.append(perfect_song)
        
        # Use the regular sing_song method
        result = self.player1.sing_song(perfect_song, self.singer1, self.game.turn_number)
        
        # Verify it works as expected
        self.assertTrue(result, "Regular sing_song should work with a single adequate singer.")
        self.assertIn(perfect_song, self.player1.discard_pile, "Song should move to discard pile.")
        self.assertTrue(self.singer1.is_exerted, "Singer should be exerted.")
        self.assertFalse(self.singer2.is_exerted, "Second singer should not be affected.")


if __name__ == '__main__':
    unittest.main()
