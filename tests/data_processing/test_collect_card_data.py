import unittest
import requests
import os
import pandas as pd
from unittest.mock import patch, MagicMock
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.data_processing.collect_card_data import fetch_lorcana_data

class TestCollectCardData(unittest.TestCase):
    """Tests the card data collection and processing script."""

    def setUp(self):
        """Set up for tests."""
        self.output_path = 'tests/temp_card_data.csv'
        # Ensure the temp file doesn't exist before a test
        if os.path.exists(self.output_path):
            os.remove(self.output_path)

    def tearDown(self):
        """Clean up after tests."""
        # Clean up the created file
        if os.path.exists(self.output_path):
            os.remove(self.output_path)

    @patch('requests.get')
    def test_fetch_lorcana_data_success(self, mock_get):
        """Tests the successful fetching and processing of card data using a mock API response."""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'Artist': 'Artist 1', 'Image': 'img1.png', 'Classifications': ['Storyborn'], 'Abilities': ['Ability 1'], 'Flavor': 'Flavor 1'},
            {'Artist': 'Artist 2', 'Image': 'img2.png', 'Classifications': ['Dreamborn'], 'Abilities': ['Ability 2'], 'Flavor': 'Flavor 2'}
        ]
        mock_get.return_value = mock_response

        # Run the function
        returned_df = fetch_lorcana_data(self.output_path)

        # Assertions
        self.assertIsInstance(returned_df, pd.DataFrame, "Function should return a DataFrame.")
        self.assertEqual(len(returned_df), 2, "Returned DataFrame should contain 2 rows.")

        self.assertTrue(os.path.exists(self.output_path), "Output CSV file should be created.")
        
        saved_df = pd.read_csv(self.output_path)
        self.assertEqual(len(saved_df), 2, "Saved CSV should contain 2 rows.")
        self.assertNotIn('Image', saved_df.columns, "'Image' column should be dropped.")
        self.assertNotIn('Flavor', saved_df.columns, "'Flavor' column should be dropped.")
        self.assertIn('Classification', saved_df.columns, "'Classification' column should be created.")
        self.assertEqual(saved_df.loc[0, 'Classification'], 'Storyborn')

    @patch('requests.get')
    def test_fetch_lorcana_data_api_error(self, mock_get):
        """Tests the script's handling of an API error."""
        # Mock a failed API response
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Client Error")
        mock_get.return_value = mock_response

        # The function should raise a RuntimeError on API failure
        with self.assertRaises(RuntimeError):
            fetch_lorcana_data(self.output_path)

        self.assertFalse(os.path.exists(self.output_path), "Output file should not be created on API error.")

if __name__ == '__main__':
    unittest.main()
