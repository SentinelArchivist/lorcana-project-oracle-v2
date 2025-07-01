import random
from typing import List, Dict, Optional, Any

class Card:
    """
    Represents a single instance of a card within a game.
    It holds both the static data from the master dataset and its dynamic state in the game.
    """
    def __init__(self, card_data: Dict[str, Any], owner_player_id: int):
        # Static data from the CSV
        self.unique_id = card_data.get('Unique_ID')
        self.name = card_data.get('Name')
        self.cost = card_data.get('Cost')
        self.inkable = card_data.get('Inkable')
        self.strength = card_data.get('Strength')
        self.willpower = card_data.get('Willpower')
        self.lore = card_data.get('Lore')
        # Dynamic state for an individual game
        self.owner_player_id = owner_player_id
        self.is_exerted = False
        self.damage_counters = 0
        self.location = 'deck' # deck, hand, inkwell, play, discard

    def __repr__(self) -> str:
        return f"Card({self.name})"

class Deck:
    """
    Represents a player's deck of 60 cards.
    """
    def __init__(self, card_list: List[Card]):
        self.cards = card_list
        self.shuffle()

    def shuffle(self):
        """Shuffles the deck randomly."""
        random.shuffle(self.cards)

    def draw(self) -> Optional[Card]:
        """Draws a card from the top of the deck."""
        if self.cards:
            return self.cards.pop(0)
        return None

    def is_empty(self) -> bool:
        """Checks if the deck is out of cards."""
        return not self.cards

class Player:
    """
    Represents a player in the game, holding their state and all their cards.
    """
    def __init__(self, player_id: int, deck: Deck):
        self.player_id = player_id
        self.deck = deck
        self.hand: List[Card] = []
        self.inkwell: List[Card] = []
        self.play_area: List[Card] = []
        self.discard_pile: List[Card] = []
        self.lore = 0

    def draw_initial_hand(self, num_cards: int = 7):
        """Draws the initial hand of 7 cards."""
        for _ in range(num_cards):
            card = self.deck.draw()
            if card:
                card.location = 'hand'
                self.hand.append(card)

class GameState:
    """
    The main container for the entire state of a single game.
    It manages players, turns, and the overall game flow.
    """
    def __init__(self, player1: Player, player2: Player):
        self.players = {player1.player_id: player1, player2.player_id: player2}
        self.current_player_id = player1.player_id
        self.turn_number = 1

    def get_player(self, player_id: int) -> Player:
        """Gets a player object by their ID."""
        return self.players[player_id]

    def get_opponent(self, player_id: int) -> Player:
        """Gets the opponent of a given player."""
        opponent_id = 2 if player_id == 1 else 1
        return self.players[opponent_id]
