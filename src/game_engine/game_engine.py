import random
from typing import List, Dict, Optional, Any

from . import player_logic
from src.abilities.create_abilities_database import ParsedAbility

class Card:
    """Represents a single instance of a card within a game."""
    def __init__(self, card_data: Dict[str, Any], owner_player_id: int):
        self.unique_id = card_data.get('Unique_ID')
        self.name = card_data.get('Name')
        self.cost = card_data.get('Cost', 0)
        self.inkable = card_data.get('Inkable', False)
        self.lore = card_data.get('Lore', 0)
        self.card_type = card_data.get('Type', 'Character') # Character, Action, Item
        self.keywords = card_data.get('Keywords', [])
        self.abilities = [ParsedAbility(**ability) for ability in card_data.get('Abilities', [])]
        self.owner_player_id = owner_player_id
        self.is_exerted = False
        self.damage_counters = 0
        self.location = 'deck'
        self.turn_played: Optional[int] = None # For "ink drying" rule
        self._base_strength: Optional[int] = card_data.get('Strength')
        self.willpower: Optional[int] = card_data.get('Willpower')
        self.strength_modifiers: List[Dict[str, Any]] = []  # e.g., [{'value': 2, 'duration': 'start_of_next_turn'}]
        self.keyword_modifiers: List[Dict[str, Any]] = []  # e.g., [{'keyword': 'Evasive', 'duration': 'start_of_turn'}]

    def __repr__(self) -> str:
        return f"Card({self.name})"

    def get_base_name(self) -> str:
        """Returns the base name of the character, stripping subtitles."""
        return self.name.split(',')[0].strip()

    @property
    def strength(self) -> Optional[int]:
        if self._base_strength is None:
            return None
        
        total_strength = self._base_strength
        for modifier in self.strength_modifiers:
            total_strength += modifier.get('value', 0)
        return total_strength

    def has_keyword(self, keyword: str) -> bool:
        """Checks if a card has a specific keyword ability, including temporary ones."""
        # Check for inherent keywords from the 'Keywords' list
        for kw in self.keywords:
            if kw.lower().startswith(keyword.lower()):
                return True

        # Check for keywords granted by abilities (e.g. from a parsed ability text)
        for ability in self.abilities:
            if isinstance(ability.value, dict) and ability.value.get('keyword') == keyword:
                return True
        
        # Check for temporary keywords from modifiers
        for modifier in self.keyword_modifiers:
            if modifier.get('keyword') == keyword:
                return True

        return False

    def get_keyword_value(self, keyword: str) -> Optional[int]:
        """Get the numeric value associated with a keyword (e.g., Challenger +X, Shift X)."""
        # Check for inherent keywords from the 'Keywords' list
        for kw_string in self.keywords:
            if kw_string.lower().startswith(keyword.lower()):
                parts = kw_string.split()
                if len(parts) > 1:
                    try:
                        # Attempt to parse the last part as an integer
                        return int(parts[-1])
                    except (ValueError, IndexError):
                        continue  # Not a numeric value, or no value present

        # Check for keywords granted by abilities (e.g. from a parsed ability text)
        for ability in self.abilities:
            if isinstance(ability.value, dict) and ability.value.get('keyword', '').lower() == keyword.lower():
                value = ability.value.get('amount')
                if isinstance(value, int):
                    return value

        # Check for temporary keywords from modifiers
        for modifier in self.keyword_modifiers:
            kw_string = modifier.get('keyword', '')
            if kw_string.lower().startswith(keyword.lower()):
                parts = kw_string.split()
                if len(parts) > 1:
                    try:
                        return int(parts[-1])
                    except (ValueError, IndexError):
                        continue

        return None

    def take_damage(self, amount: int):
        """Applies damage to the card."""
        if self.willpower is not None and amount > 0:
            self.damage_counters += amount

class Deck:
    """Represents a player's deck of 60 cards."""
    def __init__(self, card_list: List[Card]):
        self.cards = card_list
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self) -> Optional[Card]:
        return self.cards.pop(0) if self.cards else None

    def is_empty(self) -> bool:
        return not self.cards

