from typing import List, Optional, Any
from abc import ABC, abstractmethod

# To avoid circular imports, we'll use string type hints for game engine classes
# and import them only for type checking if necessary.
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .game_engine import Card, GameState, Player

# --- Action Abstraction ---
class Action(ABC):
    """Abstract base class for any action a player can take."""
    def __init__(self, score: float = 0.0):
        self.score = score

    @abstractmethod
    def execute(self, game: 'GameState', player: 'Player'):
        pass

    def __repr__(self):
        return f"{self.__class__.__name__}(score={self.score})"

class InkAction(Action):
    def __init__(self, card: 'Card'):
        super().__init__()
        self.card = card

    def execute(self, game: 'GameState', player: 'Player'):
        player.ink_card(self.card)

    def __repr__(self):
        return f"InkAction(card={self.card.name}, score={self.score})"

class PlayCardAction(Action):
    def __init__(self, card: 'Card', shift_target: Optional['Card'] = None):
        super().__init__()
        self.card = card
        self.shift_target = shift_target

    def execute(self, game: 'GameState', player: 'Player'):
        player.play_card(self.card, game, shift_target=self.shift_target)

    def __repr__(self):
        if self.shift_target:
            return f"PlayCardAction(card={self.card.name}, shift_on={self.shift_target.name}, score={self.score})"
        return f"PlayCardAction(card={self.card.name}, score={self.score})"

class QuestAction(Action):
    def __init__(self, character: 'Card', support_target: Optional['Card'] = None):
        super().__init__()
        self.character = character
        self.support_target = support_target

    def execute(self, game: 'GameState', player: 'Player'):
        player.quest(self.character, game.turn_number, self.support_target)

    def __repr__(self):
        return f"QuestAction(character={self.character.name}, score={self.score})"

class ChallengeAction(Action):
    def __init__(self, attacker: 'Card', defender: 'Card'):
        super().__init__()
        self.attacker = attacker
        self.defender = defender

    def execute(self, game: 'GameState', player: 'Player'):
        game.challenge(self.attacker, self.defender)

    def __repr__(self):
        return f"ChallengeAction(attacker={self.attacker.name}, defender={self.defender.name}, score={self.score})"

class SingAction(Action):
    def __init__(self, song_card: 'Card', singer: 'Card'):
        super().__init__()
        self.song_card = song_card
        self.singer = singer

    def execute(self, game: 'GameState', player: 'Player'):
        player.sing_song(self.song_card, self.singer, game.turn_number)

    def __repr__(self):
        return f"SingAction(song={self.song_card.name}, singer={self.singer.name}, score={self.score})"

class ActivateAbilityAction(Action):
    def __init__(self, character: 'Card', ability_index: int):
        super().__init__()
        self.character = character
        self.ability_index = ability_index

    def execute(self, game: 'GameState', player: 'Player'):
        player.activate_ability(self.character, self.ability_index, game.turn_number)

    def __repr__(self):
        return f"ActivateAbilityAction: Use {self.character.name}'s ability #{self.ability_index}, score={self.score}"

# --- Heuristics and Evaluation ---

def evaluate_actions(actions: List[Action], game: 'GameState', player: 'Player'):
    """
    Scores each possible action based on a set of heuristics.
    This is the core 'brain' of the AI.
    """
    for action in actions:
        if isinstance(action, QuestAction):
            # Base score is the lore gained.
            action.score = action.character.lore or 0
            if action.character.has_keyword('Support'):
                # Small bonus for using support
                action.score += 0.5

        elif isinstance(action, ChallengeAction):
            # Heuristic for evaluating a challenge trade.
            attacker = action.attacker
            defender = action.defender
            
            # Simulate damage
            attacker_strength = (attacker.strength or 0) + player.temporary_strength_mods.get(attacker.unique_id, 0)
            if attacker.has_keyword('Challenger'):
                challenger_bonus = attacker.get_keyword_value('Challenger')
                if challenger_bonus:
                    attacker_strength += challenger_bonus

            damage_to_defender = attacker_strength
            if defender.has_keyword('Resist'):
                resist_value = defender.get_keyword_value('Resist')
                if resist_value:
                    damage_to_defender = max(0, damage_to_defender - resist_value)
            
            defender_will_be_banished = (defender.damage_counters + damage_to_defender) >= (defender.willpower or 999)
            attacker_will_be_banished = (attacker.damage_counters + (defender.strength or 0)) >= (attacker.willpower or 999)

            # Scoring based on trade outcome
            score = 0
            if defender_will_be_banished:
                # Big score for banishing an opponent's character
                score += (defender.strength or 0) + (defender.willpower or 0) + (defender.lore or 0)
            if attacker_will_be_banished:
                # Negative score for losing our character
                score -= (attacker.strength or 0) + (attacker.willpower or 0) + (attacker.lore or 0)
            
            # Bonus for removing a character with lore
            if defender_will_be_banished and (defender.lore or 0) > 0:
                score += defender.lore * 1.5

            action.score = score

        elif isinstance(action, PlayCardAction):
            # Simple heuristic: score is based on stats for cost.
            card = action.card
            stats_score = (card.strength or 0) + (card.willpower or 0) + (card.lore or 0)
            action.score = stats_score - card.cost

        elif isinstance(action, InkAction):
            # Inking is generally a setup move, so it should have a low but positive score
            # to be chosen when no better plays are available.
            action.score = 0.1 # Small positive score to do it if nothing else is better

        elif isinstance(action, SingAction):
            # Singing a song is good tempo. Score it higher than just playing the card.
            action.score = action.song_card.cost # Free value is good

        elif isinstance(action, ActivateAbilityAction):
            ability = action.character.abilities[action.ability_index]
            if ability.effect == "DrawCard":
                action.score = 28 # Drawing cards is very good
            else:
                action.score = 10 # Default for other abilities for now

