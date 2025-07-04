import random
import json
import uuid
from typing import List, Dict, Optional, Any, TYPE_CHECKING
import pandas as pd

from . import player_logic
from .effect_resolver import EffectResolver

if TYPE_CHECKING:
    from .game_engine import GameState

class Card:
    """Represents a single instance of a card within a game."""
    def __init__(self, card_data: Dict[str, Any], owner_player_id: int):
        # Generate a unique ID if not provided
        self.unique_id = card_data.get('Unique_ID') or str(uuid.uuid4())
        self.name = card_data.get('Name')
        self.cost = card_data.get('Cost', 0)
        self.inkable = card_data.get('Inkable', False)
        self.lore = card_data.get('Lore', 0)
        self.card_type = card_data.get('Type', 'Character') # Character, Action, Item
        keywords_data = card_data.get('Keywords')
        if isinstance(keywords_data, str):
            self.keywords = {kw.strip() for kw in keywords_data.split(',')}
        elif isinstance(keywords_data, list):
            self.keywords = set(keywords_data)
        else:
            self.keywords = set()

        schema_abilities_data = card_data.get('schema_abilities', '[]')
        self.abilities: List[Dict[str, Any]] = []
        if isinstance(schema_abilities_data, str):
            try:
                self.abilities = json.loads(schema_abilities_data)
            except json.JSONDecodeError:
                self.abilities = []
        elif isinstance(schema_abilities_data, list):
            self.abilities = schema_abilities_data
        self.owner_player_id = owner_player_id
        self.is_exerted = False
        self.damage_counters = 0
        self.location = 'deck'
        self.turn_played: Optional[int] = None
        self._base_strength: Optional[int] = card_data.get('Strength')
        self.willpower: Optional[int] = card_data.get('Willpower')
        self.strength_modifiers: List[Dict[str, Any]] = []
        self.keyword_modifiers: List[Dict[str, Any]] = []

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
        if any(kw.lower().startswith(keyword.lower()) for kw in self.keywords):
            return True
            
        # Handle ability keywords - check both dict and object styles
        for ability in self.abilities:
            # Handle dictionary-style abilities
            if isinstance(ability, dict):
                if isinstance(ability.get('value'), dict) and ability['value'].get('keyword') == keyword:
                    return True
            # Handle ParsedAbility objects
            elif hasattr(ability, 'value'):
                if isinstance(ability.value, dict) and ability.value.get('keyword') == keyword:
                    return True
                    
        # Check keyword modifiers
        for modifier in self.keyword_modifiers:
            if modifier.get('keyword') == keyword:
                return True
                
        return False

    def get_keyword_value(self, keyword: str) -> Optional[int]:
        """Get the numeric value associated with a keyword (e.g., Challenger +X, Shift X)."""
        for kw_string in self.keywords:
            if kw_string.lower().startswith(keyword.lower()):
                parts = kw_string.split()
                if len(parts) > 1:
                    try:
                        return int(parts[-1])
                    except (ValueError, IndexError):
                        continue
        for ability in self.abilities:
            if isinstance(ability.get('value'), dict) and ability['value'].get('keyword', '').lower() == keyword.lower():
                value = ability['value'].get('amount')
                if isinstance(value, int):
                    return value
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
    def __init__(self, player_id: int, initial_deck: Optional[Deck] = None, deck_list: Optional[List[str]] = None, card_data: Optional[pd.DataFrame] = None):
        """
        Initializes a Player.

        Can be initialized in two ways:
        1. With a pre-made Deck object.
        2. With a list of card names and a pandas DataFrame containing all card data.
        """
        self.player_id = player_id
        
        if initial_deck is not None:
            self.deck = initial_deck
        elif deck_list is not None and card_data is not None:
            card_objects = []
            for card_name in deck_list:
                # Find all rows that match the card name
                card_data_rows = card_data[card_data['Name'] == card_name]
                if not card_data_rows.empty:
                    # Use the first match
                    card_info = card_data_rows.iloc[0].to_dict()
                    card_objects.append(Card(card_info, owner_player_id=self.player_id))
                else:
                    print(f"Warning: Card '{card_name}' not found in dataset. Skipping.")
            self.deck = Deck(card_objects)
        else:
            # If no deck information is provided, initialize with an empty deck.
            # This is useful for testing purposes.
            self.deck = Deck([])

        self.hand: List[Card] = []
        self.inkwell: List[Card] = []
        self.play_area: List[Card] = []
        self.discard_pile: List[Card] = []
        self.locations: List[Card] = []  # Added missing locations attribute
        self.lore = 0
        self.has_inked_this_turn = False

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
        """Returns the number of un-exerted cards in the inkwell."""
        return sum(1 for card in self.inkwell if not card.is_exerted)

    def ready_cards(self):
        """Readies all cards in the inkwell and play area."""
        for card in self.inkwell:
            card.is_exerted = False
        for card in self.play_area:
            card.is_exerted = False

    def _can_character_act(self, character: Card, game_turn: int) -> bool:
        """Checks if a character can perform an action (ink is 'dry')."""
        if character.is_exerted:
            return False
        if character.has_keyword('Rush'):
            return True
        # A character's ink is 'wet' on the turn it is played
        return character.turn_played is None or character.turn_played < game_turn

    def ink_card(self, card: Card) -> bool:
        """Moves a card from hand to inkwell. Returns True on success."""
        if self.has_inked_this_turn:
            return False
        if not card.inkable:
            return False
        if card not in self.hand:
            raise ValueError("Card to be inked is not in the player's hand.")
        self.hand.remove(card)
        self.inkwell.append(card)
        card.location = 'inkwell'
        card.is_exerted = True
        self.has_inked_this_turn = True
        return True

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

    def play_card(self, card: 'Card', game: 'GameState', shift_target: Optional['Card'] = None, chosen_targets: Optional[List['Card']] = None):
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
            card.is_exerted = shift_target.is_exerted
            card.damage_counters = shift_target.damage_counters
            card.strength_modifiers = list(shift_target.strength_modifiers)
            card.keyword_modifiers = list(shift_target.keyword_modifiers)
            card.turn_played = shift_target.turn_played
            self.play_area.remove(shift_target)
            self.discard_pile.append(shift_target)
            shift_target.location = 'discard'
            card.location = 'play_area'
            self.play_area.append(card)
        elif card.card_type in ['Character', 'Item']:
            card.location = 'play_area'
            self.play_area.append(card)
            card.turn_played = game.turn_number
        elif card.card_type == 'Location':
            card.location = 'play_area'
            self.locations.append(card)
        elif card.card_type in ['Action', 'Song']:
            card.location = 'discard'
            self.discard_pile.append(card)

        # Resolve OnPlay abilities
        for ability in card.abilities:
            # Handle ability as either dict or object
            if isinstance(ability, dict):
                trigger = ability.get('trigger')
            elif hasattr(ability, 'trigger'):
                trigger = ability.trigger
            else:
                continue  # Skip abilities with unknown format
                
            if trigger and trigger.upper() == "ON_PLAY":
                if game.effect_resolver:
                    game.effect_resolver.resolve_effect(ability, source_card=card, chosen_targets=chosen_targets)

    def sing_song(self, song_card: Card, singer: Card, game_turn: int) -> bool:
        """Plays a song by exerting a single character. Returns True on success."""
        return self.sing_song_together(song_card, [singer], game_turn)
        
    def sing_song_together(self, song_card: Card, singers: list[Card], game_turn: int) -> bool:
        """Plays a song by exerting multiple characters together (Sing Together mechanic).
        
        Returns True on success.
        
        The combined Singer values of all singers must be at least equal to the song's cost.
        All singers must be able to act (not exerted and ink is dry).
        """
        # Check if the song is in hand and is actually a Song card
        if song_card not in self.hand or song_card.card_type != 'Song':
            return False
            
        # Validate all singers
        total_singer_value = 0
        for singer in singers:
            # Check if singer is in play area and can act
            if (singer not in self.play_area or 
                not self._can_character_act(singer, game_turn)):
                return False
            
            # Check if it has the Singer keyword
            singer_ability_cost = singer.get_keyword_value('Singer')
            if singer_ability_cost is None:
                return False
                
            total_singer_value += singer_ability_cost
        
        # Check if the combined Singer value is enough for the song
        if total_singer_value < song_card.cost:
            return False
            
        # Success! Exert all singers and play the song
        for singer in singers:
            singer.is_exerted = True
            
        self.hand.remove(song_card)
        song_card.location = 'discard'
        self.discard_pile.append(song_card)
        return True

    def clear_temporary_mods(self):
        """Clears any temporary modifications, like from Support."""
        self.temporary_strength_mods.clear()

    def quest(self, character: Card, game_turn: int, support_target: Optional[Card] = None) -> bool:
        """Quests with a character. Returns True on success."""
        if character in self.play_area and self._can_character_act(character, game_turn):
            character.is_exerted = True
            self.lore += character.lore
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
                character.damage_counters = 0
                self.hand.append(character)
            else:
                character.location = 'discard'
                self.discard_pile.append(character)

    def activate_ability(self, card: Card, ability_index: int, game: 'GameState') -> bool:
        """Activates a card's ability. Returns True on success."""
        if not (card in self.play_area and not card.is_exerted):
            return False
        if not (0 <= ability_index < len(card.abilities)):
            return False
        ability = card.abilities[ability_index]
        if ability.get('trigger', {}).get('type') != "ACTIVATED":
            return False
        card.is_exerted = True
        game.effect_resolver.resolve_effect(ability, source_card=card, chosen_targets=None)
        return True

    def get_valid_challenge_targets(self, challenger: Card, opponent: 'Player') -> list[Card]:
        """Returns a list of valid characters the given character can challenge."""
        # First check for bodyguards (they must be challenged first if present)
        bodyguard_targets = [char for char in opponent.play_area if char.is_exerted and char.has_keyword('Bodyguard')]
        if bodyguard_targets:
            return self._filter_invalid_challenge_targets(challenger, bodyguard_targets)
            
        # Find all valid targets based on game rules
        valid_targets = []
        challenger_has_evasive = challenger.has_keyword('Evasive')
        for target in opponent.play_area:
            if not target.is_exerted:
                continue
            if target.has_keyword('Evasive') and not challenger_has_evasive:
                continue
            valid_targets.append(target)
            
        # Filter out invalid targets (e.g., self-challenge)
        return self._filter_invalid_challenge_targets(challenger, valid_targets)
        
    def _filter_invalid_challenge_targets(self, challenger: Card, targets: list[Card]) -> list[Card]:
        """Filters out invalid challenge targets (e.g., self-challenge, same name, or Location)."""
        # Remove targets that are the same card, have the same name as the challenger, or are Locations
        # Also prevent Locations from initiating challenges
        return [target for target in targets 
                if target.unique_id != challenger.unique_id 
                and target.name != challenger.name 
                and target.card_type != 'Location' 
                and challenger.card_type != 'Location']

    def get_valid_effect_targets(self, opponent: 'Player') -> list[Card]:
        """Returns a list of characters on the opponent's board that can be targeted by effects."""
        return [char for char in opponent.play_area if not char.has_keyword('Ward')]

    def can_play_card(self, card: Card) -> bool:
        """Checks if the player can afford to play a card normally."""
        return self.get_available_ink() >= card.cost

