import unittest
import pandas as pd
from src.deck_analyzer import DeckAnalyzer

class TestDeckAnalyzer(unittest.TestCase):
    def setUp(self):
        # Create a small test card dataframe
        self.test_cards = [
            {'Name': 'Test Character 1', 'Type': 'Character', 'Cost': 3, 'Ink': 'Ruby', 
             'Lore': 2, 'Keywords': 'Rush, Evasive', 'Strength': 3, 'Willpower': 2},
            {'Name': 'Test Character 2', 'Type': 'Character', 'Cost': 5, 'Ink': 'Ruby', 
             'Lore': 3, 'Keywords': 'Ward, Challenger', 'Strength': 4, 'Willpower': 4},
            {'Name': 'Test Action', 'Type': 'Action', 'Cost': 2, 'Ink': 'Amber', 
             'Lore': 0, 'Keywords': ''},
            {'Name': 'Test Location', 'Type': 'Location', 'Cost': 4, 'Ink': 'Amber', 
             'Lore': 1, 'Keywords': ''},
            {'Name': 'Test Singer', 'Type': 'Character', 'Cost': 3, 'Ink': 'Sapphire', 
             'Lore': 1, 'Keywords': 'Singer 3'},
            {'Name': 'Test Song', 'Type': 'Song', 'Cost': 4, 'Ink': 'Sapphire', 
             'Lore': 0, 'Keywords': ''},
        ]
        self.card_df = pd.DataFrame(self.test_cards)
        self.analyzer = DeckAnalyzer(self.card_df)

    def test_analyze_deck_basic(self):
        # Test with a basic deck without performance data
        deck = ['Test Character 1'] * 20 + ['Test Character 2'] * 15 + ['Test Action'] * 15 + ['Test Location'] * 10
        
        analysis = self.analyzer.analyze_deck(deck)
        
        # Check if analysis contains all expected sections
        self.assertIn('composition', analysis)
        self.assertIn('synergies', analysis)
        self.assertIn('key_cards', analysis)
        self.assertIn('strategy', analysis)
        
        # Check card type counts
        self.assertEqual(analysis['composition']['card_types']['Character'], 35)
        self.assertEqual(analysis['composition']['card_types']['Action'], 15)
        self.assertEqual(analysis['composition']['card_types']['Location'], 10)
        
        # Check identified key cards (should include cards with 3+ copies)
        key_card_names = [card['name'] for card in analysis['key_cards']]
        self.assertIn('Test Character 1', key_card_names)
        self.assertIn('Test Character 2', key_card_names)
        self.assertIn('Test Action', key_card_names)
        
        # Check strategy is determined
        self.assertIsNotNone(analysis['strategy']['archetype'])

    def test_analyze_deck_with_performance(self):
        # Test with performance data
        deck = ['Test Character 1'] * 20 + ['Test Character 2'] * 15 + ['Test Action'] * 15 + ['Test Location'] * 10
        performance_data = {
            'Meta Deck 1': 0.7,  # 70% win rate (strength)
            'Meta Deck 2': 0.5,  # 50% win rate (neutral)
            'Meta Deck 3': 0.3,  # 30% win rate (weakness)
        }
        
        analysis = self.analyzer.analyze_deck(deck, performance_data)
        
        # Check if performance data is included
        self.assertIn('performance', analysis)
        self.assertAlmostEqual(analysis['performance']['overall_win_rate'], 0.5)
        
        # Check strengths and weaknesses
        strengths = [s['deck'] for s in analysis['performance']['strengths']]
        weaknesses = [w['deck'] for w in analysis['performance']['weaknesses']]
        self.assertIn('Meta Deck 1', strengths)
        self.assertIn('Meta Deck 3', weaknesses)

    def test_identify_synergies(self):
        # Test synergy identification with specific combinations
        deck = ['Test Character 1', 'Test Character 2', 'Test Singer', 'Test Song'] * 15
        
        analysis = self.analyzer.analyze_deck(deck)
        
        # Check for keyword synergies
        keyword_synergies = []
        for synergy in analysis['synergies']:
            if synergy['type'] == 'keyword':
                keyword_synergies.append(tuple(sorted(synergy['keywords'])))
                
        # Check for expected keyword synergies across cards
        self.assertIn(('Rush', 'Ward'), [tuple(sorted(x)) for x in keyword_synergies])
        self.assertIn(('Challenger', 'Evasive'), [tuple(sorted(x)) for x in keyword_synergies])
        
        # Make sure we have some card type synergies
        type_synergies = [s for s in analysis['synergies'] if s['type'] == 'card_type']
        self.assertTrue(len(type_synergies) > 0, "No card type synergies detected")

    def test_generate_report(self):
        # Test report generation
        deck = ['Test Character 1'] * 20 + ['Test Character 2'] * 15 + ['Test Action'] * 15 + ['Test Location'] * 10
        performance_data = {
            'Meta Deck 1': 0.7,
            'Meta Deck 2': 0.5,
            'Meta Deck 3': 0.3,
        }
        
        report = self.analyzer.generate_report('Test Deck', deck, performance_data)
        
        # Check if report contains expected sections
        self.assertIn('# Deck Analysis: Test Deck', report)
        self.assertIn('## Strategy Overview', report)
        self.assertIn('## Key Cards', report)
        self.assertIn('## Notable Synergies', report)
        self.assertIn('## Deck Composition', report)
        self.assertIn('## Performance Analysis', report)
        
        # Check if report contains specific content
        self.assertIn('**Overall Win Rate**: 50.0%', report)
        self.assertIn('Test Character 1', report)
        self.assertIn('Test Character 2', report)

if __name__ == '__main__':
    unittest.main()
