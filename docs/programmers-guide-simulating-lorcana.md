---
tags:
  - "#Lorcana"
  - "#AI"
  - "#Simulation"
  - "#Rules"
  - "#DisneyLorcana"
  - "#Programming"
  - "#Coding"
---
# The Definitive Programmer's Guide to Simulating High-Level Disney Lorcana

This document provides a complete and comprehensive overview of the rules, mechanics, keywords, and strategic logic of Disney Lorcana. It is structured from the ground up to serve as a definitive blueprint for a programmer creating an AI capable of high-level, competitive play.

## 1. Core Rules Engine & Game State

This section details the foundational rules that govern the game state, deck construction, and the fundamental objects the AI will interact with.

### 1.1. The Primary Objective
* **Goal:** The primary objective is to be the first player to accumulate **20 or more lore**. Victory is declared the moment a player reaches or exceeds 20 lore.
* **Loss Condition:** A player who is required to draw a card but has no cards left in their deck immediately loses the game.

### 1.2. Deck Construction Rules
An AI's understanding of the game must be grounded in the rules of deck creation, which dictate the available resources and probabilities.
* **Deck Size:** A deck must contain **exactly 60 cards**.
* **Ink Colors:** A deck may contain cards from no more than **two (2) ink colors** (e.g., a deck can be Amber and Amethyst, but not Amber, Amethyst, and Emerald).
* **Card Uniqueness:** A deck may contain a maximum of **four (4) copies** of any single card, identified by its full name and subtitle (e.g., "Elsa - Snow Queen"). Most competitive decks will have almost all their cards as 4 copies per card, to maximize consistency.

### 1.3. Card Types & Their Functions
The AI must be able to parse and differentiate four distinct card types.

* **Character:** The primary agents in the game. Characters are played to the board and are defined by:
    * **Cost:** The ink required to play them.
    * **Strength (S):** The amount of damage they deal in challenges.
    * **Willpower (W):** The amount of damage they can sustain before being banished.
    * **Lore Value (L):** The number of lore points gained when they quest.
    * **Abilities/Keywords:** Special rules printed in their text box.
    * **Classifications**: Some classifications can have effects on the game or on other cards, usually based on abilities. Classifications include things like, e.g., "Pirate," "Hero," or "Ally". All characters have at least some of these classifications.

* **Action:** These cards represent one-time effects. When an Action card is played, its instructions are followed, and then the card is immediately placed into the discard pile.
    * **Song Cards:** A special sub-type of Action. A player has two options for playing a Song:
        1.  **Pay the Cost:** Pay the Song's ink cost from their inkwell.
        2.  **Sing the Song:** A player with a character that has been in play since the start of their turn (its "ink is dry") may exert that character to play the Song for free, provided the character's ink cost is equal to or greater than the Song's ink cost. This is a critical tempo mechanic.

* **Item:** Items are played to the board and provide ongoing effects or abilities that can be activated. They are not characters and cannot quest or challenge unless an effect specifically allows it. They remain in play until banished by a card effect. Items do not need to wait for their ink to dry in order to become exerted for abilities.

* **Location:** Locations are played to the board and represent places characters can visit. They have unique rules:
    * **Mechanics:** They have an ink cost to be played, a move cost for characters to move to them, a Willpower value, and sometimes a lore value.
    * **Passive Lore:** At the start of their controller's turn, if a Location has a lore value, its controller gains that much lore automatically.
    * **Challenging:** Locations can be challenged by an opponent's characters. The challenger deals damage equal to its Strength, but the Location (having no Strength) deals no damage back. They do not need to be exerted to be challenged. If damage matches or exceeds the location's willpower, it is banished.

### 1.4. Game Zones
The AI must track the state of cards across several distinct game zones:
* **Deck:** The ordered, face-down library of 60 cards.
* **Hand:** The hidden set of cards held by a player.
* **Play Area:** The public area where Character, Item, and Location cards reside.
* **Inkwell:** A player's face-down resource cards.
* **Discard Pile:** An unordered, public, face-up collection of used or banished cards.
* **The Bag:** A temporary "location" for resolving all actions and abilities. All abilities that trigger at the exact same time go into this "Bag." Then, the active player resolves their abilities in any order they choose (the order that most benefits their game state). Then, the non-active player does the same. Original abilities and effects always fully resolve before new abilities that were triggered as a result of those abilities/effects begin to resolve from the Bag. The Bag only applies to effects that were triggered simultaneously by some action or condition.

