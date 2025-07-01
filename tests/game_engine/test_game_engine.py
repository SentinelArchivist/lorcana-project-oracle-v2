import unittest
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from game_engine.game_engine import Card, Deck, Player, GameState

# --- Test Fixtures ---

def create_mock_card_data(name: str, unique_id: str) -> dict:
    """Creates a dictionary of mock card data for testing."""
    return {
        'Name': name,
        'Unique_ID': unique_id,
        'Cost': 3,
        'Inkable': True,
        'Strength': 2,
        'Willpower': 4,
        'Lore': 1
    }

def create_mock_deck(player_id: int, num_cards: int = 60) -> Deck:
    """Creates a mock deck of cards for a given player."""
    cards = [Card(create_mock_card_data(f"Card {i}", f"P{player_id}-{i}"), player_id) for i in range(num_cards)]
    return Deck(cards)

# --- Test Cases ---

class TestGameEngineClasses(unittest.TestCase):
    """
    Test suite for the core classes of the game engine.
    """

    def test_card_initialization(self):
        """Tests that a Card object initializes with correct static and dynamic data."""
        mock_data = create_mock_card_data("Test Card", "T-01")
        card = Card(mock_data, owner_player_id=1)
        
        self.assertEqual(card.name, "Test Card")
        self.assertEqual(card.owner_player_id, 1)
        self.assertEqual(card.is_exerted, False)
        self.assertEqual(card.damage_counters, 0)
        self.assertEqual(card.location, 'deck') # Default initial location

    def test_deck_creation_and_shuffle(self):
        """Tests that a Deck is created with 60 cards and that shuffling changes the order."""
        deck = create_mock_deck(player_id=1)
        self.assertEqual(len(deck.cards), 60)
        
        original_order = [card.unique_id for card in deck.cards]
        deck.shuffle()
        shuffled_order = [card.unique_id for card in deck.cards]
        
        self.assertNotEqual(original_order, shuffled_order, "Shuffling should change the card order.")
        self.assertEqual(len(deck.cards), 60, "Shuffling should not change the number of cards.")

    def test_player_draw_initial_hand(self):
        """Tests that a player draws 7 cards correctly, updating hand and deck states."""
        deck = create_mock_deck(player_id=1)
        player = Player(player_id=1, deck=deck)
        
        self.assertEqual(len(player.hand), 0)
        self.assertEqual(len(player.deck.cards), 60)
        
        player.draw_initial_hand()
        
        self.assertEqual(len(player.hand), 7)
        self.assertEqual(len(player.deck.cards), 53)
        self.assertTrue(all(card.location == 'hand' for card in player.hand))

    def test_game_state_initialization(self):
        """Tests that the GameState is initialized with two players and correct starting values."""
        p1_deck = create_mock_deck(player_id=1)
        p2_deck = create_mock_deck(player_id=2)
        player1 = Player(player_id=1, deck=p1_deck)
        player2 = Player(player_id=2, deck=p2_deck)
        
        # Draw hands before creating the game state
        player1.draw_initial_hand()
        player2.draw_initial_hand()
        
        game = GameState(player1, player2)
        
        self.assertEqual(game.current_player_id, 1)
        self.assertEqual(game.turn_number, 1)
        self.assertEqual(len(game.get_player(1).hand), 7)
        self.assertEqual(len(game.get_player(2).hand), 7)
        self.assertEqual(game.get_opponent(1).player_id, 2)
        self.assertEqual(game.get_opponent(2).player_id, 1)

if __name__ == '__main__':
    unittest.main()
