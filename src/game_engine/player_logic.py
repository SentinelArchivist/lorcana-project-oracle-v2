from typing import List, Optional, Any, Tuple
from abc import ABC, abstractmethod

# To avoid circular imports, we'll use string type hints for game engine classes
# and import them only for type checking if necessary.
from typing import TYPE_CHECKING
from .advanced_heuristics import evaluate_board_state, evaluate_inkwell_candidate, perform_lookahead_analysis
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
        return f"{self.__class__.__name__}" # Score is transient, not part of identity

class InkAction(Action):
    def __init__(self, card: 'Card'):
        super().__init__()
        self.card = card

    def execute(self, game: 'GameState', player: 'Player'):
        player.ink_card(self.card)

    def __repr__(self):
        return f"InkAction(card={self.card.name})"

class PlayCardAction(Action):
    def __init__(self, card: 'Card', shift_target: Optional['Card'] = None):
        super().__init__()
        self.card = card
        self.shift_target = shift_target

    def execute(self, game: 'GameState', player: 'Player'):
        player.play_card(self.card, game, shift_target=self.shift_target)

    def __repr__(self):
        if self.shift_target:
            return f"PlayCardAction(card={self.card.name}, shift_on={self.shift_target.name})"
        return f"PlayCardAction(card={self.card.name})"

class QuestAction(Action):
    def __init__(self, character: 'Card', support_target: Optional['Card'] = None):
        super().__init__()
        self.character = character
        self.support_target = support_target

    def execute(self, game: 'GameState', player: 'Player'):
        player.quest(self.character, game.turn_number, self.support_target)

    def __repr__(self):
        return f"QuestAction(character={self.character.name})"

class ChallengeAction(Action):
    def __init__(self, attacker: 'Card', defender: 'Card'):
        super().__init__()
        self.attacker = attacker
        self.defender = defender

    def execute(self, game: 'GameState', player: 'Player'):
        game.challenge(self.attacker, self.defender)

    def __repr__(self):
        return f"ChallengeAction(attacker={self.attacker.name}, defender={self.defender.name})"

class SingAction(Action):
    def __init__(self, song_card: 'Card', singer: 'Card'):
        super().__init__()
        self.song_card = song_card
        self.singer = singer

    def execute(self, game: 'GameState', player: 'Player'):
        player.sing_song(self.song_card, self.singer, game.turn_number)

    def __repr__(self):
        return f"SingAction(song={self.song_card.name}, singer={self.singer.name})"

class ActivateAbilityAction(Action):
    def __init__(self, card: 'Card', ability_index: int):
        super().__init__()
        self.card = card
        self.ability_index = ability_index

    def execute(self, game: 'GameState', player: 'Player'):
        player.activate_ability(self.card, self.ability_index, game.turn_number)

    def __repr__(self):
        return f"ActivateAbilityAction(card={self.card.name}, ability_index={self.ability_index})"

# --- Heuristics and Evaluation ---

