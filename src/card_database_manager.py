import os
import pandas as pd
import glob
import datetime
from typing import List, Dict, Set, Tuple, Optional, Union
from src.utils.logger import get_logger
from src.utils.error_handler import safe_operation, handle_file_operations

# Get the logger instance
logger = get_logger()

class CardDatabaseManager:
    """
    Manages the card database, including meta-deck handling, set rotation,
    and card pool restrictions.
    """
    
    def __init__(self, 
                 card_dataset_path: str = 'data/processed/lorcana_card_master_dataset.csv',
                 meta_decks_dir: str = 'data/processed/meta_decks'):
        """
        Initialize the CardDatabaseManager.
        
        Args:
            card_dataset_path: Path to the master card dataset
            meta_decks_dir: Directory containing meta deck files
        """
        # Ensure paths are absolute
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.abspath(os.path.join(self.script_dir, '..'))
        
        if not os.path.isabs(card_dataset_path):
            self.card_dataset_path = os.path.join(self.project_root, card_dataset_path)
        else:
            self.card_dataset_path = card_dataset_path
            
        if not os.path.isabs(meta_decks_dir):
            self.meta_decks_dir = os.path.join(self.project_root, meta_decks_dir)
        else:
            self.meta_decks_dir = meta_decks_dir
        
        # Ensure meta decks directory exists
        os.makedirs(self.meta_decks_dir, exist_ok=True)
        
        # Load the card dataset
        self.card_df = self._load_card_dataset()
        
        # Track legal sets
        self.legal_sets = set(self.card_df['Set_Name'].unique())
        self.default_excluded_sets = {'Lorcana TCG Quick Start Decks'}
        
        # Current meta deck path
        self.current_meta_deck_path = None
    
    @handle_file_operations
    def _load_card_dataset(self) -> pd.DataFrame:
        """
        Load the card dataset from the specified path.
        
        Returns:
            DataFrame containing card data
        """
        card_df = pd.read_csv(self.card_dataset_path)
        return card_df
    
    def get_filtered_card_pool(self, legal_sets: Optional[Set[str]] = None) -> pd.DataFrame:
        """
        Get a filtered card pool based on legal sets.
        
        Args:
            legal_sets: Set of legal set names. If None, all sets except default excluded are legal.
            
        Returns:
            DataFrame with filtered card pool
        """
        if legal_sets is None:
            # By default, exclude certain sets
            return self.card_df[~self.card_df['Set_Name'].isin(self.default_excluded_sets)]
        else:
            # Filter by specified legal sets
            return self.card_df[self.card_df['Set_Name'].isin(legal_sets)]
    
    def get_available_meta_deck_files(self) -> List[str]:
        """
        Get a list of available meta deck files.
        
        Returns:
            List of meta deck filenames
        """
        pattern = os.path.join(self.meta_decks_dir, '*.csv')
        return [os.path.basename(f) for f in glob.glob(pattern)]
    
    def get_latest_meta_deck_file(self) -> str:
        """
        Get the most recent meta deck file based on filename date.
        
        Returns:
            Path to the most recent meta deck file, or None if no files exist
        """
        files = self.get_available_meta_deck_files()
        
        if not files:
            # If no files in meta_decks dir, check for the legacy location
            legacy_path = os.path.join(self.project_root, 'data/processed/lorcana_metagame_decks.csv')
            if os.path.exists(legacy_path):
                return legacy_path
            else:
                return None
        
        # Try to parse dates from filenames (format: meta_decks_YYYY-MM-DD.csv)
        dated_files = []
        for f in files:
            # Extract date from filename or use file modification time as fallback
            try:
                # Extract date from filename
                date_str = f.replace('meta_decks_', '').replace('.csv', '')
                date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                dated_files.append((date, f))
            except (ValueError, IndexError):
                # If date can't be parsed, use file modification time
                full_path = os.path.join(self.meta_decks_dir, f)
                mtime = os.path.getmtime(full_path)
                dated_files.append((datetime.datetime.fromtimestamp(mtime), f))
        
        if not dated_files:
            return None
            
        # Sort by date and get the most recent
        dated_files.sort(reverse=True)
        most_recent = dated_files[0][1]  # Filename only
        
        return os.path.join(self.meta_decks_dir, most_recent)
    
    @safe_operation(default_return=[], log_level='error')
    def load_meta_decks(self, meta_deck_path: Optional[str] = None) -> List[List[str]]:
        """
        Load meta decks from the specified path or the most recent file.
        
        Args:
            meta_deck_path: Path to the meta decks file. If None, uses the most recent file.
            
        Returns:
            List of deck lists, where each deck list is a list of card names
        """
        if meta_deck_path is None:
            meta_deck_path = self.get_latest_meta_deck_file()
            
        if not meta_deck_path:
            return []
            
        self.current_meta_deck_path = meta_deck_path
        
        # First attempt new format (list of deck lists)
        deck_lists = []
        df = pd.read_csv(meta_deck_path)
        
        # Group by Deck_Name
        for deck_name, group in df.groupby('Deck_Name'):
            deck_cards = []
            for _, row in group.iterrows():
                # Add the card to the deck multiple times based on Count
                card_count = row.get('Count', 1)
                card_name = row.get('Card_Name', '')
                deck_cards.extend([card_name] * card_count)
            deck_lists.append(deck_cards)
            
        return deck_lists
    
    @safe_operation(default_return=set(), log_level='error')
    def get_rotation_sets(self, rotation_date: Optional[datetime.date] = None) -> Set[str]:
        """
        Get the list of legal sets based on a rotation date.
        
        Args:
            rotation_date: The date to check legality against. If None, uses current date.
            
        Returns:
            Set of legal set names
        """
        if rotation_date is None:
            rotation_date = datetime.date.today()
        
        legal_sets = set()
        
        # Process each set in the card dataset
        for _, row in self.card_df.drop_duplicates(subset=['Set_Name']).iterrows():
            set_name = row.get('Set_Name')
            date_added_str = row.get('Date_Added', None)
            
            # Skip entries with missing data
            if not set_name or not date_added_str or pd.isna(date_added_str):
                continue
                
            try:
                # Parse the date and check if it's before the rotation date
                date_added = datetime.datetime.strptime(date_added_str, '%Y-%m-%d').date()
                
                # Sets are legal if they were added within 2 years of the rotation date
                years_diff = (rotation_date.year - date_added.year)
                is_legal = years_diff < 2 or (years_diff == 2 and 
                                             rotation_date.month < date_added.month or 
                                             (rotation_date.month == date_added.month and 
                                              rotation_date.day <= date_added.day))
                
                if is_legal:
                    legal_sets.add(set_name)
            except Exception as e:
                # Skip sets with unparseable dates
                logger.debug(f"Error processing set {row['Set_Name']}: {e}")
                continue
        
        return legal_sets
    
    def save_meta_deck_file(self, decks: Dict[str, List[str]], filename: Optional[str] = None) -> str:
        """
        Save meta decks to a new file with today's date.
        
        Args:
            decks: Dictionary mapping deck names to card lists
            filename: Optional filename, if None uses date format
            
        Returns:
            Path to the saved file
        """
        if filename is None:
            today = datetime.date.today().strftime('%Y-%m-%d')
            filename = f"meta_decks_{today}.csv"
            
        file_path = os.path.join(self.meta_decks_dir, filename)
        
        # Prepare data in the standard format
        rows = []
        for deck_name, cards in decks.items():
            # Count card quantities
            card_counts = {}
            for card in cards:
                card_counts[card] = card_counts.get(card, 0) + 1
            
            # Create rows with quantity
            for card_name, quantity in card_counts.items():
                rows.append({
                    'DeckName': deck_name,
                    'CardName': card_name,
                    'Quantity': quantity
                })
        
        # Save to CSV
        pd.DataFrame(rows).to_csv(file_path, index=False)
        return file_path