### 1.5. The Inkwell & Resource System
The resource system is foundational to every decision.
1.  **Inkable Cards:** Many cards feature a gold swirl around their hexagonal cost symbol. Only these cards are "inkable." "Uninkable" cards normally cannot be added to the inkwell, except when card abilities override this (e.g., Fishbone Quill allows you to exert the item itself in order to, "Add **any** card from your hand to your inkwell." which allows you to ink an uninkable card--and an extra card for that turn).
2.  **Adding to Inkwell:** **Once per turn**, during their Main Phase, a player may choose one inkable card from their hand, show it to their opponent, and place it face-down into their inkwell. This can only happen once per turn, unless an ability says otherwise.
3.  **Generating Ink:** Each card in the inkwell can be exerted ("tapped") to produce one ink. To pay a cost of 3, a player exerts 3 cards in their inkwell.
4.  **Permanence:** Once a card is in the inkwell, it remains there for the rest of the game and cannot be used for its printed text.

### 1.6. The Mulligan Phase
At the start of the game, after drawing an initial hand of seven cards, each player may perform a one-time mulligan.
1.  A player can select any number of cards from their hand to put aside.
2.  They then draw that many new cards from the top of their deck.
3.  The set-aside cards are then shuffled back into the deck.
4.  The AI must use this opportunity to improve its starting hand, typically by getting rid of unplayable high-cost cards, or uninkable cards, in favor of low-cost cards it can play or add to its inkwell.

### 1.7. Step-by-Step Turn Structure
A turn is composed of two main phases with strict steps.

**1. Beginning Phase (Ready, Set, Draw):**
* **Ready:** All exerted cards controlled by the player (Characters, Items, and ink in their inkwell) are returned to a ready (upright) state.
* **Set:** Any abilities that trigger "at the start of your turn" are resolved. This is also when players gain lore from any Location cards they control.
* **Draw:** The current player draws one card from the top of their deck. The player who goes first **skips this step** on their first turn of the game.

**2. Main Phase:**
During this phase, the active player may take any of the following actions in any order, as many times as they are able and wish to, with the exception of inking a card.
* **Play a Card:** Pay the ink cost to play a Character, Item, Action, or Location from hand.
* **Add a Card to the Inkwell:** This may only be done **once per turn**.
* **Quest:** Exert a ready Character whose ink is dry (i.e., it has been in play since the start of the current turn) to gain lore equal to that character's lore value.
* **Challenge:** Exert a ready Character whose ink is dry to challenge an opponent's exerted Character or any of their Locations.
* **Move a Character:** Pay a Location's move cost to move one of your characters to that location.
* **Activate an Ability:** Use an ability on a Character or Item in play, paying any associated costs (ink, exerting, etc.).

## 3. A Grammar of Lorcana Effects (Effect Primitives)

To enable an AI to play *any* card, its text must be deconstructed into fundamental, programmable actions, or "primitives." This allows the AI to understand cards it has never seen before by parsing their grammar.

### 3.1. Targeting Primitives (`Choose a...`)
This defines how the AI selects targets for effects.
* **`Choose a/an...`**: The AI must select one valid target from the game state that matches the description.
* **`Your/Opponent's...`**: A constraint that limits the pool of valid targets to one player's side of the board.
* **`Chosen...`**: A reference that refers back to the target that was selected. Sometimes it simply implies that a target should be selected first, then something is applied to the chosen character.
* **Constraints on Targeting:** The AI's targeting logic must be filtered by game rules and keywords:
    * **`Ward`:** A character with Ward is an invalid target for any opponent's effect that uses the `Choose` or `Chosen` primitive.
    * **`Bodyguard`:** If an opponent has an exerted Bodyguard character in play, it is an invalid move to Challenge any non-Bodyguard characters until the Bodyguard character is banished or otherwise removed.

