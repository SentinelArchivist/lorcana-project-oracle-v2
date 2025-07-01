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
    
    Heuristic Order:
    1. Ink a card.
    2. Sing a Song.
    3. Play a card with ink.
    4. Challenge.
    5. Quest.
    """
    # 1. Ink a card (once per turn)
    card_to_ink = choose_card_to_ink(player)
    if card_to_ink:
        player.ink_card(card_to_ink)

    # 2. Sing a Song (simple version: find first and best opportunity)
    singable_songs = sorted([c for c in player.hand if c.card_type == 'Song'], key=lambda c: c.cost, reverse=True)
    possible_singers = [char for char in player.play_area if player._can_character_act(char, game.turn_number) and char.has_keyword('Singer')]
    
    if singable_songs and possible_singers:
        song_to_sing = singable_songs[0]
        # Find a singer who can sing this song
        valid_singers = [s for s in possible_singers if s.get_keyword_value('Singer') >= song_to_sing.cost]
        if valid_singers:
            # Use the first available singer
            player.sing_song(song_to_sing, valid_singers[0], game.turn_number)

    # 3. Play a card with ink
    playable_cards = sorted([c for c in player.hand if c.cost <= player.get_available_ink()], key=lambda c: c.cost, reverse=True)
    if playable_cards:
        player.play_card(playable_cards[0], game.turn_number)

    # 4. Challenge
    my_ready_characters = [c for c in player.play_area if player._can_character_act(c, game.turn_number)]
    opponent = game.get_opponent(player.player_id)
    opponent_exerted_characters = [c for c in opponent.play_area if c.is_exerted]

    # AI Challenge Logic
    if my_ready_characters and opponent_exerted_characters:
        # Prioritize Bodyguard characters
        bodyguard_targets = [c for c in opponent_exerted_characters if c.has_keyword('Bodyguard')]
        if bodyguard_targets:
            # If there are bodyguards, they are the only valid targets
            target_pool = bodyguard_targets
        else:
            # Otherwise, any exerted character is a valid target
            target_pool = opponent_exerted_characters

        # Heuristic: challenge the strongest target with our strongest character
        my_best_challenger = max(my_ready_characters, key=lambda c: c.strength or 0)
        opponent_best_target = max(target_pool, key=lambda c: c.strength or 0)
        game.challenge(my_best_challenger, opponent_best_target)

    # 5. Quest
    # Quest with all remaining ready characters, using Support first.
    my_ready_characters = [c for c in player.play_area if player._can_character_act(c, game.turn_number)]
    for character in my_ready_characters:
        # This loop is safe because player.quest() checks _can_character_act again.
        support_target = None
        if character.has_keyword('Support'):
            # Heuristic: Find the strongest character on our board to receive the support.
            # Exclude the character itself.
            potential_targets = [t for t in player.play_area if t.unique_id != character.unique_id]
            if potential_targets:
                support_target = max(potential_targets, key=lambda c: c.strength or 0)

        player.quest(character, game.turn_number, support_target=support_target)
