import unittest
from src.abilities.create_abilities_database import parse_ability_text, ParsedAbility

class TestAbilityParser(unittest.TestCase):

    def test_parse_simple_keyword(self):
        """Tests parsing of a simple, valueless keyword."""
        text = "Rush"
        abilities = parse_ability_text(text)
        self.assertEqual(len(abilities), 1)
        self.assertEqual(abilities[0].effect, "GainKeyword")
        self.assertEqual(abilities[0].value['keyword'], "Rush")
        self.assertTrue(abilities[0].value['amount'])
        self.assertIsNone(abilities[0].condition)
        self.assertIsNone(abilities[0].duration)

    def test_parse_keyword_with_value(self):
        """Tests parsing of a keyword with a numeric value."""
        text = "Challenger +3"
        abilities = parse_ability_text(text)
        self.assertEqual(len(abilities), 1)
        self.assertEqual(abilities[0].effect, "GainKeyword")
        self.assertEqual(abilities[0].value['keyword'], "Challenger")
        self.assertEqual(abilities[0].value['amount'], 3)
        self.assertIsNone(abilities[0].condition)
        self.assertIsNone(abilities[0].duration)

    def test_parse_activated_ability(self):
        """Tests a simple activated ability."""
        text = "{EXERT} - Draw a card."
        abilities = parse_ability_text(text)
        self.assertEqual(len(abilities), 1)
        self.assertEqual(abilities[0].trigger['type'], "Activated")
        self.assertEqual(abilities[0].effect, "DrawCard")
        self.assertEqual(abilities[0].value, 1)
        self.assertIsNone(abilities[0].condition)
        self.assertIsNone(abilities[0].duration)

    def test_parse_on_play_trigger(self):
        """Tests a simple 'OnPlay' triggered ability."""
        text = "When you play this character, you may draw a card."
        abilities = parse_ability_text(text)
        self.assertEqual(len(abilities), 1)
        self.assertEqual(abilities[0].trigger['type'], "OnPlay")
        self.assertEqual(abilities[0].effect, "DrawCard")
        self.assertEqual(abilities[0].target, "Player")
        self.assertEqual(abilities[0].value, 1)
        self.assertIsNone(abilities[0].condition)
        self.assertIsNone(abilities[0].duration)

    def test_parse_on_quest_trigger_with_damage(self):
        """Tests a 'OnQuest' trigger with a damage effect."""
        text = "Whenever this character quests, you may deal 1 damage to chosen character."
        abilities = parse_ability_text(text)
        self.assertEqual(len(abilities), 1)
        self.assertEqual(abilities[0].trigger['type'], "OnQuest")
        self.assertEqual(abilities[0].effect, "DealDamage")
        self.assertEqual(abilities[0].target, "ChosenCharacter")
        self.assertEqual(abilities[0].value, 1)
        self.assertIsNone(abilities[0].condition)
        self.assertIsNone(abilities[0].duration)

    def test_parse_multiple_abilities(self):
        """Tests parsing of a card with multiple distinct abilities."""
        text = "Rush. When you play this character, gain 2 lore."
        abilities = parse_ability_text(text)
        self.assertEqual(len(abilities), 2)

        # Check for Rush keyword
        rush_ability = next((a for a in abilities if a.effect == "GainKeyword"), None)
        self.assertIsNotNone(rush_ability)
        self.assertEqual(rush_ability.value['keyword'], "Rush")
        self.assertIsNone(rush_ability.condition)
        self.assertIsNone(rush_ability.duration)

        # Check for OnPlay ability
        on_play_ability = next((a for a in abilities if a.trigger['type'] == "OnPlay"), None)
        self.assertIsNotNone(on_play_ability)
        self.assertEqual(on_play_ability.effect, "GainLore")
        self.assertEqual(on_play_ability.value, 2)
        self.assertIsNone(on_play_ability.condition)
        self.assertIsNone(on_play_ability.duration)

    def test_parse_complex_trigger_with_subject(self):
        """Tests a trigger that has a specific subject, like 'one of your other characters'."""
        text = "Whenever one of your other characters is challenged and banished, you may draw a card."
        abilities = parse_ability_text(text)
        self.assertEqual(len(abilities), 1)
        ability = abilities[0]
        self.assertEqual(ability.trigger['type'], 'OnBanish')
        self.assertEqual(ability.trigger.get('subject'), 'OtherCharacters')
        self.assertEqual(ability.trigger.get('context'), 'OnChallenge')
        self.assertEqual(ability.effect, 'DrawCard')
        self.assertEqual(ability.target, 'Player')
        self.assertEqual(ability.value, 1)
        self.assertIsNone(ability.condition)
        self.assertIsNone(ability.duration)

    def test_parse_named_ability_with_status_effect(self):
        """Tests a named ability that grants a permanent status."""
        text = "HIDDEN AWAY: This character can't be challenged."
        abilities = parse_ability_text(text)
        self.assertEqual(len(abilities), 1)
        ability = abilities[0]
        self.assertEqual(ability.trigger['type'], 'Passive')
        self.assertEqual(ability.effect, 'GrantStatus')
        self.assertEqual(ability.value, 'CannotBeChallenged')
        self.assertEqual(ability.target, 'Self')
        self.assertIsNone(ability.condition)
        self.assertIsNone(ability.duration)

    def test_parse_complex_named_ability_with_subtype_trigger(self):
        """Tests a named ability with a trigger that specifies a character subtype."""
        text = "SWEET REVENGE: Whenever one of your other Racer characters is banished, each opponent chooses and banishes one of their characters."
        abilities = parse_ability_text(text)
        self.assertEqual(len(abilities), 1)
        ability = abilities[0]
        self.assertEqual(ability.trigger['type'], 'OnBanish')
        self.assertEqual(ability.trigger.get('subject'), 'OtherCharacters')
        self.assertEqual(ability.trigger.get('subtype'), 'Racer')
        self.assertEqual(ability.effect, 'OpponentChoosesAndBanishes')
        self.assertEqual(ability.target, 'OpponentCharacter')
        self.assertEqual(ability.value, 1)
        self.assertIsNone(ability.condition)
        self.assertIsNone(ability.duration)

    def test_no_abilities(self):
        """Tests that text with no abilities returns an empty list."""
        text = "Just a regular character with no special text."
        abilities = parse_ability_text(text)
        self.assertEqual(len(abilities), 0)

    def test_text_with_only_keyword(self):
        """Tests text that contains only a single keyword."""
        text = "Evasive"
        abilities = parse_ability_text(text)
        self.assertEqual(len(abilities), 1)
        self.assertEqual(abilities[0].value['keyword'], "Evasive")
        self.assertIsNone(abilities[0].condition)
        self.assertIsNone(abilities[0].duration)

    def test_parse_on_banish_remove_damage(self):
        """Tests an 'OnBanish' trigger with a 'RemoveDamage' effect."""
        text = "When this character is banished, you may remove up to 2 damage from chosen character."
        abilities = parse_ability_text(text)
        self.assertEqual(len(abilities), 1)
        ability = abilities[0]
        self.assertEqual(ability.trigger['type'], "OnBanish")
        self.assertEqual(ability.effect, "RemoveDamage")
        self.assertEqual(ability.target, "ChosenCharacter")
        self.assertEqual(ability.value, 2)
        self.assertIsNone(ability.condition)
        self.assertIsNone(ability.duration)

    def test_parse_quest_remove_damage_from_type(self):
        """Tests an OnQuest trigger removing damage from a specific character type."""
        text = "Whenever this character quests, you may remove up to 1 damage from each of your Puppy characters."
        abilities = parse_ability_text(text)
        self.assertEqual(len(abilities), 1)
        ability = abilities[0]
        self.assertEqual(ability.trigger['type'], "OnQuest")
        self.assertEqual(ability.effect, "RemoveDamage")
        self.assertEqual(ability.target, "EachPuppyCharacter")
        self.assertEqual(ability.value, 1)
        self.assertIsNone(ability.condition)
        self.assertIsNone(ability.duration)

    def test_parse_conditional_activated_ability(self):
        """Tests an activated ability with a condition."""
        text = "{EXERT} - If you have 3 or more other characters in play, draw a card."
        abilities = parse_ability_text(text)
        self.assertEqual(len(abilities), 1)
        ability = abilities[0]
        self.assertEqual(ability.trigger['type'], "Activated")
        self.assertEqual(ability.effect, "DrawCard")
        self.assertEqual(ability.value, 1)
        self.assertIsNotNone(ability.condition)
        self.assertEqual(ability.condition['type'], 'PlayerHasCharacters')
        self.assertEqual(ability.condition['value'], 3)
        self.assertIsNone(ability.duration)

    def test_parse_conditional_passive_ability(self):
        """Tests a passive ability with a 'while' condition."""
        text = "While you have a character named Dolores Madrigal in play, this character gets +1 {l}."
        abilities = parse_ability_text(text)
        self.assertEqual(len(abilities), 1)
        ability = abilities[0]
        self.assertEqual(ability.trigger['type'], "Passive")
        self.assertEqual(ability.effect, "ModifyLore")
        self.assertEqual(ability.target, "Self")
        self.assertEqual(ability.value, 1)
        self.assertIsNotNone(ability.condition)
        self.assertEqual(ability.condition['type'], 'PlayerHasCharacterNamed')
        self.assertEqual(ability.condition['value'], 'Dolores Madrigal')
        self.assertIsNone(ability.duration)

    def test_parse_trigger_with_temporary_effect(self):
        """Tests a trigger that grants a temporary status effect."""
        text = "I'M TIRED OF PERFECT: Whenever one of your characters sings a song, this character can't be challenged until the start of your next turn."
        abilities = parse_ability_text(text)
        self.assertEqual(len(abilities), 1)
        ability = abilities[0]
        self.assertEqual(ability.trigger['type'], 'OnSingSong')
        self.assertEqual(ability.effect, 'GrantStatus')
        self.assertEqual(ability.value, 'CannotBeChallenged')
        self.assertEqual(ability.target, 'Self')
        self.assertEqual(ability.duration, 'StartOfNextTurn')
        self.assertIsNone(ability.condition)

    def test_parse_multi_effect_ability_with_condition(self):
        """Tests an ability with a trigger, a condition, and multiple effects in one clause."""
        text = "HE NEEDS ME: At the end of your turn, if this character is exerted, you may ready another chosen character of yours and remove all damage from them."
        abilities = parse_ability_text(text)
        self.assertEqual(len(abilities), 2)

        base_trigger = {'type': 'EndOfTurn'}
        base_condition = {'type': 'CharacterIsExerted', 'target': 'Self'}

        # Check for ReadyCharacter effect
        ready_ability = next((a for a in abilities if a.effect == "ReadyCharacter"), None)
        self.assertIsNotNone(ready_ability)
        self.assertEqual(ready_ability.trigger, base_trigger)
        self.assertEqual(ready_ability.condition, base_condition)
        self.assertEqual(ready_ability.target, 'AnotherChosenCharacter')

        # Check for RemoveAllDamage effect
        remove_damage_ability = next((a for a in abilities if a.effect == "RemoveAllDamage"), None)
        self.assertIsNotNone(remove_damage_ability)
        self.assertEqual(remove_damage_ability.trigger, base_trigger)
        self.assertEqual(remove_damage_ability.condition, base_condition)
        self.assertEqual(remove_damage_ability.target, 'AnotherChosenCharacter')

    def test_parse_passive_willpower_buff(self):
        """Tests a passive ability that buffs the Willpower of other characters."""
        text = "Your other characters get +2 {w}."
        abilities = parse_ability_text(text)
        self.assertEqual(len(abilities), 1)
        ability = abilities[0]
        self.assertEqual(ability.trigger['type'], "Passive")
        self.assertEqual(ability.effect, "ModifyWillpower")
        self.assertEqual(ability.target, "OtherCharacters")
        self.assertEqual(ability.value, 2)
        self.assertIsNone(ability.condition)
        self.assertIsNone(ability.duration)

if __name__ == '__main__':
    unittest.main()
