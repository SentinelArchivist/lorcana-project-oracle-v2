import unittest
from src.data_processing.ability_transformer import transform_abilities

class TestAbilityTransformer(unittest.TestCase):

    def test_transform_simple_keyword(self):
        """Tests transforming a simple keyword like 'Evasive'."""
        parsed_ability = [{"ability": "Evasive", "value": None}]
        expected_schema = [{"effect": "ADD_KEYWORD", "keyword": "EVASIVE"}]
        self.assertEqual(transform_abilities(parsed_ability), expected_schema)

    def test_transform_shift_keyword(self):
        """Tests transforming a 'Shift' keyword."""
        parsed_ability = [{"ability": "Shift", "value": 5}]
        expected_schema = [{"effect": "SET_SHIFT_COST", "value": 5}]
        self.assertEqual(transform_abilities(parsed_ability), expected_schema)

    def test_transform_keyword_with_value(self):
        """Tests transforming a keyword with a value, like 'Resist +1'."""
        parsed_ability = [{"ability": "Resist", "value": 1}]
        expected_schema = [{"effect": "ADD_KEYWORD", "keyword": "RESIST", "value": 1}]
        self.assertEqual(transform_abilities(parsed_ability), expected_schema)

    def test_transform_singer_keyword(self):
        """Tests transforming a 'Singer' keyword with a value."""
        parsed_ability = [{"ability": "Singer", "value": 5}]
        expected_schema = [{"effect": "SINGER", "value": 5}]
        self.assertEqual(transform_abilities(parsed_ability), expected_schema)

    def test_transform_complex_and_edge_cases(self):
        """Tests a complex mix of abilities and edge cases."""
        # Test a complex list
        parsed_abilities = [
            {"ability": "Evasive", "value": None},
            {"ability": "Resist", "value": 2},
            {"ability": "Puppy Shift", "value": 1},
            {"ability": "Singer", "value": 3}
        ]
        expected_schema = [
            {"effect": "ADD_KEYWORD", "keyword": "EVASIVE"},
            {"effect": "ADD_KEYWORD", "keyword": "RESIST", "value": 2},
            {"effect": "SET_SHIFT_COST", "value": 1},
            {"effect": "SINGER", "value": 3}
        ]
        self.assertEqual(transform_abilities(parsed_abilities), expected_schema)

        # Test an empty list
        self.assertEqual(transform_abilities([]), [])
