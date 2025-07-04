import pandas as pd
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Set, Optional

class DeckAnalyzer:
    """Analyzes deck compositions to identify synergies and explain strategic strengths."""

    # Card type synergies - which types work well together
    TYPE_SYNERGIES = {
        ('Character', 'Character'): 'Multiple characters can challenge together and build board presence',
        ('Character', 'Item'): 'Items can enhance character abilities or protect them',
        ('Character', 'Action'): 'Actions can provide tempo advantage or protect key characters',
        ('Character', 'Location'): 'Locations provide passive benefits that grow in value with strong characters',
        ('Character', 'Song'): 'Songs can be played for free with Singer characters',
        ('Action', 'Action'): 'Multiple actions can create powerful combinations',
        ('Item', 'Item'): 'Multiple items can build an engine of effects',
    }
    
    # Known keyword synergies
    KEYWORD_SYNERGIES = {
        ('Evasive', 'Challenger'): 'Evasive characters can challenge without being blocked, while Challenger provides extra lore',
        ('Ward', 'Support'): 'Ward protects high-value characters that can then safely use Support',
        ('Singer', 'Song'): 'Singer characters can play Songs without paying their ink cost',
        ('Rush', 'Challenger'): 'Rush characters can challenge immediately, and Challenger increases their lore gain',
        ('Rush', 'Evasive'): 'Allows for immediate attacks that are harder to block',
        ('Ward', 'Challenger'): 'Creates protected threats that can immediately challenge',
        ('Shift', 'Evasive'): 'Creates flexible threats that are difficult to block',
        ('Shift', 'Ward'): 'Creates protected threats that can adapt to different situations',
        ('Sing', 'Protection'): 'Singers can be protected while generating value',
        ('Rush', 'Ward'): 'Creates protected threats that can attack immediately',
        ('Challenger', 'Evasive'): 'Creates threats that can challenge and are harder to block',
    }
    
    # Ink color synergies and their general strategies
    INK_SYNERGIES = {
        ('Amber', 'Amethyst'): 'Combines board control with direct damage effects',
        ('Amber', 'Emerald'): 'Mixes aggression with card advantage and ramp',
        ('Amber', 'Ruby'): 'Full aggression strategy with multiple attackers',
        ('Amber', 'Sapphire'): 'Balances aggression with protection effects',
        ('Amber', 'Steel'): 'Combines direct damage with board wipes',
        ('Amethyst', 'Emerald'): 'Control deck with card advantage',
        ('Amethyst', 'Ruby'): 'Tempo-oriented with disruption',
        ('Amethyst', 'Sapphire'): 'Full control strategy',
        ('Amethyst', 'Steel'): 'Control with board wipes',
        ('Emerald', 'Ruby'): 'Ramp into big threats',
        ('Emerald', 'Sapphire'): 'Value generation and protection',
        ('Emerald', 'Steel'): 'Midrange with board clears',
        ('Ruby', 'Sapphire'): 'Aggression with protection',
        ('Ruby', 'Steel'): 'Aggression with disruption',
        ('Sapphire', 'Steel'): 'Defensive strategy with board wipes',
    }
    
    def __init__(self, card_df: pd.DataFrame):
        """Initialize the analyzer with card dataset information.
        
        Args:
            card_df: Pandas DataFrame containing all card data
        """
        self.card_df = card_df
        
    def analyze_deck(self, deck_list: List[str], performance_data: Optional[Dict[str, float]] = None) -> Dict:
        """Analyze a deck to identify synergies, strategic strengths, and key cards.
        
        Args:
            deck_list: List of card names in the deck
            performance_data: Optional dict of deck performance against meta decks
            
        Returns:
            Dict containing analysis results including synergies, strategy, and key cards
        """
        # Count occurrences of each card
        card_counts = Counter(deck_list)
        
        # Get full card information from the dataset
        deck_cards_info = []
        for card_name in deck_list:
            card_info = self.card_df[self.card_df['Name'] == card_name].to_dict('records')
            if card_info:  # Add only if the card was found
                deck_cards_info.append(card_info[0])
        
        # Extract card types, keywords, abilities, costs, inks, etc.
        types = [card.get('Type', 'Character') for card in deck_cards_info]
        costs = [card.get('Cost', 0) for card in deck_cards_info]
        inks = set(card.get('Ink') for card in deck_cards_info if card.get('Ink'))
        keywords = []
        
        # Process keywords properly
        for card in deck_cards_info:
            card_keywords = card.get('Keywords', '')
            if isinstance(card_keywords, str) and card_keywords:
                # Split by comma and clean up
                kw_list = [kw.strip() for kw in card_keywords.split(',')]
                # Extract base keywords (without values)
                base_kws = [kw.split()[0] for kw in kw_list if kw]
                keywords.extend(base_kws)
            elif isinstance(card_keywords, list):
                # Extract base keywords from list
                base_kws = [kw.split()[0] if isinstance(kw, str) else '' for kw in card_keywords]
                keywords.extend([kw for kw in base_kws if kw])
        
        # Analyze the deck composition
        type_counts = Counter(types)
        keyword_counts = Counter(keywords)
        mana_curve = self._analyze_mana_curve(costs)
        identified_synergies = self._identify_synergies(deck_cards_info)
        key_cards = self._identify_key_cards(deck_cards_info, card_counts)
        deck_strategy = self._determine_strategy(type_counts, keyword_counts, inks, identified_synergies)
        
        # Generate the analysis result
        analysis = {
            'composition': {
                'card_types': dict(type_counts),
                'mana_curve': mana_curve,
                'keyword_frequency': dict(keyword_counts),
                'ink_colors': list(inks)
            },
            'synergies': identified_synergies,
            'key_cards': key_cards,
            'strategy': deck_strategy
        }
        
        # Add performance analysis if data is provided
        if performance_data:
            analysis['performance'] = self._analyze_performance(performance_data)
            
        return analysis
    
    def _analyze_mana_curve(self, costs: List[int]) -> Dict[str, int]:
        """Analyze the mana curve of the deck."""
        curve = Counter(costs)
        # Group high costs together
        high_cost = sum(curve[cost] for cost in curve if cost >= 8)
        curve_result = {str(cost): count for cost, count in curve.items() if cost < 8}
        curve_result['8+'] = high_cost
        return curve_result
    
    def _identify_synergies(self, cards: List[Dict]) -> List[Dict]:
        """Identify synergies between cards in the deck."""
        synergies = []
        
        # Extract card types and keywords
        card_types = [(card.get('Name', ''), card.get('Type', 'Character')) for card in cards]
        unique_cards = [card.get('Name', '') for card in cards]
        card_info_map = {card.get('Name', ''): card for card in cards}
        
        # Extract card keywords for synergy checking
        card_keywords = {}
        for card_name in unique_cards:
            if card_name in card_info_map:
                kws = card_info_map[card_name].get('Keywords', '')
                if isinstance(kws, str):
                    # Split by comma, clean up, and filter empty strings
                    card_keywords[card_name] = [kw.strip() for kw in kws.split(',') if kw.strip()] 
                elif isinstance(kws, list):
                    card_keywords[card_name] = kws
                else:
                    card_keywords[card_name] = []
        
        # Check for type synergies
        type_pairs = set()
        for i, (card1_name, type1) in enumerate(card_types):
            for j, (card2_name, type2) in enumerate(card_types[i+1:], i+1):
                if card1_name != card2_name:  # Don't check a card with itself
                    type_pair = tuple(sorted([type1, type2]))
                    if type_pair in self.TYPE_SYNERGIES and type_pair not in type_pairs:
                        synergies.append({
                            'type': 'card_type',
                            'cards': [card1_name, card2_name],
                            'synergy': self.TYPE_SYNERGIES[type_pair],
                            'strength': 'medium'
                        })
                        type_pairs.add(type_pair)
        
        # Check for keyword synergies
        keyword_pairs = set()
        
        # First, check for synergies within the same card (like Rush + Evasive)
        for card_name, keywords_list in card_keywords.items():
            # Get all unique base keywords from this card
            base_keywords = [kw.split()[0] for kw in keywords_list if kw]
            # Check all pairs of keywords
            for i, kw1 in enumerate(base_keywords):
                for kw2 in base_keywords[i+1:]:
                    kw_pair = tuple(sorted([kw1, kw2]))
                    if kw_pair in self.KEYWORD_SYNERGIES and kw_pair not in keyword_pairs:
                        synergies.append({
                            'type': 'keyword',
                            'cards': [card_name],  # Only one card here
                            'keywords': list(kw_pair),
                            'synergy': self.KEYWORD_SYNERGIES[kw_pair],
                            'strength': 'high'
                        })
                        keyword_pairs.add(kw_pair)
        
        # Then check for synergies between different cards
        for card1_name, keywords1 in card_keywords.items():
            for card2_name, keywords2 in card_keywords.items():
                if card1_name != card2_name:  # Don't check a card with itself
                    for kw1 in keywords1:
                        for kw2 in keywords2:
                            # Extract base keyword without values
                            base_kw1 = kw1.split()[0] if kw1 else ''
                            base_kw2 = kw2.split()[0] if kw2 else ''
                            kw_pair = tuple(sorted([base_kw1, base_kw2]))
                            
                            if kw_pair in self.KEYWORD_SYNERGIES and kw_pair not in keyword_pairs:
                                synergies.append({
                                    'type': 'keyword',
                                    'cards': [card1_name, card2_name],
                                    'keywords': list(kw_pair),
                                    'synergy': self.KEYWORD_SYNERGIES[kw_pair],
                                    'strength': 'high'
                                })
                                keyword_pairs.add(kw_pair)
        
        # Look for special ability synergies (e.g., drawing cards, buffing)
        # This would require more detailed ability parsing
        
        return synergies
    
    def _identify_key_cards(self, cards: List[Dict], card_counts: Dict[str, int]) -> List[Dict]:
        """Identify key cards in the deck based on their qualities and quantity."""
        key_cards = []
        
        # First, find cards with multiple copies as they are likely important
        for card_name, count in card_counts.items():
            if count >= 3:  # If we have 3+ copies, it's likely a key card
                card_info = next((c for c in cards if c.get('Name') == card_name), None)
                if card_info:
                    reason = f"Included {count}x copies, suggesting it's central to the deck's strategy"
                    key_cards.append({
                        'name': card_name,
                        'count': count,
                        'reason': reason
                    })
        
        # Next, look for high-impact cards (based on cost, lore, abilities)
        for card in cards:
            name = card.get('Name', '')
            # Skip cards we've already identified
            if any(k['name'] == name for k in key_cards):
                continue
                
            is_key = False
            reasons = []
            
            # High lore is valuable
            if card.get('Lore', 0) >= 3:
                is_key = True
                reasons.append(f"Provides high lore value ({card.get('Lore')})") 
            
            # High cost cards are usually impactful
            if card.get('Cost', 0) >= 7:
                is_key = True
                reasons.append(f"High-cost card ({card.get('Cost')}) with potentially game-changing impact")
            
            # Look for important keywords
            keywords = card.get('Keywords', [])
            if isinstance(keywords, str) and keywords:
                keywords = [kw.strip() for kw in keywords.split(',')]
            
            important_keywords = ['Evasive', 'Ward', 'Rush', 'Challenger', 'Singer', 'Shift']
            found_keywords = [kw.split()[0] for kw in keywords if any(ik in kw for ik in important_keywords)]
            if found_keywords:
                is_key = True
                reasons.append(f"Has powerful keywords: {', '.join(found_keywords)}")
            
            if is_key:
                key_cards.append({
                    'name': name,
                    'count': card_counts[name],
                    'reason': '; '.join(reasons)
                })
        
        # Limit to top 5-8 key cards to keep it focused
        return sorted(key_cards, key=lambda x: x['count'], reverse=True)[:8]
    
    def _determine_strategy(self, type_counts: Counter, keyword_counts: Counter, 
                           inks: Set[str], synergies: List[Dict]) -> Dict:
        """Determine the overall strategy of the deck."""
        strategy = {}
        
        # Determine archetype based on card types
        if type_counts.get('Character', 0) >= 30:
            if type_counts.get('Action', 0) >= 15:
                strategy['archetype'] = 'Tempo'
                strategy['description'] = 'Focuses on playing efficient characters and using actions for tempo advantage'
            else:
                strategy['archetype'] = 'Aggro'
                strategy['description'] = 'Aims to quickly deploy characters and challenge for lore'
        elif type_counts.get('Action', 0) >= 20:
            strategy['archetype'] = 'Control'
            strategy['description'] = 'Uses actions to control the board while generating value over time'
        elif type_counts.get('Location', 0) >= 8:
            strategy['archetype'] = 'Value'
            strategy['description'] = 'Generates ongoing value through locations and persistent effects'
        else:
            strategy['archetype'] = 'Midrange'
            strategy['description'] = 'Balanced approach with a mix of threats and answers'
        
        # Determine play style based on keywords
        play_style = []
        if keyword_counts.get('Evasive', 0) + keyword_counts.get('Rush', 0) >= 8:
            play_style.append('Fast-paced')
        if keyword_counts.get('Ward', 0) + keyword_counts.get('Support', 0) >= 8:
            play_style.append('Defensive')
        if keyword_counts.get('Challenger', 0) >= 6:
            play_style.append('Lore-focused')
        if keyword_counts.get('Singer', 0) >= 4 and type_counts.get('Song', 0) >= 6:
            play_style.append('Combo-oriented')
        
        if not play_style:  # Default if no specific style is detected
            play_style = ['Balanced']
            
        strategy['play_style'] = play_style
        
        # Add ink color strategy if available
        if len(inks) == 2:  # Standard 2-color deck
            ink_pair = tuple(sorted(list(inks)))
            if ink_pair in self.INK_SYNERGIES:
                strategy['ink_strategy'] = self.INK_SYNERGIES[ink_pair]
        
        return strategy
    
    def _analyze_performance(self, performance_data: Dict[str, float]) -> Dict:
        """Analyze the performance data of the deck against meta decks."""
        performance = {
            'overall_win_rate': sum(performance_data.values()) / len(performance_data) if performance_data else 0,
            'matchups': performance_data,
            'strengths': [],
            'weaknesses': []
        }
        
        # Identify strong and weak matchups
        for deck_name, win_rate in performance_data.items():
            if win_rate >= 0.6:  # 60%+ win rate is strong
                performance['strengths'].append({
                    'deck': deck_name,
                    'win_rate': win_rate,
                    'note': 'Favorable matchup'
                })
            elif win_rate <= 0.4:  # 40%- win rate is weak
                performance['weaknesses'].append({
                    'deck': deck_name,
                    'win_rate': win_rate,
                    'note': 'Unfavorable matchup'
                })
        
        return performance
    
    def generate_report(self, deck_name: str, deck_list: List[str], 
                        performance_data: Optional[Dict[str, float]] = None) -> str:
        """Generate a human-readable report for the deck.
        
        Args:
            deck_name: Name of the deck
            deck_list: List of card names
            performance_data: Optional performance data against meta decks
            
        Returns:
            A formatted string containing the analysis report
        """
        # Get the full analysis
        analysis = self.analyze_deck(deck_list, performance_data)
        
        # Format the report
        report = [f"# Deck Analysis: {deck_name}\n"]
        
        # Strategy section
        strategy = analysis['strategy']
        report.append("## Strategy Overview")
        report.append(f"**Archetype**: {strategy['archetype']}")
        report.append(f"**Play Style**: {', '.join(strategy['play_style'])}")
        report.append(f"**Description**: {strategy['description']}")
        if 'ink_strategy' in strategy:
            report.append(f"**Ink Strategy**: {strategy['ink_strategy']}\n")
        else:
            report.append("\n")
        
        # Key cards section
        report.append("## Key Cards")
        for card in analysis['key_cards'][:5]:  # Show top 5 key cards
            report.append(f"- **{card['name']}** ({card['count']}x): {card['reason']}")
        report.append("\n")
        
        # Synergies section
        report.append("## Notable Synergies")
        if analysis['synergies']:
            for i, synergy in enumerate(analysis['synergies'][:5]):  # Show top 5 synergies
                if synergy['type'] == 'keyword':
                    report.append(f"{i+1}. **{' + '.join(synergy['keywords'])}**: {synergy['synergy']}")
                else:
                    report.append(f"{i+1}. **{' + '.join(synergy['cards'])}**: {synergy['synergy']}")
        else:
            report.append("No significant synergies detected.")
        report.append("\n")
        
        # Deck composition section
        report.append("## Deck Composition")
        report.append("**Card Types**:")
        for card_type, count in analysis['composition']['card_types'].items():
            report.append(f"- {card_type}: {count}")
        
        report.append("\n**Mana Curve**:")
        for cost in sorted([int(c) if c != '8+' else 8 for c in analysis['composition']['mana_curve'].keys()]):
            cost_key = str(cost) if cost != 8 else '8+'
            report.append(f"- {cost_key}: {analysis['composition']['mana_curve'][cost_key]}")
        report.append("\n")
        
        # Performance section (if available)
        if 'performance' in analysis:
            perf = analysis['performance']
            report.append("## Performance Analysis")
            report.append(f"**Overall Win Rate**: {perf['overall_win_rate']:.1%}")
            
            report.append("\n**Matchups**:")
            for deck_name, win_rate in perf['matchups'].items():
                report.append(f"- vs {deck_name}: {win_rate:.1%}")
                
            if perf['strengths']:
                report.append("\n**Strong Against**:")
                for strength in perf['strengths']:
                    report.append(f"- {strength['deck']} ({strength['win_rate']:.1%})")
                    
            if perf['weaknesses']:
                report.append("\n**Weak Against**:")
                for weakness in perf['weaknesses']:
                    report.append(f"- {weakness['deck']} ({weakness['win_rate']:.1%})")
        
        # Join all report sections
        return '\n'.join(report)