def evaluate_actions(actions: List[Action], game: 'GameState', player: 'Player'):
    """
    Scores each possible action based on a comprehensive set of heuristics.
    This is the core 'brain' of the AI.
    """
    # First, get the baseline board evaluation to compare against
    baseline_score = evaluate_board_state(game, player.player_id)
    
    # Use lookahead analysis for initial scoring
    scored_actions = perform_lookahead_analysis(game, player, actions)
    
    # Update the action scores
    for action, score in scored_actions:
        action.score = score
    
    # Add more detailed heuristics for each action type
    for action in actions:
        if isinstance(action, QuestAction):
            # Base score is the lore gained
            score = action.character.lore or 0
            if action.character.has_keyword('Support'):
                # Bonus for using support
                score += 1.5

            # Risk assessment: check if questing makes the character vulnerable to banishment
            opponent = game.get_opponent(player.player_id)
            character_at_risk = action.character
            for opponent_char in opponent.play_area:
                if (opponent_char.card_type == 'Character' and 
                    not opponent_char.is_exerted and 
                    opponent_char.strength >= character_at_risk.willpower):
                    # Character could be banished by a challenge; major penalty
                    score -= 3
                    break
            
            # Higher bonus for questing when close to winning
            if player.lore + score >= 20:  # Would win the game
                score += 10
            elif player.lore >= 15:  # Close to winning
                score += 3
            
            action.score = score

        elif isinstance(action, PlayCardAction):
            # Base score uses a formula: Value = (Card power / Cost) * scaling factor
            # For characters, power = strength + willpower + lore
            card = action.card
            cost = card.cost or 1  # Avoid division by zero
            score = 0

            if card.card_type == 'Character':
                # Character value calculation
                power = (card.strength or 0) + (card.willpower or 0) + (card.lore or 0)
                score = (power / cost) * 2.5

                # Bonus for good keywords
                if card.has_keyword('Evasive'):
                    score += 1.5
                if card.has_keyword('Ward'):
                    score += 2.0
                if card.has_keyword('Resist'):
                    score += 1.5
                if card.has_keyword('Challenger'):
                    score += 1.0
                if card.has_keyword('Rush'):
                    score += 1.2

                # Penalty for Reckless (forces bad attacks)
                if card.has_keyword('Reckless'):
                    score -= 1.0

                # Shift bonus if there's a valid target
                if card.has_keyword('Shift') and action.shift_target:
                    score += 3.0
                    
                # Singer bonus for song synergy
                if card.has_keyword('Singer'):
                    # Count songs in hand that this character could sing
                    singer_value = card.get_keyword_value('Singer') or 0
                    eligible_songs = sum(1 for c in player.hand 
                                        if c.card_type == 'Action' and 
                                        hasattr(c, 'song') and c.song and 
                                        c.cost <= singer_value)
                    score += eligible_songs * 0.8

            elif card.card_type == 'Item':
                # Value for items based on their utility
                score = 3.5
                
                # Check for synergy with board
                if "gain +1 strength" in str(card.abilities).lower():
                    # More valuable if we have many characters
                    character_count = sum(1 for c in player.play_area if c.card_type == 'Character')
                    score += character_count * 0.3

            elif card.card_type == 'Action':
                # Value for actions
                score = 3.5
                
                # Songs are valued differently
                if hasattr(card, 'song') and card.song:
                    # Check if we have singers to use it
                    singers = [c for c in player.play_area 
                              if c.card_type == 'Character' and 
                              not c.is_exerted and 
                              c.has_keyword('Singer') and
                              c.get_keyword_value('Singer') >= card.cost]
                    if singers:
                        score += 2.0  # Bonus if we can sing it for free
            
            elif card.card_type == 'Location':
                # Locations with lore are very valuable
                if hasattr(card, 'lore') and card.lore > 0:
                    score = card.lore * 3.5
                else:
                    score = 2.5

            # Final adjustment based on cost vs. current turn
            # Prefer playing cheaper cards early, expensive cards later
            turn_factor = min(game.turn_number / 10, 1.0)  # 0.1 to 1.0
            if cost > game.turn_number + 2:
                # Penalty for playing expensive cards too early
                score -= (cost - game.turn_number - 2) * (1 - turn_factor)
            else:
                # Bonus for playing appropriately costed cards
                score += (game.turn_number - cost + 2) * turn_factor * 0.3

            action.score = score

        elif isinstance(action, ChallengeAction):
            attacker = action.attacker
            defender = action.defender
            score = 0

            # Basic damage calculation
            attacker_damage = attacker.strength
            defender_damage = defender.strength

            # Apply any keyword modifiers
            if attacker.has_keyword('Challenger'):
                attacker_damage += 2  # Challenger adds 2 strength in challenges

            if defender.has_keyword('Evasive'):
                defender_damage = 0  # Evasive prevents return damage

            # Core score logic: Does attacker banish defender?
            attacker_banishes_defender = attacker_damage >= defender.willpower

            # Does defender banish attacker?
            defender_banishes_attacker = defender_damage >= attacker.willpower

            # Calculate trade value
            if attacker_banishes_defender:
                # Base score for banishing = defender's total stats
                score += (defender.strength or 0) + (defender.willpower or 0) + (defender.lore or 0) * 1.5

                # Extra value for banishing an unexerted character (tempo gain)
                if not defender.is_exerted:
                    score += 3

            if defender_banishes_attacker:
                # Cost for being banished = attacker's total stats
                score -= (attacker.strength or 0) + (attacker.willpower or 0) + (attacker.lore or 0) * 1.5

            # Evaluate special cases: Don't attack if it's a very bad trade
            if defender_banishes_attacker and not attacker_banishes_defender:
                # Bad trade, major penalty
                score -= 6
                if attacker.lore and attacker.lore > 2:  # Don't sacrifice high-lore characters
                    score -= attacker.lore * 3

            # Reckless characters MUST challenge
            if attacker.has_keyword('Reckless'):
                score += 15  # High bonus to ensure this happens
                
            # Rush characters get bonus for early challenges
            if attacker.has_keyword('Rush') and game.turn_number <= 3:
                score += 2

            action.score = score

        elif isinstance(action, InkAction):
            # Heuristic: The best card to ink is one that is least useful to play.
            card_to_ink = action.card
            
            # Start with a baseline score for inking.
            score = 5 # Inking is generally a good setup action.

            # Calculate the card's value as if we were to play it.
            play_score = 0
            if card_to_ink.card_type == 'Location':
                play_score = ((card_to_ink.lore or 0) * 5) + (card_to_ink.willpower or 0) - card_to_ink.cost
            else:
                play_score = (card_to_ink.strength or 0) + (card_to_ink.willpower or 0) + (card_to_ink.lore or 0) - card_to_ink.cost

            # Penalize inking more valuable cards.
            score -= play_score

            # Bonus for inking a card that is currently unplayable anyway.
            if card_to_ink.cost > player.get_available_ink():
                score += 3

            # Penalty for inking a card we could play this turn.
            if card_to_ink.cost <= player.get_available_ink():
                score -= 5

            action.score = score

        elif isinstance(action, SingAction):
            # Singing a song is good tempo. Score it higher than just playing the card.
            # The value is the effect of the song, plus the ink saved.
            song_card = action.song_card
            play_action = PlayCardAction(song_card)
            # Create a temporary list for the recursive call
            temp_actions = [play_action]
            evaluate_actions(temp_actions, game, player) # Recursively score the play action
            action.score = temp_actions[0].score + song_card.cost

        elif isinstance(action, ActivateAbilityAction):
            ability = action.card.abilities[action.ability_index]
            # Heuristic: score based on the effect.
            # This is a simplified placeholder. A real AI would have complex scoring.
            
            # Handle both dictionary-style abilities and object abilities
            if isinstance(ability, dict):
                effect = ability.get('effect')
            elif hasattr(ability, 'effect'):
                effect = ability.effect
            else:
                effect = None
                
            if effect == 'DrawCard':
                action.score = 25 # Drawing is very good
            else:
                action.score = 5 # Generic positive score for doing something

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
            if isinstance(ability, dict):
                # Handle abilities as dictionaries
                if ability.get('trigger') == "Activated":
                    actions.append(ActivateAbilityAction(char, i))
            elif hasattr(ability, 'trigger'):
                # Handle abilities as objects with attributes (backward compatibility)
                if ability.trigger == "Activated":
                    actions.append(ActivateAbilityAction(char, i))

        # Sing Actions
        if char.has_keyword('Singer'):
            singable_songs = [c for c in player.hand if c.card_type == 'Song']
            for song in singable_songs:
                # Check if the singer can sing this song for free
                if char.get_keyword_value('Singer') >= song.cost:
                    actions.append(SingAction(song, char))

    # 4. Item actions (Abilities)
    ready_items = [c for c in player.play_area if c.card_type == 'Item' and not c.is_exerted]
    for item in ready_items:
        for i, ability in enumerate(item.abilities):
            if isinstance(ability, dict):
                # Handle abilities as dictionaries
                if ability.get('trigger') == "Activated":
                    actions.append(ActivateAbilityAction(item, i))
            elif hasattr(ability, 'trigger'):
                # Handle abilities as objects with attributes (backward compatibility)
                if ability.trigger == "Activated":
                    actions.append(ActivateAbilityAction(item, i))

    return actions

