import unittest
from unittest.mock import MagicMock, patch
import json
from typing import Dict, Any

from src.game_engine.game_engine import GameState, Player, Card
from src.game_engine.trigger_bag import TriggerBag


class TestTriggerBag(unittest.TestCase):
    def setUp(self):
        # Create mock players
        self.player1 = MagicMock(spec=Player)
        self.player1.player_id = 1
        self.player1.play_area = []
        
        self.player2 = MagicMock(spec=Player)
        self.player2.player_id = 2
        self.player2.play_area = []
        
        # Create a mock game state with our mock players
        self.game_state = MagicMock(spec=GameState)
        self.game_state.players = {1: self.player1, 2: self.player2}
        self.game_state.current_player_id = 1  # Player 1 is active
        self.game_state.get_player = lambda pid: self.game_state.players[pid]
        self.game_state.get_opponent = lambda pid: self.game_state.players[2 if pid == 1 else 1]
        
        # Create the TriggerBag we'll test
        self.trigger_bag = TriggerBag(self.game_state)
        
        # Create mock effect resolver
        self.game_state.effect_resolver = MagicMock()
        
    def create_mock_card(self, owner_id, name="Test Card"):
        """Helper to create a mock card for testing"""
        card = MagicMock(spec=Card)
        card.owner_player_id = owner_id
        card.name = name
        return card
        
    def create_effect_schema(self, effect_type="DealDamage", value=1):
        """Helper to create a test effect schema"""
        return {"effect": effect_type, "value": value}
        
    def test_add_trigger(self):
        """Test that triggers can be added to the bag"""
        # Create a mock card and effect
        card = self.create_mock_card(1)
        effect = self.create_effect_schema()
        
        # Add trigger to bag
        self.trigger_bag.add_trigger(1, effect, card)
        
        # Verify it was added
        self.assertEqual(len(self.trigger_bag.triggers[1]), 1)
        self.assertEqual(self.trigger_bag.triggers[1][0]['effect_schema'], effect)
        self.assertEqual(self.trigger_bag.triggers[1][0]['source_card'], card)
    
    def test_active_player_priority(self):
        """Test that active player's triggers resolve first"""
        # Create cards for each player
        card1 = self.create_mock_card(1, "Player 1's Card")
        card2 = self.create_mock_card(2, "Player 2's Card")
        
        # Create effects
        effect1 = self.create_effect_schema("Effect1")
        effect2 = self.create_effect_schema("Effect2")
        
        # Add triggers to bag in reverse order (non-active player first)
        self.trigger_bag.add_trigger(2, effect2, card2)
        self.trigger_bag.add_trigger(1, effect1, card1)
        
        # Resolve triggers
        self.trigger_bag.resolve_triggers()
        
        # Check that effects were resolved in correct order (active player first)
        # We can verify this by checking the order of calls to effect_resolver.resolve_effect
        call_args_list = self.game_state.effect_resolver.resolve_effect.call_args_list
        self.assertEqual(len(call_args_list), 2)
        self.assertEqual(call_args_list[0][0][0], effect1)  # Active player's effect should be first
        self.assertEqual(call_args_list[1][0][0], effect2)  # Non-active player's effect should be second
    
    def test_nested_triggers(self):
        """Test that triggers created during resolution are processed correctly"""
        # Create a side effect for the resolve_effect method that adds a new trigger
        def side_effect(effect_schema, source_card, chosen_targets=None):
            if effect_schema.get('effect') == 'Effect1':
                # Add a new trigger when Effect1 resolves
                self.trigger_bag.add_trigger(
                    player_id=1,  # Active player's trigger
                    effect_schema={'effect': 'NestedEffect'},
                    source_card=source_card
                )
        
        # Set up the side effect
        self.game_state.effect_resolver.resolve_effect.side_effect = side_effect
        
        # Create initial trigger
        card = self.create_mock_card(1)
        effect = self.create_effect_schema("Effect1")
        
        # Add and resolve
        self.trigger_bag.add_trigger(1, effect, card)
        self.trigger_bag.resolve_triggers()
        
        # Verify both effects were resolved
        call_args_list = self.game_state.effect_resolver.resolve_effect.call_args_list
        self.assertEqual(len(call_args_list), 2)  # Should have resolved both effects
        self.assertEqual(call_args_list[0][0][0]['effect'], 'Effect1')  # Original effect first
        self.assertEqual(call_args_list[1][0][0]['effect'], 'NestedEffect')  # Nested effect second
    
    def test_start_of_turn_integration(self):
        """Test integration with start-of-turn phase"""
        # Create cards with start-of-turn abilities
        active_card = MagicMock(spec=Card)
        active_card.owner_player_id = 1
        active_card.card_type = 'Character'  # Add card_type attribute
        active_card.lore = 0  # Add lore attribute
        active_card.abilities = [
            {'at_start_of_turn': True, 'effect': 'DrawCard', 'value': 1}
        ]
        
        non_active_card = MagicMock(spec=Card)
        non_active_card.owner_player_id = 2
        non_active_card.card_type = 'Character'  # Add card_type attribute
        non_active_card.lore = 0  # Add lore attribute
        non_active_card.abilities = [
            {'at_start_of_turn': True, 'effect': 'DealDamage', 'value': 1}
        ]
        
        # Add cards to play areas
        self.player1.play_area = [active_card]
        self.player2.play_area = [non_active_card]
        
        # Use a real GameState object for this test
        with patch('src.game_engine.game_engine.EffectResolver') as MockEffectResolver:
            # Set up mock effect resolver
            mock_resolver = MockEffectResolver.return_value
            
            # Call _set_phase which should process start-of-turn triggers
            game_state = GameState(self.player1, self.player2)
            game_state.effect_resolver = mock_resolver
            game_state._set_phase()
            
            # Verify effect resolver was called with triggers in correct order
            calls = mock_resolver.resolve_effect.call_args_list
            self.assertEqual(len(calls), 2)
            # Active player's card effect should be resolved first
            self.assertEqual(calls[0][0][0]['effect'], 'DrawCard')
            # Then non-active player's card effect
            self.assertEqual(calls[1][0][0]['effect'], 'DealDamage')
