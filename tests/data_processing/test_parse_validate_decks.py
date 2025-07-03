import unittest
import os
import pandas as pd
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.data_processing.parse_validate_decks import parse_and_validate_decks

class TestParseValidateDecks(unittest.TestCase):
    """Tests the decklist parsing and validation script."""

    def setUp(self):
        """Set up mock data files for tests."""
        self.test_dir = 'tests/temp_data'
        os.makedirs(self.test_dir, exist_ok=True)

        self.master_path = os.path.join(self.test_dir, 'master.csv')
        self.decklist_path = os.path.join(self.test_dir, 'decks.md')
        self.invalid_decklist_path = os.path.join(self.test_dir, 'invalid_decks.md')
        self.output_path = os.path.join(self.test_dir, 'output.csv')

        # Create mock master card dataset
        master_data = {'Name': ['Mickey Mouse, Brave Little Tailor', 'Elsa, Snow Queen', 'Captain Hook, Forceful Duelist']}
        pd.DataFrame(master_data).to_csv(self.master_path, index=False)

        # Create mock valid decklist file
        with open(self.decklist_path, 'w') as f:
            f.write('# [Set 1] Amber/Amethyst Aggro\n')
            f.write('4 Mickey Mouse, Brave Little Tailor\n')
            f.write('2 Elsa, Snow Queen\n')

        # Create mock invalid decklist file
        with open(self.invalid_decklist_path, 'w') as f:
            f.write('# [Set 1] Invalid Deck\n')
            f.write('1 Goofy, Super Goof\n') # This card is not in the master list

    def tearDown(self):
        """Clean up created files and directory."""
        for path in [self.master_path, self.decklist_path, self.invalid_decklist_path, self.output_path]:
            if os.path.exists(path):
                os.remove(path)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_success_scenario(self):
        """Tests successful parsing and validation of a correct decklist."""
        returned_df = parse_and_validate_decks(self.master_path, self.decklist_path, self.output_path)

        self.assertIsInstance(returned_df, pd.DataFrame)
        self.assertEqual(len(returned_df), 2)
        self.assertTrue(os.path.exists(self.output_path))

        saved_df = pd.read_csv(self.output_path)
        self.assertEqual(len(saved_df), 2)
        self.assertEqual(saved_df.loc[0, 'CardName'], 'Mickey Mouse, Brave Little Tailor')

    def test_validation_failure_invalid_card(self):
        """Tests that validation fails when a card is not in the master dataset."""
        with self.assertRaises(ValueError) as cm:
            parse_and_validate_decks(self.master_path, self.invalid_decklist_path, self.output_path)
        
        self.assertIn('Validation Failed', str(cm.exception))
        self.assertIn('Goofy, Super Goof', str(cm.exception))
        self.assertFalse(os.path.exists(self.output_path), "Output file should not be created on validation failure.")

    def test_file_not_found_error(self):
        """Tests that a FileNotFoundError is raised for missing input files."""
        with self.assertRaises(FileNotFoundError):
            parse_and_validate_decks('non_existent_master.csv', self.decklist_path, self.output_path)

        with self.assertRaises(FileNotFoundError):
            parse_and_validate_decks(self.master_path, 'non_existent_decks.md', self.output_path)

if __name__ == '__main__':
    unittest.main()
