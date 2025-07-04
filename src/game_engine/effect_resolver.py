from typing import Dict, Callable, Any, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.game_engine.game_engine import GameState, Player, Card

class EffectResolver:
    """Translates a canonical effect schema into a concrete game state change."""

    def __init__(self, game: 'GameState', card_class: type, player_class: type):
        self.game = game
        self.Card = card_class
        self.Player = player_class
        self.effect_map: Dict[str, Callable[..., None]] = {
            'DealDamage': self._resolve_deal_damage,
            'DrawCard': self._resolve_draw_card,
            'Banish': self._resolve_banish,
            'GainStrength': self._resolve_gain_strength,
            'ReturnToHand': self._resolve_return_to_hand,
            'GainKeyword': self._resolve_gain_keyword,
            'ADD_KEYWORD': self._resolve_add_keyword,
            'SET_SHIFT_COST': self._resolve_set_shift_cost,
            'SINGER': self._resolve_singer,
        }

    def resolve_effect(self, effect_schema: Dict[str, Any], source_card: 'Card', chosen_targets: Optional[List[Any]] = None):
        """
        Resolves a single effect based on its schema.
        This is the primary method for executing abilities.
        """
        handler = self.effect_map.get(effect_schema.get('effect'))
        if not handler:
            return

        targets = self._get_targets(effect_schema, source_card, chosen_targets)
        if not targets:
            return

        # Pass the whole schema as kwargs to the handler, plus the source card
        handler(targets=targets, source_card=source_card, **effect_schema)

    def _get_targets(self, effect_schema: Dict[str, Any], source_card: 'Card', chosen_targets: Optional[List[Any]] = None) -> List[Any]:
        """Determines the target(s) of an effect based on the schema."""
        target_type = effect_schema.get('target')
        if target_type == 'Self':
            return [source_card]
        elif target_type == 'ChosenCharacter':
            return chosen_targets if chosen_targets else []
        # TODO: Implement other target types like Opponent, AllCharacters, etc.
        return []

    def _resolve_deal_damage(self, targets: List['Card'], value: int, **kwargs):
        for target_card in targets:
            if isinstance(target_card, self.Card) and hasattr(target_card, 'take_damage'):
                target_card.take_damage(value)

    def _resolve_draw_card(self, targets: List['Card'], value: int, **kwargs):
        # This handler receives cards as targets (e.g., from a 'Self' target).
        # We need to find the owner of the card and make them draw.
        for target_card in targets:
            if isinstance(target_card, self.Card) and target_card.owner_player_id is not None:
                owner_player = self.game.get_player(target_card.owner_player_id)
                if owner_player:
                    owner_player.draw_cards(value)

    def _resolve_banish(self, targets: List['Card'], **kwargs):
        for target_card in targets:
            if isinstance(target_card, self.Card) and target_card.owner_player_id is not None:
                owner_player = self.game.get_player(target_card.owner_player_id)
                if owner_player:
                    owner_player.banish_character(target_card)

    def _resolve_gain_strength(self, targets: List['Card'], value: int, duration: str, source_card: 'Card', **kwargs):
        modifier = {'strength': value, 'duration': duration, 'player_id': source_card.owner_player_id}
        for target_card in targets:
            if isinstance(target_card, self.Card) and hasattr(target_card, 'strength_modifiers'):
                target_card.strength_modifiers.append(modifier)

    def _resolve_return_to_hand(self, targets: List['Card'], **kwargs):
        for target_card in targets:
            if isinstance(target_card, self.Card) and target_card.owner_player_id is not None:
                owner_player = self.game.get_player(target_card.owner_player_id)
                if owner_player:
                    owner_player.return_to_hand(target_card)

    def _resolve_gain_keyword(self, targets: List['Card'], value: str, duration: str, source_card: 'Card', **kwargs):
        modifier = {'keyword': value, 'duration': duration, 'player_id': source_card.owner_player_id}
        for target_card in targets:
            if isinstance(target_card, self.Card) and hasattr(target_card, 'keyword_modifiers'):
                target_card.keyword_modifiers.append(modifier)

    def _resolve_add_keyword(self, targets: List['Card'], value: str, **kwargs):
        for target_card in targets:
            if isinstance(target_card, self.Card) and hasattr(target_card, 'keywords'):
                target_card.keywords.add(value)

    def _resolve_set_shift_cost(self, targets: List['Card'], value: int, **kwargs):
        for target_card in targets:
            if isinstance(target_card, self.Card) and hasattr(target_card, 'keywords'):
                target_card.keywords.add(f"Shift {value}")

    def _resolve_singer(self, targets: List['Card'], value: int, **kwargs):
        for target_card in targets:
            if isinstance(target_card, self.Card) and hasattr(target_card, 'keywords'):
                target_card.keywords.add(f"Singer {value}")
