import unittest
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.game_engine.game_engine import Card, Player, Deck, GameState


class TestCard(unittest.TestCase):
    """Tests the Card class from the game engine."""

    def setUp(self):
        """Set up mock card data for tests."""
        self.mock_card_data_simple = {
            'Name': 'Mickey Mouse, Brave Little Tailor',
            'Cost': 8,
            'Inkable': True,
            'Type': 'Character',
            'Strength': 5,
            'Willpower': 5,
            'Lore': 4,
            'Keywords': ['Evasive'],
            'Abilities': '[]' # Empty JSON array as string
        }

        self.mock_card_data_challenger = {
            'Name': 'Captain Hook, Forceful Duelist',
            'Cost': 1,
            'Inkable': True,
            'Type': 'Character',
            'Strength': 1,
            'Willpower': 1,
            'Lore': 1,
            'Keywords': ['Challenger +2'],
            'Abilities': '[]'
        }

        self.mock_card_data_shift = {
            'Name': 'Stitch, Rock Star',
            'Cost': 6,
            'Inkable': True,
            'Type': 'Character',
            'Strength': 3,
            'Willpower': 5,
            'Lore': 2,
            'Keywords': ['Shift 4', 'Singer 6'],
            'Abilities': '[]'
        }

        self.simple_card = Card(self.mock_card_data_simple, owner_player_id=1)
        self.challenger_card = Card(self.mock_card_data_challenger, owner_player_id=1)
        self.shift_card = Card(self.mock_card_data_shift, owner_player_id=1)

    def test_card_initialization(self):
        """Tests that a card's attributes are initialized correctly."""
        self.assertEqual(self.simple_card.name, 'Mickey Mouse, Brave Little Tailor')
        self.assertEqual(self.simple_card.cost, 8)
        self.assertEqual(self.simple_card.strength, 5)
        self.assertEqual(self.simple_card.willpower, 5)
        self.assertEqual(self.simple_card.lore, 4)
        self.assertIn('Evasive', self.simple_card.keywords)

    def test_take_damage(self):
        """Tests that damage is applied correctly to a card."""
        self.simple_card.take_damage(3)
        self.assertEqual(self.simple_card.damage_counters, 3)
        self.simple_card.take_damage(1)
        self.assertEqual(self.simple_card.damage_counters, 4)

    def test_strength_property_with_modifiers(self):
        """Tests that the strength property correctly applies modifiers."""
        self.assertEqual(self.simple_card.strength, 5)
        # Add a temporary strength modifier
        self.simple_card.strength_modifiers.append({'value': 2, 'duration': 'end_of_turn'})
        self.assertEqual(self.simple_card.strength, 7)
        # Add another modifier
        self.simple_card.strength_modifiers.append({'value': -1, 'duration': 'end_of_turn'})
        self.assertEqual(self.simple_card.strength, 6)

    def test_has_keyword(self):
        """Tests the keyword checking logic."""
        self.assertTrue(self.simple_card.has_keyword('Evasive'))
        self.assertFalse(self.simple_card.has_keyword('Challenger'))
        self.assertTrue(self.challenger_card.has_keyword('Challenger'))
        self.assertTrue(self.shift_card.has_keyword('Shift'))
        self.assertTrue(self.shift_card.has_keyword('Singer'))

    def test_get_keyword_value(self):
        """Tests parsing of numeric values from keywords."""
        self.assertIsNone(self.simple_card.get_keyword_value('Evasive'), "Keywords without values should return None")
        self.assertEqual(self.challenger_card.get_keyword_value('Challenger'), 2)
        self.assertEqual(self.shift_card.get_keyword_value('Shift'), 4)
        self.assertEqual(self.shift_card.get_keyword_value('Singer'), 6)
        self.assertIsNone(self.shift_card.get_keyword_value('Evasive'), "Non-existent keywords should return None")