### 3.2. Action Primitives (The "Verbs" of Lorcana)
These are the fundamental actions an effect can cause.
* **`Banish`**: Move the target card from the Play Area to its owner's Discard Pile.
* **`Return to Hand (Bounce)`**: Move the target card from the Play Area to its owner's Hand.
* **`Draw X card(s)`**: Take the top X cards from the player's Deck and add them to their Hand.
* **`Discard X card(s)`**: The target player chooses X cards from their Hand and moves them to their Discard Pile. The effect specifies if the choice is the player's or random.
* **`Exert`**: Change a card's state from Ready to Exerted.
* **`Ready`**: Change a card's state from Exerted to Ready.
* **`Deal X damage to...`**: Place X damage counters on the target. The AI must immediately check if the target's total damage is now equal to or greater than its Willpower, and if so, move it to the Discard Pile.
* **`Gain X Lore` / `Lose X Lore`**: Directly modify a player's lore total.
* **`Look at...`**: Reveal a hidden zone (opponent's hand, top cards of deck) to the AI. The AI must log this information for future decisions.
* **`Search / Tutor`**: Look through a zone (usually the Deck) for a card that meets specific criteria and perform an action with it (put in hand, put into play, etc.).

### 3.3. Modification Primitives (Stat & Keyword Modifiers)
These effects alter the state of cards, and the AI must track their values and durations.
* **Stat Modification**: E.g., `...gains +X Strength`, `...gets -X Willpower`. These must be applied before calculating challenge outcomes.
* **Keyword Granting**: E.g., `...gains Evasive`. The AI must temporarily grant the keyword and its associated rules to the target card.
* **Cost Alteration**: E.g., `The next action you play costs 1 less.` The AI must apply this floating discount to the next valid action it takes.
* **Duration**: The AI must parse and track the duration of the effect: `until the end of the turn`, `on your next turn`, or a persistent static ability (`while this item is in play`).

### 3.4. Trigger Primitives (The "Whens" and "Ifs")
These define the conditions that cause an ability to be placed on The Bag.
* **`On Play / Enters Play`**: Triggers when the card is successfully played from hand. `Shift`ing a character onto another *does* count as playing it and triggers these effects.
* **`Leaves Play / On Banish`**: Triggers when the card is moved from the Play Area to the Discard Pile or Hand.
* **`When you Quest with...`**: Triggers when the character is exerted specifically for the Quest action.
* **`When this character Challenges...`**: Triggers when the character is exerted to initiate a Challenge.
* **`At the start of your turn` / `At the end of your turn`**: Triggers during the "Set" step or End Phase, respectively.

## 4. Keyword Dictionary & Advanced AI Implications

| Keyword             | Mechanic Description                                                                                                                                                                                                                                                                                                                       | Advanced Strategic Implication for AI                                                                                                                                                                                                                                                                                                                                                                                                                      |
| :------------------ | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Bodyguard**       | An opposing player cannot challenge any of your other characters if you have an exerted Character with Bodyguard in play. This protection does not extend to your Locations. Also, a player can choose to have Bodyguard characters can enter play exerted, so their protection is immediate (but so is their vulnerability to challenge). | **Forced Interaction Protocol:** The AI must treat ready Bodyguard characters as a hard "taunt" that overrides its optimal challenge selection. It must weigh the cost of removing the exerted Bodyguard against the value of the protected targets. This keyword often signals a "protect the queen" strategy from the opponent.                                                                                                                          |
| **Challenger +X**   | This character gets +X Strength only on the controlling player's turn and only when it is challenging.                                                                                                                                                                                                                                     | **Asymmetric Threat Assessment:** The AI must assign two threat values for this character: a lower defensive value and a higher offensive value. This is critical for calculating if it should attack into a Challenger or leave its own characters exerted and vulnerable.                                                                                                                                                                                |
| **Evasive**         | Only characters with Evasive can challenge this character.                                                                                                                                                                                                                                                                                 | **Sub-Game of Lore vs. Removal:** The AI must recognize that Evasive characters create a separate "game on the board." It needs to assess if it can win this parallel lore race or if it must expend premium, non-challenge removal (using `Banish` or `Deal Damage` Action primitives) to handle them. Of course, it is also possible to use one's own evasive characters to challenge opposing ones, if that is advantageous given the game/board state. |
| **Reckless**        | This character cannot quest and must challenge if able during the controlling player's turn. Reckless characters can still be exerted to sing songs to essentially "bypass" this challenge requirement, if advantageous.                                                                                                                   | **Forced Aggression/Board Control Tool:** The AI must understand that Reckless characters are pure board control tools that cannot advance the primary win condition directly. The AI should play them when behind on board or to maintain pressure. It's a high-risk keyword; if the opponent has no exerted characters, a Reckless character is a dead card on the board for that turn.                                                                  |
| **Resist +X**       | Reduce all damage dealt to this character by X. This applies to challenge damage and effect damage.                                                                                                                                                                                                                                        | **Durability/Value Trading:** Resist makes a character significantly harder to remove. The AI's damage calculation for challenges *must* subtract X from incoming damage. A character with Resist can often absorb a challenge from a stronger character and survive, creating a value trade.                                                                                                                                                              |
| **Rush**            | This character can challenge the turn they are played (their "ink is not yet dry"). They still cannot quest or use other exert abilities on that turn.                                                                                                                                                                                     | **Tempo & Initiative:** Rush allows the AI to immediately answer threats and reclaim **initiative**. A key heuristic: The value of a Rush character increases proportionally to the value of the opponent's exerted characters. It is the primary tool for punishing an opponent's questing.                                                                                                                                                               |
| **Shift X**         | You may pay X ink to play this card on top of one of your characters with the same name. The new character inherits damage, "dry ink," and other "states" of the character underneath.                                                                                                                                                     | **Resource & Action Compression:** Shift is a high-skill mechanic. The AI must constantly scan its hand and board for shift targets. It represents: 1. **Mana Cheating.** 2. **Action Compression** (play + challenge/quest in one). 4. **Surprise Factor** (suddenly, a 2-cost character may be a 5 or 6-cost character with the ability to sing 5 or 6-cost songs immediately (if the underlying character was already "dry"))                           |
| **Singer X**        | This character counts as costing X ink *only* for the purpose of meeting the requirement to sing a Song card for free by exerting.                                                                                                                                                                                                         | **Tempo Engine Identification:** The AI must flag characters with high Singer values as top-priority targets for both protection (if its own) and removal (if the opponent's). It enables turns where a player can expend all their ink on a character and still play a powerful Action, a massive tempo swing.                                                                                                                                            |
| **Support**         | Whenever this character quests, you may add their Strength to another chosen character's Strength until the end of the turn.                                                                                                                                                                                                               | **Challenge Enhancement/Strategic Sequencing:** The AI's action sequencing is critical here. It must always process a Quest action with a Support character *before* initiating a Challenge action with another character to get the bonus. This allows smaller characters to trade up.                                                                                                                                                                    |
| **Ward**            | Opponents can't choose this character with actions or abilities. This character can still be challenged.                                                                                                                                                                                                                                   | **Forced Combat Protocol:** The AI's targeting system must mark warded characters as invalid for any effect using the `Choose` primitive from an opponent. This forces the AI to rely on combat math or non-targeting board wipes, making these characters very resilient.                                                                                                                                                                                 |
| **Sing Together X** | Any number of your characters whose ink is dry may exert to sing this song for free, provided their total cost is X or more.                                                                                                                                                                                                               | **Swarm Synergy/Go-Wide Payoff:** This is a variant of the Sing mechanic that rewards having many characters in play. The AI needs to be able to sum the costs of its available ready characters to see if it can play a Sing Together song. This makes low-cost "go-wide" strategies viable for casting powerful, expensive songs.                                                                                                                        |
| **Vanish**          | If an opponent chooses a character with Vanish for an action, the character with Vanish is banished (unless the effect of the action removed them from play before the game state check--e.g., the action returned them to their player's hand)                                                                                            | **Over-Statted Cards, but easier to remove**. Vanish characters are designed to be overpowered for their cost, but they are also thus easier to remove with actions.                                                                                                                                                                                                                                                                                       |


## 5. AI Strategic Heuristics & Decision-Making

With the rules and grammar defined, the AI needs a "brain" to make skillful decisions.

### 5.1. The Inkwell Choice Heuristic
The AI needs a function to decide which card to place in its inkwell each turn. This function should weigh several factors to return the "most inkable" card:
* **High-Cost "Bricks":** Is the card's cost > (current turn number + 3)? If so, it's a high-priority ink target as it's unplayable soon.
* **Redundancy:** Is this the 3rd or 4th copy of a card in hand or play? Redundant copies are good ink targets.
* **Situational Usefulness:** Is this a tech card (e.g., item removal) when the opponent has no items? It has low current utility. Good ink target.
* **Core Win Condition:** Is this a key Shift card or a powerful late-game bomb of which you have limited copies in deck? (Lowest ink priority). The AI should almost never ink these cards unless its survival depends on playing another card that turn.

### 5.2. Board State Evaluation Function
At any point, the AI should be able to run a function `evaluate(board_state)` that returns a numerical score representing its position. This score is a composite of:
* **Lore Delta:** `(My Lore - Opponent's Lore) * Lore_Weight`. This is the most important factor, with a high weight.
* **Potential Lore:** `(Sum of lore from my ready characters + passive lore from my locations) - (Sum of lore from opponent's ready characters + passive lore from their locations)`. This predicts the next turn's lore swing.
* **Board Presence:** A weighted sum of the stats and keywords of all characters in play. A simplified version: `Sum((Strength + Willpower) * Keyword_Multiplier)`. Keywords like Evasive, Ward, and Resist should have a multiplier > 1.
* **Card Advantage:** `(My Cards in Hand - Opponent's Cards in Hand) * Card_Advantage_Weight`.
* **Tempo & Initiative:** A value representing which player is dictating the flow of play. Can be measured by comparing ready vs. exerted characters and available ink.

### 5.3. Play-line Analysis (Lookahead)
A strong AI doesn't just choose the single best play for the *current* state. It must perform a limited lookahead to anticipate counter-play.
1.  **Generate Legal Moves:** The AI generates a tree of all possible legal moves (play card X, quest with Y, challenge Z with A, etc.).
2.  **Evaluate Outcomes:** For each leaf of the move tree, run the `evaluate()` function on the resulting board state.
3.  **Simulate Opponent's Response:** For the top-scoring moves, the AI should then simulate the opponent's most likely response (e.g., they will use their Rush character to challenge the character I just quested with).
4.  **Re-evaluate:** The AI re-runs the `evaluate()` function on the board state *after* the opponent's likely response.
5.  **Select Optimal Line:** The AI chooses the play-line that results in the highest evaluation score after this sequence of play and anticipated counter-play, balancing immediate gain with future risk.