def get_possible_actions(game: 'GameState', player: 'Player', has_inked: bool) -> List[Action]:
    """Enumerates all legal actions the player can take, respecting keywords like Reckless."""
    actions: List[Action] = []
    opponent = game.get_opponent(player.player_id)

    # 1. Ink action (if not already done)
    if not has_inked:
        inkable_cards = [card for card in player.hand if card.inkable]
        if inkable_cards:
            # Simple heuristic: ink highest cost card
            inkable_cards.sort(key=lambda c: c.cost, reverse=True)
            actions.append(InkAction(inkable_cards[0]))

    # 2. Play card actions (Normal and Shift)
    available_ink = player.get_available_ink()
    for card in player.hand:
        # Normal play
        if player.can_play_card(card):
            actions.append(PlayCardAction(card))

        # Shift play
        if card.has_keyword('Shift'):
            shift_cost = card.get_keyword_value('Shift')
            if shift_cost is not None and player.get_available_ink() >= shift_cost:
                shift_targets = player.get_possible_shift_targets(card)
                for target in shift_targets:
                    actions.append(PlayCardAction(card, shift_target=target))

    # 3. Character actions (Quest, Challenge, Abilities, Sing)
    # This section is refactored to be character-centric to handle Reckless correctly.
    ready_characters = [c for c in player.play_area if player._can_character_act(c, game.turn_number)]

    for char in ready_characters:
        # A character that is Reckless MUST challenge if able.
        if char.has_keyword('Reckless'):
            valid_targets = player.get_valid_challenge_targets(char, opponent)
            if valid_targets:
                # This character can only challenge. Add challenge actions and nothing else for this character.
                for defender in valid_targets:
                    actions.append(ChallengeAction(char, defender))
                continue  # Move to the next character

        # If the character is not Reckless (or is Reckless but cannot challenge), generate its other actions.

        # Quest Action
        support_target = None
        if char.has_keyword('Support'):
            potential_targets = [t for t in player.play_area if t.unique_id != char.unique_id]
            if potential_targets:
                # A real AI would pick the best target, for now we just pick the strongest
                support_target = max(potential_targets, key=lambda c: c.strength or 0)
        actions.append(QuestAction(char, support_target))

        # Challenge Actions (for non-reckless characters)
        valid_targets = player.get_valid_challenge_targets(char, opponent)
        for defender in valid_targets:
            actions.append(ChallengeAction(char, defender))

        # Activated Ability Actions
        for i, ability in enumerate(char.abilities):
            if ability.trigger == "Activated":
                actions.append(ActivateAbilityAction(char, i))

        # Sing Actions
        if char.has_keyword('Singer'):
            singable_songs = [c for c in player.hand if c.card_type == 'Song']
            for song in singable_songs:
                # Check if the singer can sing this song for free
                if char.get_keyword_value('Singer') >= song.cost:
                    actions.append(SingAction(song, char))

    return actions

def run_main_phase(game: 'GameState', player: 'Player'):
    """
    Runs the main phase for a player using a flexible, heuristic-driven loop.
    The AI will continuously evaluate all possible actions and choose the best one
    until it decides to pass the turn.
    """
    has_inked_this_turn = False

    while True:
        possible_actions = get_possible_actions(game, player, has_inked_this_turn)
        
        if not possible_actions:
            break # No more actions to take

        evaluate_actions(possible_actions, game, player)
        
        possible_actions.sort(key=lambda a: a.score, reverse=True)
        best_action = possible_actions[0]

        # If the best available action has a negative or zero score, the AI decides to stop.
        # Exception: Inking is a low-score setup move we should do if available.
        if best_action.score <= 0 and not isinstance(best_action, InkAction):
            break

        # Execute the best action
        best_action.execute(game, player)

        if isinstance(best_action, InkAction):
            has_inked_this_turn = True
