import unittest
from unittest.mock import Mock

from src.game_engine.game_engine import GameState, Player, Card

class TestKeywords(unittest.TestCase):
    def setUp(self):
        """Set up a basic game state for testing keywords."""
        self.player1 = Player(player_id=1, deck=[])
        self.player2 = Player(player_id=2, deck=[])
        self.game = GameState(player1=self.player1, player2=self.player2)
        self.player1.game = self.game
        self.player2.game = self.game
        self.game.current_player_id = 1

    def test_evasive_keyword(self):
        """Test the Evasive keyword logic."""
        # 1. Setup
        # Challenger has no keywords
        challenger = Card({'Name': 'Challenger', 'Type': 'Character', 'Cost': 1, 'Strength': 1, 'Willpower': 1}, owner_player_id=1)
        challenger.can_challenge = True # Assume it can challenge this turn
        self.player1.play_area.append(challenger)

        # Target 1 has Evasive and is exerted
        target_evasive = Card({'Name': 'Evasive Target', 'Type': 'Character', 'Cost': 1, 'Strength': 1, 'Willpower': 1, 'Keywords': ['Evasive']}, owner_player_id=2)
        target_evasive.is_exerted = True
        self.player2.play_area.append(target_evasive)

        # Target 2 does not have Evasive and is exerted
        target_plain = Card({'Name': 'Plain Target', 'Type': 'Character', 'Cost': 1, 'Strength': 1, 'Willpower': 1}, owner_player_id=2)
        target_plain.is_exerted = True
        self.player2.play_area.append(target_plain)

        # 2. Action
        # Get valid targets for the non-Evasive challenger
        valid_targets = self.player1.get_valid_challenge_targets(challenger, self.player2)

        # 3. Assert
        # The non-Evasive challenger should only be able to challenge the non-Evasive target
        self.assertIn(target_plain, valid_targets)
        self.assertNotIn(target_evasive, valid_targets)

        # Now, give the challenger Evasive
        challenger_evasive = Card({'Name': 'Evasive Challenger', 'Type': 'Character', 'Cost': 1, 'Strength': 1, 'Willpower': 1, 'Keywords': ['Evasive']}, owner_player_id=1)
        challenger_evasive.can_challenge = True # Assume it can challenge this turn
        self.player1.play_area = [challenger_evasive] # Replace the old challenger

        # Get valid targets for the Evasive challenger
        valid_targets_for_evasive = self.player1.get_valid_challenge_targets(challenger_evasive, self.player2)

        # The Evasive challenger should be able to challenge BOTH targets
        self.assertIn(target_plain, valid_targets_for_evasive)
        self.assertIn(target_evasive, valid_targets_for_evasive)

    def test_rush_keyword(self):
        """Test that characters with Rush can act on the turn they are played."""
        # 1. Setup
        # Character with Rush
        rush_char = Card({'Name': 'Rush Character', 'Type': 'Character', 'Keywords': ['Rush']}, owner_player_id=1)

        # Character without Rush
        non_rush_char = Card({'Name': 'Non-Rush Character', 'Type': 'Character'}, owner_player_id=1)

        # Add cards to hand before playing
        self.player1.hand.extend([rush_char, non_rush_char])

        # Play both characters on the current turn (turn 1)
        self.player1.play_card(rush_char, self.game)
        self.player1.play_card(non_rush_char, self.game)

        # 2. Action & Assert
        # The character with Rush should be able to act
        self.assertTrue(self.player1._can_character_act(rush_char, game_turn=1))

        # The character without Rush should NOT be able to act (summoning sickness)
        self.assertFalse(self.player1._can_character_act(non_rush_char, game_turn=1))

        # On the next turn, both should be able to act
        self.assertTrue(self.player1._can_character_act(rush_char, game_turn=2))
        self.assertTrue(self.player1._can_character_act(non_rush_char, game_turn=2))


    def test_ward_keyword(self):
        """Test that characters with Ward cannot be chosen by opponent's effects."""
        # 1. Setup
        # Player 2 has two characters: one with Ward, one without.
        ward_char = Card({'Name': 'Ward Character', 'Type': 'Character', 'Keywords': ['Ward']}, owner_player_id=2)
        plain_char = Card({'Name': 'Plain Character', 'Type': 'Character'}, owner_player_id=2)
        self.player2.play_area.extend([ward_char, plain_char])

        # Player 1 is attempting to use an effect that targets an opposing character.
        # We'll need a new method to determine valid targets for an effect.

        # 2. Action
        # Get valid targets for an effect that Player 1 is initiating.
        valid_targets = self.player1.get_valid_effect_targets(self.player2)

        # 3. Assert
        # The character with Ward should not be in the list of valid targets.
        self.assertIn(plain_char, valid_targets)
        self.assertNotIn(ward_char, valid_targets)

    def test_shift_keyword(self):
        """Test that a character with Shift can be played for a reduced cost."""
        # 1. Setup
        # Player 1 has a character in play
        base_character_data = {'Name': 'Mickey Mouse, Friendly Face', 'Type': 'Character', 'Cost': 1}
        base_character = Card(base_character_data, owner_player_id=1)
        self.player1.play_area.append(base_character)

        # Player 1 has a character in hand with Shift that can be played on the base character
        shift_character_data = {'Name': 'Mickey Mouse, Brave Little Tailor', 'Type': 'Character', 'Cost': 7, 'Keywords': ['Shift 5']}
        shift_character = Card(shift_character_data, owner_player_id=1)
        self.player1.hand.append(shift_character)

        # Player 1 has enough ink to pay the Shift cost, but not the full cost
        ink_cards = []
        for _ in range(6):
            ink_card = Card({'Name': 'Ink Card', 'Type': 'Action', 'Inkable': True}, owner_player_id=1)
            ink_card.is_exerted = False
            ink_cards.append(ink_card)
        self.player1.inkwell = ink_cards

        # 2. Debugging Assertions - Verify each component of the logic
        self.assertEqual(shift_character.get_keyword_value('Shift'), 5, "get_keyword_value should return 5")
        self.assertEqual(self.player1.get_available_ink(), 6, "Player should have 6 available ink")
        self.assertEqual(shift_character.get_base_name(), "Mickey Mouse", "Shift character base name is incorrect")
        self.assertEqual(base_character.get_base_name(), "Mickey Mouse", "Base character base name is incorrect")

        # 3. Action
        self.player1.play_card(shift_character, self.game, shift_target=base_character)

        # 4. Assert
        self.assertIn(shift_character, self.player1.play_area)
        self.assertNotIn(shift_character, self.player1.hand)
        self.assertIn(base_character, self.player1.discard_pile)
        self.assertEqual(self.player1.get_available_ink(), 1, "Incorrect ink amount after shifting")



    def test_vanish_keyword(self):
        """Test that a character with Vanish returns to hand when banished."""
        # 1. Setup
        # Player 1 has a character with Vanish in play
        vanish_char_data = {'Name': 'Cheshire Cat, Not All There', 'Type': 'Character', 'Strength': 0, 'Willpower': 3, 'Keywords': ['Vanish']}
        vanish_char = Card(vanish_char_data, owner_player_id=1)
        self.player1.play_area.append(vanish_char)

        # Deal lethal damage to the character
        vanish_char.take_damage(3)

        # 2. Action
        # The banish logic is triggered within take_damage, but we'll call it explicitly
        # to ensure the test is clear. In the real engine, this check happens after damage.
        if vanish_char.willpower is not None and vanish_char.damage_counters >= vanish_char.willpower:
            self.player1.banish_character(vanish_char)

        # 3. Assert
        self.assertIn(vanish_char, self.player1.hand, "Character with Vanish should return to hand.")
        self.assertNotIn(vanish_char, self.player1.discard_pile, "Character with Vanish should not be in the discard pile.")
        self.assertNotIn(vanish_char, self.player1.play_area, "Character with Vanish should be removed from play.")


if __name__ == '__main__':
    unittest.main()
