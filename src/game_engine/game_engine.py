import random
from typing import List, Dict, Optional, Any

# --- Core Classes (from Task 2.1) ---

class Card:
    """Represents a single instance of a card within a game."""
    def __init__(self, card_data: Dict[str, Any], owner_player_id: int):
        self.unique_id = card_data.get('Unique_ID')
        self.name = card_data.get('Name')
        self.cost = card_data.get('Cost')
        self.inkable = card_data.get('Inkable')
        self.strength = card_data.get('Strength')
        self.willpower = card_data.get('Willpower')
        self.lore = card_data.get('Lore')
        self.owner_player_id = owner_player_id
        self.is_exerted = False
        self.damage_counters = 0
        self.location = 'deck'

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
    """Represents a player in the game."""
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

# --- Turn Structure and Game Loop (Task 2.2) ---

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

    def _ready_phase(self):
        """Ready all of the current player's cards."""
        player = self.get_player(self.current_player_id)
        for card in player.play_area:
            card.is_exerted = False

    def _set_phase(self):
        """Handle start-of-turn effects. (Placeholder for now)"""
        # This is where abilities like "At the start of your turn..." would trigger.
        pass

    def _draw_phase(self):
        """Current player draws a card, checking for loss condition."""
        # The first player skips the draw on their first turn.
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
        """Check if any player has met the lore win condition."""
        for player_id, player in self.players.items():
            if player.lore >= 20:
                self.winner = player_id
                return

    def run_turn(self):
        """Executes the sequence of phases for a single turn."""
        if self.winner:
            return

        self._check_win_conditions() # Check at start of turn
        if self.winner:
            return

        # 1. Ready Phase
        self._ready_phase()

        # 2. Set Phase
        self._set_phase()

        # 3. Draw Phase
        self._draw_phase()
        if self.winner: # Check for loss on draw
            return

        # 4. Main Phase (Placeholder for player actions)
        # In the full simulation, this would be a loop where the AI makes decisions.
        # For now, we just check for wins and end the turn.

        self._check_win_conditions() # Check after actions

    def end_turn(self):
        """Passes the turn to the next player."""
        if self.winner:
            return
        self.current_player_id = self.get_opponent(self.current_player_id).player_id
        if self.current_player_id == 1:
            self.turn_number += 1
