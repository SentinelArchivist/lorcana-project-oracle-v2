from typing import Dict, List, Any, Optional, Callable, Tuple
from collections import defaultdict


class TriggerBag:
    """
    The Bag - A temporary location for resolving all actions and abilities that trigger at the same time.
    
    When multiple abilities trigger at the same moment, they are added to the bag.
    They are then resolved in this order:
    1. Active player's abilities (in the order they choose)
    2. Non-active player's abilities (in the order they choose)
    """
    
    def __init__(self, game_state):
        self.game_state = game_state
        # Dictionary mapping player_id to a list of pending triggers
        self.triggers = defaultdict(list)
        # Track if we're currently resolving triggers
        self.resolving = False
        # Queue for triggers generated during resolution
        self.pending_triggers = []
        
    def add_trigger(self, player_id: int, effect_schema: Dict[str, Any], source_card, chosen_targets=None):
        """
        Add a triggered ability to the bag.
        
        Args:
            player_id: The ID of the player who controls the triggered ability
            effect_schema: The effect schema describing the trigger
            source_card: The card that is the source of the trigger
            chosen_targets: Any pre-selected targets for the effect
        """
        trigger = {
            'player_id': player_id,
            'effect_schema': effect_schema,
            'source_card': source_card,
            'chosen_targets': chosen_targets
        }
        
        # If we're already resolving triggers, queue this for the next resolution pass
        if self.resolving:
            self.pending_triggers.append(trigger)
        else:
            self.triggers[player_id].append(trigger)
    
    def resolve_triggers(self):
        """
        Resolve all triggers in the bag according to the active player priority rule.
        Returns True if any triggers were resolved, False otherwise.
        """
        if not any(self.triggers.values()):
            return False
            
        self.resolving = True
        
        # First, resolve active player's triggers
        active_player_id = self.game_state.current_player_id
        self._resolve_player_triggers(active_player_id)
        
        # Then, resolve non-active player's triggers
        non_active_player_id = self.game_state.get_opponent(active_player_id).player_id
        self._resolve_player_triggers(non_active_player_id)
        
        # Check if any new triggers were generated during resolution
        if self.pending_triggers:
            # Move pending triggers to the main triggers dictionary
            for trigger in self.pending_triggers:
                self.triggers[trigger['player_id']].append(trigger)
            self.pending_triggers = []
            
            # Recursively resolve the new triggers
            self.resolve_triggers()
            
        self.resolving = False
        return True
    
    def _resolve_player_triggers(self, player_id: int):
        """
        Resolve all triggers for a specific player.
        In a real game, the player would choose the order, but for AI simulation
        we'll just resolve in the order they were added.
        
        Args:
            player_id: The ID of the player whose triggers to resolve
        """
        player_triggers = self.triggers.pop(player_id, [])
        for trigger in player_triggers:
            self.game_state.effect_resolver.resolve_effect(
                trigger['effect_schema'],
                trigger['source_card'],
                trigger['chosen_targets']
            )