class TestPlayer(unittest.TestCase):
    """Tests the Player class from the game engine."""

    def setUp(self):
        """Set up a player with a mock deck for tests."""
        self.mock_cards = [Card({'Name': f'Card {i}', 'Cost': 1, 'Inkable': True, 'Type': 'Character', 'Strength': 1, 'Willpower': 1, 'Lore': 1}, owner_player_id=1) for i in range(10)]
        self.mock_deck = Deck(self.mock_cards[:])  # Pass a copy
        self.player = Player(player_id=1, initial_deck=self.mock_deck)
        self.player.draw_cards(7)

    def test_player_initialization(self):
        """Tests that a player's attributes are initialized correctly."""
        self.assertEqual(self.player.player_id, 1)
        self.assertEqual(len(self.player.hand), 7)
        self.assertEqual(len(self.player.inkwell), 0)
        self.assertEqual(len(self.player.play_area), 0)
        self.assertEqual(self.player.lore, 0)

    def test_draw_cards(self):
        """Tests drawing cards from the deck to the hand."""
        # setUp provides a 7-card hand from a 10-card deck.
        self.assertEqual(len(self.player.hand), 7)
        self.assertEqual(len(self.player.deck.cards), 3)

        # Draw the remaining 3 cards
        self.player.draw_cards(3)
        self.assertEqual(len(self.player.hand), 10)
        self.assertTrue(self.player.deck.is_empty())

    def test_ink_card(self):
        """Tests moving a card from hand to the inkwell."""
        # Player starts with a 7-card hand from setUp.
        card_to_ink = self.player.hand[0]
        initial_hand_size = len(self.player.hand)

        self.assertTrue(self.player.ink_card(card_to_ink))
        self.assertEqual(len(self.player.hand), initial_hand_size - 1)
        self.assertEqual(len(self.player.inkwell), 1)
        self.assertIn(card_to_ink, self.player.inkwell)
        self.assertEqual(card_to_ink.location, 'inkwell')

    def test_get_available_ink(self):
        """Tests the calculation of available (ready) ink across turns."""
        # Turn 1: Ink a card. It should enter play exerted.
        card1 = self.player.hand[0]
        self.assertTrue(self.player.ink_card(card1), "Inking should succeed on the first attempt.")
        self.assertEqual(self.player.get_available_ink(), 0, "Ink should be exerted when first played.")
        self.assertTrue(self.player.has_inked_this_turn, "Player should be marked as having inked.")

        # Attempting to ink a second card in the same turn should fail.
        card2 = self.player.hand[0]
        self.assertFalse(self.player.ink_card(card2), "Inking should fail on the second attempt in the same turn.")
        self.assertEqual(len(self.player.inkwell), 1, "Inkwell should still only have one card.")

        # Simulate start of Turn 2
        self.player.has_inked_this_turn = False
        self.player.ready_cards()
        self.assertEqual(self.player.get_available_ink(), 1, "Ink from prior turn should be ready.")

        # Ink a second card on the new turn.
        self.assertTrue(self.player.ink_card(card2), "Inking should succeed in a new turn.")
        self.assertEqual(len(self.player.inkwell), 2, "Inkwell should now have two cards.")

        # The first ink should still be ready, the new one is exerted.
        self.assertEqual(self.player.get_available_ink(), 1, "Only previously available ink should be ready.")

        # Simulate start of Turn 3
        self.player.has_inked_this_turn = False
        self.player.ready_cards()
        self.assertEqual(self.player.get_available_ink(), 2, "All ink should be ready after readying again.")

        # Manually exert one ink and check again
        self.player.inkwell[0].is_exerted = True
        self.assertEqual(self.player.get_available_ink(), 1, "Available ink should decrease after one is exerted.")

    def test_quest(self):
        """Tests that questing correctly adds lore and exerts the character."""
        character = Card({'Name': 'Quester', 'Lore': 2, 'Type': 'Character'}, owner_player_id=1)
        character.turn_played = 0 # Assume ink is dry
        self.player.play_area.append(character)

        self.assertTrue(self.player.quest(character, game_turn=1))
        self.assertEqual(self.player.lore, 2)
        self.assertTrue(character.is_exerted)


