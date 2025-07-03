# Project Oracle: Ability Schema Definition

## 1. Introduction

This document defines the normalized, canonical schema for all card abilities in the Project Oracle game engine. The `ability_parser.py` module produces a structured representation of raw ability strings. This schema represents the final transformation of that data into a format that the `EffectResolver` can directly consume to modify the `GameState`.

The core design principle is to create a clear, unambiguous, and extensible instruction set for the game engine.

## 2. Schema Design

Each ability will be represented as a JSON object containing an `effect` type and its associated parameters.

### 2.1. Effect Type: `ADD_KEYWORD`

This is the most common effect type, used for granting a character a standard keyword ability.

- **Description:** Adds a keyword to a card. Some keywords have an associated value.
- **Parameters:**
    - `keyword` (string): The name of the keyword in uppercase (e.g., `"EVASIVE"`, `"BODYGUARD"`, `"RESIST"`).
    - `value` (integer, optional): The numeric value associated with the keyword (e.g., for `Resist +2`, the value is `2`).

- **Examples:**
    - **Evasive:** `{ "effect": "ADD_KEYWORD", "keyword": "EVASIVE" }`
    - **Support:** `{ "effect": "ADD_KEYWORD", "keyword": "SUPPORT" }`
    - **Resist +2:** `{ "effect": "ADD_KEYWORD", "keyword": "RESIST", "value": 2 }`
    - **Challenger +3:** `{ "effect": "ADD_KEYWORD", "keyword": "CHALLENGER", "value": 3 }`

### 2.2. Effect Type: `SET_SHIFT_COST`

This effect is used for all `Shift` abilities, including compound variations.

- **Description:** Defines the ink cost required to play a character using its Shift ability.
- **Parameters:**
    - `value` (integer): The ink cost for the shift.

- **Examples:**
    - **Shift 5:** `{ "effect": "SET_SHIFT_COST", "value": 5 }`
    - **Puppy Shift 3:** `{ "effect": "SET_SHIFT_COST", "value": 3 }`
    - **Universal Shift 4:** `{ "effect": "SET_SHIFT_COST", "value": 4 }`

### 2.3. Effect Type: `SINGER`

This effect is a special case of cost reduction, specifically for singing songs.

- **Description:** Allows a character to sing songs of a certain cost or less as if they had that much ink.
- **Parameters:**
    - `value` (integer): The maximum cost of a song the character can sing.

- **Example:**
    - **Singer 4:** `{ "effect": "SINGER", "value": 4 }`

## 3. Extensibility

This schema is designed to be extensible. As we begin to parse more complex, natural language abilities (e.g., "When you play this character, draw a card"), we will introduce new effect types, such as:

- `DRAW_CARDS`
- `DEAL_DAMAGE`
- `MODIFY_ATTRIBUTE` (for changing Strength or Willpower)
- `HEAL_DAMAGE`

Each new effect will have a clearly defined set of parameters, ensuring the `EffectResolver` remains robust and maintainable.
