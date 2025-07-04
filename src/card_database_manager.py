import os
import pandas as pd
import datetime
import glob
from typing import List, Dict, Set, Tuple, Optional, Union


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
    
    def _load_card_dataset(self) -> pd.DataFrame:
        """
        Load the card dataset from the specified path.
        
        Returns:
            DataFrame containing card data
        """
        try:
            card_df = pd.read_csv(self.card_dataset_path)
            return card_df
        except FileNotFoundError:
            raise FileNotFoundError(f"Card dataset not found at {self.card_dataset_path}")
    
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
            
        if meta_deck_path is None or not os.path.exists(meta_deck_path):
            # No meta deck file available
            return []
        
        self.current_meta_deck_path = meta_deck_path
        
        try:
            meta_decks_df = pd.read_csv(meta_deck_path)
            
            # Check if the file has the old format (Deck_Name, Card_Name columns)
            if 'Deck_Name' in meta_decks_df.columns and 'Card_Name' in meta_decks_df.columns:
                # Group by deck name and aggregate card names into a list
                deck_lists = meta_decks_df.groupby('Deck_Name')['Card_Name'].apply(
                    lambda x: list(x)).tolist()
            # Check if it has the newer format (DeckName, CardName, Quantity columns)
            elif 'DeckName' in meta_decks_df.columns and 'CardName' in meta_decks_df.columns and 'Quantity' in meta_decks_df.columns:
                # Group by deck name, then expand based on quantity
                deck_lists = []
                for deck_name, group in meta_decks_df.groupby('DeckName'):
                    deck = []
                    for _, row in group.iterrows():
                        deck.extend([row['CardName']] * int(row['Quantity']))
                    deck_lists.append(deck)
            else:
                raise ValueError(f"Unrecognized meta deck file format in {meta_deck_path}")
                
            return deck_lists
        except Exception as e:
            print(f"Error loading meta decks: {e}")
            return []
    
    def get_rotation_sets(self, rotation_date: Optional[datetime.date] = None) -> Set[str]:
        """
        Determine which sets are legal based on a rotation date.
        
        Args:
            rotation_date: Date for set rotation. If None, uses current date.
            
        Returns:
            Set of legal set names
        """
        if rotation_date is None:
            rotation_date = datetime.date.today()
        
        # Get set information including release dates
        sets_df = self.card_df[['Set_Name', 'Date_Added']].drop_duplicates()
        
        # Parse dates and filter by rotation date
        legal_sets = set()
        for _, row in sets_df.iterrows():
            try:
                set_name = row['Set_Name']
                date_str = row['Date_Added']
                
                # Skip sets without dates
                if pd.isna(date_str) or not date_str:
                    continue
                    
                # Parse the date from the card dataset
                set_date = datetime.datetime.strptime(date_str.split('T')[0], '%Y-%m-%d').date()
                
                # Lorcana typically has a 2-year rotation
                # Sets released within 2 years of the rotation date are legal
                if (rotation_date - set_date).days <= 730:  # 730 days = ~2 years
                    legal_sets.add(set_name)
            except Exception as e:
                # Skip sets with unparseable dates
                print(f"Error processing set {row['Set_Name']}: {e}")
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