class TestGameState(unittest.TestCase):
    """Tests the GameState class, which manages the overall game."""

    def setUp(self):
        """Set up for the game state tests."""
        self.card_data = [
            {'Name': 'Mickey Mouse, True Friend', 'Cost': 1, 'Inkable': True, 'Type': 'Character', 'Strength': 1, 'Willpower': 2, 'Lore': 1},
            {'Name': 'Goofy, Daredevil', 'Cost': 2, 'Inkable': True, 'Type': 'Character', 'Strength': 2, 'Willpower': 3, 'Lore': 1},
            {'Name': 'Donald Duck, Boisterous Fowl', 'Cost': 3, 'Inkable': False, 'Type': 'Character', 'Strength': 3, 'Willpower': 3, 'Lore': 2},
        ]
        # Create full 60-card decks
        cards1 = [Card(c, owner_player_id=1) for c in self.card_data * 20]
        cards2 = [Card(c, owner_player_id=2) for c in self.card_data * 20]
        deck1 = Deck(cards1)
        deck2 = Deck(cards2)

        self.player1 = Player(initial_deck=deck1, player_id=1)
        self.player2 = Player(initial_deck=deck2, player_id=2)

        # Draw starting hands
        self.player1.draw_cards(7)
        self.player2.draw_cards(7)

        self.game_state = GameState(self.player1, self.player2)
        # Manually step through the start of the turn phases
        self.game_state._ready_phase()
        self.game_state._set_phase()
        self.game_state._draw_phase()

    def test_game_state_initialization(self):
        """Tests that the game state is initialized correctly."""
        self.assertEqual(self.game_state.turn_number, 1)
        self.assertIsNotNone(self.game_state.players[1])
        self.assertIsNotNone(self.game_state.players[2])
        self.assertEqual(self.game_state.current_player_id, 1)
        self.assertEqual(self.game_state.current_player_id, self.game_state.players[1].player_id)

    def test_end_turn(self):
        """Tests that the turn progression logic is correct."""
        player1 = self.game_state.players[1]
        player2 = self.game_state.players[2]

        # Player 1 ends their turn
        self.game_state.end_turn()
        self.assertEqual(self.game_state.current_player_id, player2.player_id)
        self.assertEqual(self.game_state.turn_number, 1) # Still turn 1

        # Player 2 ends their turn, completing the round
        self.game_state.end_turn()
        self.assertEqual(self.game_state.current_player_id, player1.player_id)
        self.assertEqual(self.game_state.turn_number, 2) # Should now be turn 2

    def test_turn_start_readies_cards_and_draws(self):
        """Tests that cards are readied and one is drawn at the start of a turn."""
        # Setup: Exert a card in inkwell and a character in play for player 1
        ink_card = self.player1.hand[0]
        self.player1.ink_card(ink_card)  # This exerts the card

        # Manually move a card to the play area to set up the test state
        char_card = self.player1.hand.pop(1)
        self.player1.play_area.append(char_card)
        char_card.is_exerted = True

        self.assertEqual(self.player1.get_available_ink(), 0)
        self.assertTrue(char_card.is_exerted)

        initial_hand_size = len(self.player1.hand)

        # Action: Progress to player 1's next turn
        # End P1's turn 1 - this switches to P2
        self.game_state.end_turn()
        
        # Verify we're now on P2's turn
        self.assertEqual(self.game_state.current_player_id, self.player2.player_id)
        
        # Simulate P2's complete turn
        self.game_state._ready_phase()  # Ready P2's cards
        self.game_state._set_phase()    # P2's set phase
        self.game_state._draw_phase()   # P2 draws a card
        
        # End P2's turn - this switches back to P1 and increments turn number
        self.game_state.end_turn()
        
        # Verify we're now on P1's turn 2
        self.assertEqual(self.game_state.current_player_id, self.player1.player_id)
        
        # Now simulate P1's second turn start
        self.game_state._ready_phase()  # This should ready P1's inked card
        self.game_state._set_phase()    # P1's set phase
        self.game_state._draw_phase()   # P1 draws a card

        # Assert: Cards are readied and a card is drawn for P1 on turn 2
        self.assertEqual(self.game_state.turn_number, 2)
        self.assertEqual(self.game_state.current_player_id, self.player1.player_id)
        self.assertEqual(self.player1.get_available_ink(), 1)  # Inked card is now ready
        self.assertFalse(char_card.is_exerted)  # Character is now ready
        self.assertEqual(len(self.player1.hand), initial_hand_size + 1)


if __name__ == '__main__':
    unittest.main()