class Player:
    """Represents a player in the game, including their actions."""
    def __init__(self, player_id: int, deck: Deck):
        self.player_id = player_id
        self.deck = deck
        self.hand: List[Card] = []
        self.inkwell: List[Card] = []
        self.play_area: List[Card] = []
        self.locations: List[Card] = []
        self.discard_pile: List[Card] = []
        self.lore = 0
        self.temporary_strength_mods: Dict[str, int] = {}

    def draw_cards(self, num_cards: int):
        """Draws a specified number of cards from the deck to the hand."""
        for _ in range(num_cards):
            card = self.deck.draw()
            if card:
                card.location = 'hand'
                self.hand.append(card)

    def draw_initial_hand(self, num_cards: int = 7):
        self.draw_cards(num_cards)

    def get_available_ink(self) -> int:
        """Returns the number of unexerted cards in the inkwell."""
        return sum(1 for card in self.inkwell if not card.is_exerted)

    def _can_character_act(self, character: Card, game_turn: int) -> bool:
        """Checks if a character can perform an action (ink is 'dry')."""
        if character.is_exerted:
            return False

        # Characters with Rush ignore summoning sickness
        if character.has_keyword('Rush'):
            return True

        # Standard summoning sickness rule
        if character.turn_played == game_turn:
            return False

        return True

    def ink_card(self, card: Card) -> bool:
        """Moves a card from hand to inkwell. Returns True on success."""
        if card in self.hand and card.inkable:
            self.hand.remove(card)
            card.location = 'inkwell'
            card.is_exerted = True  # Inked cards enter exerted
            self.inkwell.append(card)
            return True
        return False

    def exert_ink(self, amount: int):
        """Exerts a specified number of ready ink cards."""
        if self.get_available_ink() < amount:
            raise ValueError(f"Not enough available ink. Have {self.get_available_ink()}, need {amount}")

        ink_to_exert = amount
        for ink_card in self.inkwell:
            if not ink_card.is_exerted and ink_to_exert > 0:
                ink_card.is_exerted = True
                ink_to_exert -= 1

    def get_possible_shift_targets(self, card: 'Card') -> List['Card']:
        """Returns a list of characters in play that the given card can be shifted onto."""
        if not card.has_keyword('Shift'):
            return []

        card_base_name = card.get_base_name()
        return [char for char in self.play_area if char.card_type == 'Character' and char.get_base_name() == card_base_name]

    def play_card(self, card: 'Card', game: 'GameState', shift_target: Optional['Card'] = None):
        """Plays a card from hand, handling normal, item, action, and shift plays."""
        if card not in self.hand:
            raise ValueError(f"Card {card.name} not in hand.")

        cost = card.cost
        if shift_target:
            shift_cost = card.get_keyword_value('Shift')
            if shift_cost is None:
                raise ValueError(f"Card {card.name} does not have a valid Shift cost.")
            cost = shift_cost

        if self.get_available_ink() < cost:
            raise ValueError(f"Not enough ink to play {card.name}. Have {self.get_available_ink()}, need {cost}.")

        self.exert_ink(cost)
        self.hand.remove(card)

        if shift_target:
            if shift_target not in self.play_area:
                raise ValueError(f"Shift target {shift_target.name} is not in play.")
            # Transfer state from the old character to the new one
            card.is_exerted = shift_target.is_exerted
            card.damage_counters = shift_target.damage_counters
            card.strength_modifiers = list(shift_target.strength_modifiers)
            card.keyword_modifiers = list(shift_target.keyword_modifiers)
            card.turn_played = shift_target.turn_played  # It's considered to have been in play

            # The old card is effectively replaced and goes to the discard pile
            self.play_area.remove(shift_target)
            self.discard_pile.append(shift_target)
            shift_target.location = 'discard'

            card.location = 'play_area'
            self.play_area.append(card)

        elif card.card_type == 'Character' or card.card_type == 'Item':
            card.location = 'play_area'
            card.turn_played = game.turn_number
            self.play_area.append(card)

        elif card.card_type == 'Location':
            card.location = 'play_area'
            self.locations.append(card)

        elif card.card_type == 'Action' or card.card_type == 'Song':
            card.location = 'discard'
            self.discard_pile.append(card)

        # Resolve OnPlay abilities
        for ability in card.abilities:
            if ability.trigger.get('primary_trigger') == 'OnPlay':
                game.effect_resolver.resolve_effect(
                    ability,
                    source_card=card,
                    source_player=self,
                    chosen_targets=None  # OnPlay effects typically don't have pre-chosen targets
                )

    def sing_song(self, song_card: Card, singer: Card, game_turn: int) -> bool:
        """Plays a song by exerting a character. Returns True on success."""
        singer_ability_cost = singer.get_keyword_value('Singer')
        if (song_card in self.hand and
            song_card.card_type == 'Song' and
            singer in self.play_area and
            self._can_character_act(singer, game_turn) and
            singer_ability_cost is not None and
            song_card.cost <= singer_ability_cost):
            
            singer.is_exerted = True
            self.hand.remove(song_card)
            song_card.location = 'discard'
            self.discard_pile.append(song_card)
            return True
        return False

    def clear_temporary_mods(self):
        """Clears any temporary modifications, like from Support."""
        self.temporary_strength_mods.clear()

    def quest(self, character: Card, game_turn: int, support_target: Optional[Card] = None) -> bool:
        """Quests with a character. Returns True on success."""
        if character in self.play_area and self._can_character_act(character, game_turn):
            character.is_exerted = True
            self.lore += character.lore

            # Handle Support keyword
            if character.has_keyword('Support') and support_target:
                if support_target in self.play_area and support_target != character:
                    support_value = character.strength or 0
                    self.temporary_strength_mods[support_target.unique_id] = self.temporary_strength_mods.get(support_target.unique_id, 0) + support_value

            return True
        return False

    def return_to_hand(self, character: Card):
        """Moves a character from the play area back to the owner's hand."""
        if character in self.play_area:
            self.play_area.remove(character)
            character.location = 'hand'
            self.hand.append(character)

    def banish_character(self, character: Card):
        """Moves a character from play. If it has Vanish, it returns to hand; otherwise, to discard."""
        if character in self.play_area:
            self.play_area.remove(character)

            if character.has_keyword('Vanish'):
                character.location = 'hand'
                character.damage_counters = 0  # Reset damage
                self.hand.append(character)
            else:
                character.location = 'discard'
                self.discard_pile.append(character)

    def activate_ability(self, card: Card, ability_index: int, game_turn: int) -> bool:
        """Activates a card's ability. Returns True on success."""
        if not (card in self.play_area and not card.is_exerted):
            return False

        if not (0 <= ability_index < len(card.abilities)):
            return False  # Invalid ability index

        ability = card.abilities[ability_index]
        if ability.trigger != "Activated":
            return False  # Not an activated ability

        # For now, assume the only cost is exerting the character.
        # This will be expanded later to handle ink costs, etc.
        card.is_exerted = True

        # --- Execute the effect ---
        self.game.effect_resolver.resolve_effect(
            ability,
            source_card=card,
            source_player=self,
            chosen_targets=None  # Activated abilities might need targets later
        )
        return True

    def get_valid_challenge_targets(self, challenger: Card, opponent: 'Player') -> list[Card]:
        """Returns a list of valid characters the given character can challenge."""
        # Bodyguard rule: If a character with Bodyguard is exerted, they must be challenged first.
        bodyguard_targets = [char for char in opponent.play_area if char.is_exerted and char.has_keyword('Bodyguard')]
        if bodyguard_targets:
            return bodyguard_targets

        valid_targets = []
        challenger_has_evasive = challenger.has_keyword('Evasive')

        for target in opponent.play_area:
            if not target.is_exerted:
                continue  # Can only challenge exerted characters

            # Evasive rule: Evasive characters can only be challenged by other Evasive characters.
            if target.has_keyword('Evasive') and not challenger_has_evasive:
                continue

            valid_targets.append(target)

        return valid_targets

    def get_valid_effect_targets(self, opponent: 'Player') -> list[Card]:
        """Returns a list of characters on the opponent's board that can be targeted by effects."""
        return [char for char in opponent.play_area if not char.has_keyword('Ward')]

    def can_play_card(self, card: Card) -> bool:
        """Checks if the player can afford to play a card normally."""
        return self.get_available_ink() >= card.cost

    def get_valid_challenge_targets(self, challenger: 'Card', opponent: 'Player') -> List['Card']:
        """Returns a list of valid characters the challenger can challenge."""
        # Bodyguard rule: If a character with Bodyguard is exerted, they must be challenged first.
        bodyguard_targets = [char for char in opponent.play_area if char.is_exerted and char.has_keyword('Bodyguard')]
        if bodyguard_targets:
            return bodyguard_targets

        # Evasive rule: Characters with Evasive can only be challenged by other characters with Evasive.
        valid_targets = []
        challenger_has_evasive = challenger.has_keyword('Evasive')

        for target in opponent.play_area:
            if not target.is_exerted:
                continue  # Can only challenge exerted characters

            if target.has_keyword('Evasive'):
                if challenger_has_evasive:
                    valid_targets.append(target)
            else:
                # Non-evasive characters can be challenged by anyone
                valid_targets.append(target)

        return valid_targets



