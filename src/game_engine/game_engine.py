import random
from typing import List, Dict, Optional, Any

from . import player_logic

class Card:
    """Represents a single instance of a card within a game."""
    def __init__(self, card_data: Dict[str, Any], owner_player_id: int):
        self.unique_id = card_data.get('Unique_ID')
        self.name = card_data.get('Name')
        self.cost = card_data.get('Cost', 0)
        self.inkable = card_data.get('Inkable', False)
        self.strength = card_data.get('Strength')
        self.willpower = card_data.get('Willpower')
        self.lore = card_data.get('Lore', 0)
        self.owner_player_id = owner_player_id
        self.is_exerted = False
        self.damage_counters = 0
        self.location = 'deck'
        self.turn_played: Optional[int] = None # For "ink drying" rule

    def __repr__(self) -> str:
        return f"Card({self.name})"

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
        self.discard_pile: List[Card] = []
        self.lore = 0

    def draw_initial_hand(self, num_cards: int = 7):
        for _ in range(num_cards):
            card = self.deck.draw()
            if card:
                card.location = 'hand'
                self.hand.append(card)

    def get_available_ink(self) -> int:
        """Returns the number of unexerted cards in the inkwell."""
        return sum(1 for card in self.inkwell if not card.is_exerted)

    def _can_character_act(self, character: Card, game_turn: int) -> bool:
        """Checks if a character can perform an action (ink is 'dry')."""
        if character.is_exerted:
            return False
        if character.turn_played is None or character.turn_played >= game_turn:
            return False # Must have been played in a previous turn
        return True

    def ink_card(self, card: Card) -> bool:
        """Moves a card from hand to inkwell. Returns True on success."""
        if card in self.hand and card.inkable:
            self.hand.remove(card)
            card.location = 'inkwell'
            card.is_exerted = True # Inked cards enter exerted
            self.inkwell.append(card)
            return True
        return False

    def play_card(self, card: Card, game_turn: int) -> bool:
        """Plays a card from hand to the play area. Returns True on success."""
        if card in self.hand and self.get_available_ink() >= card.cost:
            # Exert the ink
            ink_to_exert = card.cost
            for ink_card in self.inkwell:
                if not ink_card.is_exerted and ink_to_exert > 0:
                    ink_card.is_exerted = True
                    ink_to_exert -= 1
            
            self.hand.remove(card)
            card.location = 'play'
            card.turn_played = game_turn
            self.play_area.append(card)
            return True
        return False

    def quest(self, character: Card, game_turn: int) -> bool:
        """Quests with a character. Returns True on success."""
        if character in self.play_area and self._can_character_act(character, game_turn):
            character.is_exerted = True
            self.lore += character.lore
            return True
        return False

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

        attacker.is_exerted = True
        
        # Deal damage
        if attacker.strength is not None:
            defender.damage_counters += attacker.strength
        if defender.strength is not None:
            attacker.damage_counters += defender.strength

        # Check for banishment
        if defender.willpower is not None and defender.damage_counters >= defender.willpower:
            defender_player.play_area.remove(defender)
            defender.location = 'discard'
            defender_player.discard_pile.append(defender)

        if attacker.willpower is not None and attacker.damage_counters >= attacker.willpower:
            attacker_player.play_area.remove(attacker)
            attacker.location = 'discard'
            attacker_player.discard_pile.append(attacker)
            
        return True

    def _ready_phase(self):
        player = self.get_player(self.current_player_id)
        for card in player.play_area + player.inkwell:
            card.is_exerted = False

    def _set_phase(self):
        pass

    def _draw_phase(self):
        if self.turn_number == 1 and self.current_player_id == 1:
            return
        player = self.get_player(self.current_player_id)
        if player.deck.is_empty():
            self.winner = self.get_opponent(self.current_player_id).player_id
            return
        card = player.deck.draw()
        if card:
            card.location = 'hand'
            player.hand.append(card)

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
        self.current_player_id = self.get_opponent(self.current_player_id).player_id
        if self.current_player_id == 1:
            self.turn_number += 1
