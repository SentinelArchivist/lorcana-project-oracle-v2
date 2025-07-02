from typing import Dict, Callable, Any, List, Optional

# These imports will be needed. We may need to refactor where ParsedAbility is stored.
from src.abilities.create_abilities_database import ParsedAbility
from src.game_engine.game_engine import GameState, Player, Card


class EffectResolver:
    """Translates a ParsedAbility into a concrete game state change."""

    def __init__(self, game: GameState):
        self.game = game
        # This map will link effect strings to the functions that execute them.
        self.effect_map: Dict[str, Callable[..., None]] = {
            'DealDamage': self._resolve_deal_damage,
            'DrawCard': self._resolve_draw_card,
            'Banish': self._resolve_banish,
            'GainStrength': self._resolve_gain_strength,
            'ReturnToHand': self._resolve_return_to_hand,
            'GainKeyword': self._resolve_gain_keyword,
        }

    def resolve_ability(self, ability: ParsedAbility, source_card: Card, chosen_targets: Optional[List[Any]] = None):
        """
        The main entry point for resolving an ability.
        It finds the correct handler and determines the target(s).

        Args:
            ability: The ParsedAbility object to resolve.
            source_card: The card that is the source of the ability.
            chosen_targets: A list of targets that have been pre-selected by the player/AI.
        """
        # 1. Find the correct function to handle the effect.
        handler = self.effect_map.get(ability.effect)
        if not handler:
            print(f"Warning: No handler found for effect: {ability.effect}")
            return

        # 2. Determine the target(s) of the ability.
        targets = self._get_targets(ability.target, source_card, ability, chosen_targets)
        if not targets:
            print(f"Warning: No valid targets found for target type: {ability.target}")
            return

        # 3. Call the handler with the targets and other parameters.
        handler(targets=targets, value=ability.value, ability=ability, source_card=source_card)

    def _get_targets(self, target_type: str, source_card: Card, ability: ParsedAbility, chosen_targets: Optional[List[Any]] = None) -> List[Any]:
        """
        Translates a target string (e.g., 'ChosenCharacter', 'Opponent') 
        into a list of actual game objects.
        """
        if target_type == 'Self':
            if source_card.owner_player_id is not None:
                player = self.game.get_player(source_card.owner_player_id)
                return [player] if player else []
        elif target_type == 'ChosenCharacter':
            return chosen_targets if chosen_targets else []
        
        # This will be expanded with more target types.
        return []

    # --- Effect Handler Implementations ---
    def _resolve_deal_damage(self, targets: List[Card], value: int, **kwargs):
        """Deals a specified amount of damage to each target."""
        for target_card in targets:
            if isinstance(target_card, Card) and hasattr(target_card, 'take_damage'):
                target_card.take_damage(value)

    def _resolve_draw_card(self, targets: List[Player], value: int, **kwargs):
        """Causes each target player to draw a specified number of cards."""
        for target_player in targets:
            if isinstance(target_player, Player) and hasattr(target_player, 'draw_cards'):
                target_player.draw_cards(value)

    def _resolve_banish(self, targets: List[Card], **kwargs):
        """Banishes each target card."""
        for target_card in targets:
            if isinstance(target_card, Card) and target_card.owner_player_id is not None:
                owner_player = self.game.get_player(target_card.owner_player_id)
                if owner_player:
                    owner_player.banish_character(target_card)

    def _resolve_gain_strength(self, targets: List[Card], value: int, ability: ParsedAbility, source_card: Card, **kwargs):
        """Applies a strength modifier to each target card."""
        modifier = {
            'value': value,
            'duration': ability.duration,
            'player_id': source_card.owner_player_id  # For turn-based expiration
        }
        for target_card in targets:
            if isinstance(target_card, Card) and hasattr(target_card, 'strength_modifiers'):
                target_card.strength_modifiers.append(modifier)

    def _resolve_return_to_hand(self, targets: List[Card], **kwargs):
        """Returns each target card to its owner's hand."""
        for target_card in targets:
            if isinstance(target_card, Card) and target_card.owner_player_id is not None:
                owner_player = self.game.get_player(target_card.owner_player_id)
                if owner_player:
                    owner_player.return_to_hand(target_card)

    def _resolve_gain_keyword(self, targets: List[Card], value: str, ability: ParsedAbility, source_card: Card, **kwargs):
        """Applies a keyword modifier to each target card."""
        modifier = {
            'keyword': value,
            'duration': ability.duration,
            'player_id': source_card.owner_player_id
        }
        for target_card in targets:
            if isinstance(target_card, Card) and hasattr(target_card, 'keyword_modifiers'):
                target_card.keyword_modifiers.append(modifier)

