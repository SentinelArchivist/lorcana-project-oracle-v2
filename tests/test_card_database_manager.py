import unittest
import os
import pandas as pd
import tempfile
import datetime
from pathlib import Path
import shutil

# Add parent directory to path so we can import our module
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.card_database_manager import CardDatabaseManager


class TestCardDatabaseManager(unittest.TestCase):
    
    def setUp(self):
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Create temporary card dataset with test data
        self.card_data = {
            'Set_Name': ['First Set', 'First Set', 'Second Set', 'Third Set', 'Excluded Set'],
            'Date_Added': ['2024-01-01T00:00:00', '2024-01-01T00:00:00', '2024-06-01T00:00:00', '2025-01-01T00:00:00', '2023-01-01T00:00:00'],
            'Name': ['Card A', 'Card B', 'Card C', 'Card D', 'Card E'],
            'Type': ['Character', 'Action', 'Character', 'Item', 'Character'],
            'Cost': [1, 2, 3, 4, 5]
        }
        self.card_df = pd.DataFrame(self.card_data)
        self.card_dataset_path = os.path.join(self.test_dir, 'test_cards.csv')
        self.card_df.to_csv(self.card_dataset_path, index=False)
        
        # Create temporary meta deck directory and files
        self.meta_decks_dir = os.path.join(self.test_dir, 'meta_decks')
        os.makedirs(self.meta_decks_dir, exist_ok=True)
        
        # Create an older meta deck file
        self.old_meta_data = {
            'DeckName': ['Test Deck 1', 'Test Deck 1', 'Test Deck 2'],
            'CardName': ['Card A', 'Card B', 'Card C'],
            'Quantity': [2, 2, 4]
        }
        old_meta_df = pd.DataFrame(self.old_meta_data)
        self.old_meta_path = os.path.join(self.meta_decks_dir, 'meta_decks_2024-01-15.csv')
        old_meta_df.to_csv(self.old_meta_path, index=False)
        
        # Create a newer meta deck file
        self.new_meta_data = {
            'DeckName': ['Test Deck 3', 'Test Deck 3', 'Test Deck 4'],
            'CardName': ['Card C', 'Card D', 'Card A'],
            'Quantity': [3, 2, 3]
        }
        new_meta_df = pd.DataFrame(self.new_meta_data)
        self.new_meta_path = os.path.join(self.meta_decks_dir, 'meta_decks_2024-06-15.csv')
        new_meta_df.to_csv(self.new_meta_path, index=False)
        
        # Create legacy-format meta deck file
        self.legacy_meta_data = {
            'Deck_Name': ['Legacy Deck 1', 'Legacy Deck 1', 'Legacy Deck 2'],
            'Card_Name': ['Card A', 'Card B', 'Card C']
        }
        legacy_meta_df = pd.DataFrame(self.legacy_meta_data)
        self.legacy_meta_path = os.path.join(self.test_dir, 'lorcana_metagame_decks.csv')
        legacy_meta_df.to_csv(self.legacy_meta_path, index=False)
        
        # Initialize the manager with test paths
        self.manager = CardDatabaseManager(
            card_dataset_path=self.card_dataset_path,
            meta_decks_dir=self.meta_decks_dir
        )
    
    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.test_dir)
    
    def test_initialization(self):
        """Test that the manager initializes correctly"""
        self.assertIsNotNone(self.manager.card_df)
        self.assertEqual(len(self.manager.card_df), 5)
        self.assertEqual(len(self.manager.legal_sets), 4)  # All sets in test data
    
    def test_get_filtered_card_pool(self):
        """Test filtering the card pool by sets"""
        # Default filtering (no excluded sets in our test data)
        filtered_df = self.manager.get_filtered_card_pool()
        self.assertEqual(len(filtered_df), 5)  # All cards should be included
        
        # Filter by specific sets
        legal_sets = {'First Set', 'Second Set'}
        filtered_df = self.manager.get_filtered_card_pool(legal_sets)
        self.assertEqual(len(filtered_df), 3)  # Cards A, B, C
        
        # Custom exclusion
        self.manager.default_excluded_sets = {'Excluded Set'}
        filtered_df = self.manager.get_filtered_card_pool()
        self.assertEqual(len(filtered_df), 4)  # All except Card E
    
    def test_get_available_meta_deck_files(self):
        """Test getting available meta deck files"""
        files = self.manager.get_available_meta_deck_files()
        self.assertEqual(len(files), 2)
        self.assertIn('meta_decks_2024-01-15.csv', files)
        self.assertIn('meta_decks_2024-06-15.csv', files)
    
    def test_get_latest_meta_deck_file(self):
        """Test getting the most recent meta deck file"""
        latest = self.manager.get_latest_meta_deck_file()
        self.assertTrue(latest.endswith('meta_decks_2024-06-15.csv'))
    
    def test_load_meta_decks_new_format(self):
        """Test loading meta decks with new format"""
        decks = self.manager.load_meta_decks(self.new_meta_path)
        self.assertEqual(len(decks), 2)  # Two decks
        
        # Verify first deck expanded correctly (3x Card C, 2x Card D)
        self.assertEqual(len(decks[0]), 5)
        self.assertEqual(decks[0].count('Card C'), 3)
        self.assertEqual(decks[0].count('Card D'), 2)
        
        # Verify second deck
        self.assertEqual(len(decks[1]), 3)
        self.assertEqual(decks[1].count('Card A'), 3)
    
    def test_load_meta_decks_legacy_format(self):
        """Test loading meta decks with legacy format"""
        decks = self.manager.load_meta_decks(self.legacy_meta_path)
        self.assertEqual(len(decks), 2)  # Two decks
        
        # Legacy format doesn't have quantities, so each card appears once
        self.assertEqual(decks[0], ['Card A', 'Card B'])
        self.assertEqual(decks[1], ['Card C'])
    
    def test_get_rotation_sets(self):
        """Test set rotation functionality"""
        # Test with a date that includes only the latest set
        rotation_date = datetime.date(2025, 1, 15)  # After Third Set release
        legal_sets = self.manager.get_rotation_sets(rotation_date)
        self.assertEqual(len(legal_sets), 3)  # Second and Third Set (within 2 years)
        self.assertNotIn('Excluded Set', legal_sets)  # Too old
        
        # Test with an earlier date
        rotation_date = datetime.date(2024, 7, 1)  # After Second Set
        legal_sets = self.manager.get_rotation_sets(rotation_date)
        self.assertEqual(len(legal_sets), 2)  # First and Second Set
        self.assertIn('First Set', legal_sets)
        self.assertIn('Second Set', legal_sets)
    
    def test_save_meta_deck_file(self):
        """Test saving meta decks to a file"""
        test_decks = {
            'New Deck 1': ['Card A', 'Card A', 'Card B', 'Card C'],
            'New Deck 2': ['Card D', 'Card D', 'Card E']
        }
        
        saved_path = self.manager.save_meta_deck_file(test_decks, 'test_save.csv')
        self.assertTrue(os.path.exists(saved_path))
        
        # Load and verify
        saved_df = pd.read_csv(saved_path)
        self.assertEqual(len(saved_df), 5)  # 5 rows total (2 + 3 cards with quantities)
        
        # Check the first deck's cards are saved correctly
        deck1_rows = saved_df[saved_df['DeckName'] == 'New Deck 1']
        self.assertEqual(len(deck1_rows), 3)  # 3 unique cards
        
        card_a_row = deck1_rows[deck1_rows['CardName'] == 'Card A']
        self.assertEqual(card_a_row['Quantity'].iloc[0], 2)  # 2x Card A


if __name__ == '__main__':
    unittest.main()