class GameState:
    """The main container for the entire state of a single game."""
    def __init__(self, player1: Player, player2: Player):
        self.players = {player1.player_id: player1, player2.player_id: player2}
        self.current_player_id = player1.player_id
        self.turn_number = 1
        self.winner = None

    def get_player(self, player_id: int) -> Player:
        return self.players[player_id]

    def get_opponent(self, player_id: int) -> Player:
        return self.players[2 if player_id == 1 else 1]

    def challenge(self, attacker: Card, defender: Card) -> bool:
        """Executes a challenge between two characters. Returns True on success."""
        attacker_player = self.get_player(attacker.owner_player_id)
        defender_player = self.get_player(defender.owner_player_id)

        if not attacker_player._can_character_act(attacker, self.turn_number):
            return False
        if not defender.is_exerted:
            return False

        # Bodyguard rule: if a bodyguard is available, it must be challenged.
        if not defender.has_keyword('Bodyguard'):
            bodyguards = [c for c in defender_player.play_area if c.is_exerted and c.has_keyword('Bodyguard')]
            if bodyguards:
                return False # Illegal move: a Bodyguard character should have been challenged.

        attacker.is_exerted = True

        # Calculate effective strength and damage, accounting for keywords
        attacker_player = self.get_player(attacker.owner_player_id)
        attacker_strength = (attacker.strength or 0) + attacker_player.temporary_strength_mods.get(attacker.unique_id, 0)
        defender_strength = defender.strength or 0

        challenger_bonus = attacker.get_keyword_value('Challenger')
        if challenger_bonus:
            attacker_strength += challenger_bonus

        resist_value = defender.get_keyword_value('Resist')
        damage_to_defender = attacker_strength
        if resist_value:
            damage_to_defender = max(0, damage_to_defender - resist_value)

        # Deal damage
        defender.take_damage(damage_to_defender)
        attacker.take_damage(defender_strength)

        # Check for banishment
        if defender.willpower is not None and defender.damage_counters >= defender.willpower:
            defender_player.banish_character(defender)

        if attacker.willpower is not None and attacker.damage_counters >= attacker.willpower:
            attacker_player.banish_character(attacker)
            
        return True

    def _ready_phase(self):
        player = self.get_player(self.current_player_id)

        # 1. Ready all cards for the current player
        for card in player.play_area + player.inkwell:
            card.is_exerted = False

        # 2. Clear expired temporary effects for all characters in play
        for p in self.players.values():
            for character in p.play_area:
                if not hasattr(character, 'strength_modifiers'):
                    continue
                # Modifiers with a duration of 'start_of_turn' expire when that player's turn starts.
                character.strength_modifiers = [
                    mod for mod in character.strength_modifiers
                    if not (mod.get('duration') == 'start_of_turn' and mod.get('player_id') == self.current_player_id)
                ]

                # Clear expired keyword modifiers
                character.keyword_modifiers = [
                    mod for mod in character.keyword_modifiers
                    if not (mod.get('duration') == 'start_of_turn' and mod.get('player_id') == self.current_player_id)
                ]

    def _set_phase(self):
        pass

    def _draw_phase(self):
        if self.turn_number == 1 and self.current_player_id == 1:
            return
        player = self.get_player(self.current_player_id)
        if player.deck.is_empty():
            self.winner = self.get_opponent(self.current_player_id).player_id
            return
        player.draw_cards(1)

    def _check_win_conditions(self):
        for player_id, player in self.players.items():
            if player.lore >= 20:
                self.winner = player_id
                return

    def run_turn(self):
        if self.winner: return
        self._check_win_conditions()
        if self.winner: return
        self._ready_phase()
        self._set_phase()
        self._draw_phase()
        if self.winner: return

        # Main Phase - AI Logic
        player = self.get_player(self.current_player_id)
        player_logic.run_main_phase(self, player)

        self._check_win_conditions()

    def end_turn(self):
        if self.winner: return

        # Clear temporary effects for the active player before the turn ends.
        self.get_player(self.current_player_id).clear_temporary_mods()
        self.current_player_id = self.get_opponent(self.current_player_id).player_id
        if self.current_player_id == 1:
            self.turn_number += 1