class GameState:
    """Manages the entire state and flow of a Lorcana game."""
    def __init__(self, player1: Player, player2: Player):
        self.players = {
            1: player1,
            2: player2
        }
        self.players[1].game = self
        self.players[2].game = self
        self.turn_number = 1
        self.current_player_id = 1
        self.initial_player_id = 1
        self.winner: Optional[int] = None
        self.effect_resolver = EffectResolver(game=self, card_class=Card, player_class=Player)

    def get_player(self, player_id: int) -> Player:
        """Gets a player by their ID."""
        return self.players[player_id]

    def get_opponent(self, player_id: int) -> Player:
        """Gets the opponent of a given player."""
        return self.players[2 if player_id == 1 else 1]

    def _check_for_winner(self):
        """Checks win conditions: lore count and decking out."""
        for player_id, player in self.players.items():
            if player.lore >= 20:
                self.winner = player_id
                return
            if player.deck.is_empty() and not any(card.location == 'hand' for card in player.hand):
                # This is a simplified deck-out rule. A more accurate one might be needed.
                self.winner = self.get_opponent(player_id).player_id
                return

    def _ready_phase(self):
        """Start of turn: Ready all cards for the current player."""
        player = self.get_player(self.current_player_id)
        player.ready_cards()
        # Here you would also handle 'start of turn' effects

    def _set_phase(self):
        """Start of turn: Check for and trigger any start-of-turn abilities."""
        # Process Location cards for passive lore gain
        player = self.get_player(self.current_player_id)
        for card in player.play_area:
            if card.card_type == 'Location' and card.lore > 0:
                player.lore += card.lore
                print(f"{player.player_id} gained {card.lore} lore from {card.name}")
        
        # Add placeholder for other start-of-turn triggers to be implemented later
        pass

    def _draw_phase(self):
        """Current player draws a card."""
        player = self.get_player(self.current_player_id)
        if self.turn_number == 1 and self.current_player_id == self.initial_player_id:
            return  # First player skips their first draw

        if player.deck.is_empty():
            self.winner = self.get_opponent(self.current_player_id).player_id
            return

        player.draw_cards(1)
        self._check_for_winner() # Check for deck-out loss

    def challenge(self, challenger: Card, target: Card) -> bool:
        """Resolves a challenge between two characters."""
        challenger_player = self.get_player(challenger.owner_player_id)
        target_player = self.get_player(target.owner_player_id)

        if not challenger_player._can_character_act(challenger, self.turn_number):
            raise ValueError(f"{challenger.name} cannot act this turn.")
        if target not in challenger_player.get_valid_challenge_targets(challenger, target_player):
            raise ValueError(f"{target.name} is not a valid challenge target for {challenger.name}.")

        challenger.is_exerted = True

        # Calculate effective strength for the challenge
        challenger_strength = challenger.strength or 0
        challenger_strength += challenger_player.temporary_strength_mods.get(challenger.unique_id, 0)

        target_strength = target.strength or 0

        # Challenger keyword bonus
        challenger_bonus = challenger.get_keyword_value('Challenger')
        if challenger_bonus:
            challenger_strength += challenger_bonus

        # Resist keyword reduction
        resist_value = target.get_keyword_value('Resist')
        if resist_value:
            challenger_strength = max(0, challenger_strength - resist_value)

        # Deal damage
        if target_strength > 0:
            challenger.take_damage(target_strength)
        if challenger_strength > 0:
            target.take_damage(challenger_strength)

        # Check for banishment
        if challenger.willpower is not None and challenger.damage_counters >= challenger.willpower:
            challenger_player.banish_character(challenger)
        if target.willpower is not None and target.damage_counters >= target.willpower:
            target_player.banish_character(target)

        return True

    def run_turn(self):
        """Executes a single full turn for the current player."""
        if self.winner: return
        self._check_for_winner()
        if self.winner: return

        self._ready_phase()
        self._set_phase()
        self._draw_phase()
        if self.winner: return

        player = self.get_player(self.current_player_id)
        player_logic.run_main_phase(self, player)

        self._check_for_winner()

    def end_turn(self):
        """Ends the current turn and passes to the next player."""
        if self.winner: return

        current_player = self.get_player(self.current_player_id)
        current_player.clear_temporary_mods()
        current_player.has_inked_this_turn = False

        self.current_player_id = self.get_opponent(self.current_player_id).player_id
        if self.current_player_id == self.initial_player_id:
            self.turn_number += 1

    def run_game(self, max_turns=100) -> Optional[Player]:
        """Runs the game loop until a winner is found or max turns are reached."""
        self.players[1].draw_initial_hand()
        self.players[2].draw_initial_hand()

        while self.winner is None and self.turn_number <= max_turns:
            self.run_turn()
            self.end_turn()

        if self.winner is not None:
            return self.get_player(self.winner)

        # If no winner after max_turns, decide by lore count
        player1_lore = self.players[1].lore
        player2_lore = self.players[2].lore
        if player1_lore > player2_lore:
            return self.players[1]
        elif player2_lore > player1_lore:
            return self.players[2]
        else:
            return None # Draw
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
