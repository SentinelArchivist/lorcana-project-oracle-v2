from typing import List, Optional

# To avoid circular imports, we'll use string type hints for game engine classes
# and import them only for type checking if necessary.
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .game_engine import Card, GameState, Player

def choose_card_to_ink(player: 'Player') -> Optional['Card']:
    """
    Heuristic to decide which card to ink.
    Prioritizes non-essential, high-cost, or duplicate cards.
    
    Current simple heuristic:
    1. Find all inkable cards in hand.
    2. Of those, choose the one with the highest cost.
    3. If there's a tie, return the first one found.
    """
    inkable_cards = [card for card in player.hand if card.inkable]
    if not inkable_cards:
        return None

    # Sort by cost (descending) and return the highest-cost card
    inkable_cards.sort(key=lambda c: c.cost, reverse=True)
    return inkable_cards[0]

def run_main_phase(game: 'GameState', player: 'Player'):
    """
    Runs the main phase for a player using a set of heuristics.
    This function will contain the logic for the AI to decide what actions to take.
    
    Heuristic Order:
    1. Ink a card if it's a good idea.
    2. Play cards from hand.
    3. Challenge opponents.
    4. Quest with remaining characters.
    """
    # For now, we will implement a simple version of this logic.
    # A more advanced AI would loop until no more actions can be taken.

    # 1. Ink a card (once per turn)
    card_to_ink = choose_card_to_ink(player)
    if card_to_ink:
        player.ink_card(card_to_ink)

    # 2. Play cards
    # Simple heuristic: play the highest-cost card possible.
    playable_cards = sorted([c for c in player.hand if c.cost <= player.get_available_ink()], key=lambda c: c.cost, reverse=True)
    if playable_cards:
        player.play_card(playable_cards[0], game.turn_number)

    # 3. Challenge
    # Simple heuristic: find the first available challenge and take it.
    my_ready_characters = [c for c in player.play_area if player._can_character_act(c, game.turn_number)]
    opponent = game.get_opponent(player.player_id)
    opponent_exerted_characters = [c for c in opponent.play_area if c.is_exerted]
    if my_ready_characters and opponent_exerted_characters:
        # Find the strongest character to attack the opponent's strongest character
        my_best_challenger = max(my_ready_characters, key=lambda c: c.strength or 0)
        opponent_best_target = max(opponent_exerted_characters, key=lambda c: c.strength or 0)
        game.challenge(my_best_challenger, opponent_best_target)

    # 4. Quest
    # Quest with all remaining ready characters
    # We need to re-fetch ready characters in case one was used for a challenge
    my_final_ready_characters = [c for c in player.play_area if player._can_character_act(c, game.turn_number)]
    for character in my_final_ready_characters:
        player.quest(character, game.turn_number)
