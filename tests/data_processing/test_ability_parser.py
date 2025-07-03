import unittest
from src.data_processing.ability_parser import parse_abilities

class TestAbilityParser(unittest.TestCase):

    def test_parse_single_keyword(self):
        """Tests parsing a single, simple keyword."""
        ability_string = "Evasive"
        expected_output = [{"ability": "Evasive", "value": None}]
        self.assertEqual(parse_abilities(ability_string), expected_output)

    def test_parse_comma_separated_keywords(self):
        """Tests parsing a comma-separated list of simple keywords."""
        ability_string = "Evasive, Ward"
        expected_output = [
            {"ability": "Evasive", "value": None},
            {"ability": "Ward", "value": None}
        ]
        self.assertEqual(parse_abilities(ability_string), expected_output)

    def test_parse_keyword_with_value(self):
        """Tests parsing a keyword with a numeric value."""
        ability_string = "Shift 5"
        expected_output = [{"ability": "Shift", "value": 5}]
        self.assertEqual(parse_abilities(ability_string), expected_output)

    def test_parse_keyword_with_signed_value(self):
        """Tests parsing a keyword with a signed numeric value (e.g., +1)."""
        ability_string = "Resist +1"
        expected_output = [{"ability": "Resist", "value": 1}]
        self.assertEqual(parse_abilities(ability_string), expected_output)

    def test_parse_complex_mixed_string(self):
        """Tests parsing a complex string with mixed ability types."""
        ability_string = "Shift 5, Evasive, Resist +1"
        expected_output = [
            {"ability": "Shift", "value": 5},
            {"ability": "Evasive", "value": None},
            {"ability": "Resist", "value": 1}
        ]
        self.assertEqual(parse_abilities(ability_string), expected_output)

    def test_parse_compound_keyword_with_value(self):
        """Tests parsing a compound keyword with a numeric value."""
        ability_string = "Puppy Shift 3"
        expected_output = [{"ability": "Puppy Shift", "value": 3}]
        self.assertEqual(parse_abilities(ability_string), expected_output)
