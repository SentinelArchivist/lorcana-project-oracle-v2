import unittest
import sys
import os

# Add the src directory to the Python path to allow for module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from abilities.create_abilities_database import parse_ability_text

class TestAbilityParser(unittest.TestCase):
    """
    Test suite for parsing raw card text into structured ParsedAbility objects.
    We will add a new test for each type of ability we teach the parser.
    """

    def test_parse_simple_keyword_rush(self):
        """Tests parsing of the 'Rush' keyword."""
        text = "Rush (This character can challenge the turn they're played.)"
        abilities = parse_ability_text(text)
        self.assertEqual(len(abilities), 1)
        ability = abilities[0]
        self.assertEqual(ability.trigger, "Passive")
        self.assertEqual(ability.effect, "GainKeyword")
        self.assertEqual(ability.target, "Self")
        self.assertEqual(ability.value, {"keyword": "Rush", "amount": True})

    def test_parse_keyword_with_value_challenger(self):
        """Tests parsing a keyword that includes a numeric value, like 'Challenger'."""
        text = "Challenger +2 (While challenging, this character gets +2 ※.)"
        abilities = parse_ability_text(text)
        self.assertEqual(len(abilities), 1)
        ability = abilities[0]
        self.assertEqual(ability.value, {"keyword": "Challenger", "amount": 2})

    def test_parse_keyword_with_value_shift(self):
        """Tests parsing a keyword with a numeric value that isn't preceded by a plus sign."""
        text = "Shift 5 (You may pay 5 ⬡ to play this on top of one of your characters named Mickey Mouse.)"
        abilities = parse_ability_text(text)
        self.assertEqual(len(abilities), 1)
        ability = abilities[0]
        self.assertEqual(ability.value, {"keyword": "Shift", "amount": 5})

    def test_no_abilities_parsed_from_empty_string(self):
        """Tests that an empty string results in no parsed abilities."""
        text = ""
        abilities = parse_ability_text(text)
        self.assertEqual(len(abilities), 0)

    def test_no_abilities_parsed_from_unrelated_text(self):
        """Tests that flavor text or non-keyword text doesn't get parsed."""
        text = "A puppy. That's it. That's the card."
        abilities = parse_ability_text(text)
        self.assertEqual(len(abilities), 0)

    def test_multiple_keywords_in_one_text(self):
        """Tests that multiple keywords in the same text block are all parsed."""
        text = "Rush. Ward. Challenger +1"
        abilities = parse_ability_text(text)
        self.assertEqual(len(abilities), 3)
        
        # Check that all keywords were found
        found_keywords = sorted([a.value['keyword'] for a in abilities])
        self.assertEqual(found_keywords, ["Challenger", "Rush", "Ward"])
        
        # Check the challenger value specifically to ensure its amount was parsed correctly
        challenger_ability = next((a for a in abilities if a.value['keyword'] == 'Challenger'), None)
        self.assertIsNotNone(challenger_ability)
        self.assertEqual(challenger_ability.value['amount'], 1)

if __name__ == '__main__':
    unittest.main()