MAX_ACTIONS_PER_TURN = 30  # Safety break to prevent infinite loops in AI

def run_main_phase(game: 'GameState', player: 'Player'):
    """
    Runs the main phase for a player using a flexible, heuristic-driven loop.
    The AI will continuously evaluate all possible actions and choose the best one
    until it decides to pass the turn.
    """
    has_inked_this_turn = False
    executed_actions_this_turn = set()  # Track actions to prevent loops
    actions_taken_count = 0

    while actions_taken_count < MAX_ACTIONS_PER_TURN:
        print(f"DEBUG: Turn {game.turn_number}, Player {player.player_id} - Before get_possible_actions")
        possible_actions = get_possible_actions(game, player, has_inked_this_turn)
        print(f"DEBUG: Turn {game.turn_number}, Player {player.player_id} - After get_possible_actions")
        
        # Print all possible actions for debugging
        print(f"DEBUG: All possible actions: {[repr(a) for a in possible_actions]}")
        
        # Filter out actions that have already been taken this turn to prevent infinite loops
        possible_actions = [action for action in possible_actions if repr(action) not in executed_actions_this_turn]
        
        if not possible_actions:
            print("DEBUG: No more possible actions, breaking")
            break  # No more actions to take

        # Use advanced heuristics for action evaluation
        evaluate_actions(possible_actions, game, player)

        # Print scores for debugging
        for action in possible_actions:
            print(f"DEBUG: Action {repr(action)} has score {action.score}")
            
        possible_actions.sort(key=lambda a: a.score, reverse=True)
        best_action = possible_actions[0]
        print(f"DEBUG: Selected best action: {repr(best_action)} with score {best_action.score}")

        # Check if the best action is a challenge with a reckless character
        is_reckless_challenge = isinstance(best_action, ChallengeAction) and best_action.attacker.has_keyword('Reckless')
        
        # If the best available action has a negative or zero score, the AI decides to stop.
        # Exceptions: 
        # 1. Inking is a low-score setup move we should do if available
        # 2. Reckless characters must challenge regardless of score
        # 3. First action of the turn - always do at least one thing if possible
        if best_action.score <= 0 and not (isinstance(best_action, InkAction) or is_reckless_challenge):
            # If we haven't done anything yet this turn, do at least one action even if it has a negative score
            if actions_taken_count == 0:
                print(f"DEBUG: Taking one action despite negative score: {repr(best_action)} with score {best_action.score}")
            else:
                print(f"DEBUG: Stopping because best action {repr(best_action)} has non-positive score {best_action.score}")
                break

        # Execute the best action
        best_action.execute(game, player)
        executed_actions_this_turn.add(repr(best_action))  # Record the action
        actions_taken_count += 1

        if isinstance(best_action, InkAction):
            has_inked_this_turn = True
