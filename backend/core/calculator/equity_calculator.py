"""
Equity Calculator Module
Calculates win probability using Monte Carlo simulation and exact enumeration
"""

import random
from typing import List, Tuple, Dict, Optional, Set
from itertools import combinations, product
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import hashlib
import json

from ..evaluator import HandEvaluator, Card


class Range:
    """Represents a range of hands for an opponent"""

    def __init__(self, range_str: Optional[str] = None):
        """
        Initialize a range
        Args:
            range_str: String representation of range (e.g., "AA,KK,QQ,AKs")
        """
        self.hands = set()
        if range_str:
            self._parse_range(range_str)

    def _parse_range(self, range_str: str):
        """Parse range string into specific hands"""
        parts = range_str.replace(" ", "").split(",")

        for part in parts:
            if not part:
                continue

            # Handle pocket pairs (e.g., "AA", "KK", "22+", "77-99")
            if len(part) == 2 and part[0] == part[1]:
                self._add_pocket_pair(part)
            elif "+" in part:  # e.g., "77+"
                self._add_pocket_pairs_plus(part)
            elif "-" in part and len(part.split("-")[0]) == 2:  # e.g., "77-99"
                self._add_pocket_pairs_range(part)
            # Handle suited/offsuit hands
            elif len(part) >= 2:
                self._add_non_pair(part)

    def _add_pocket_pair(self, pair_str: str):
        """Add a specific pocket pair"""
        rank = self._rank_from_char(pair_str[0])
        suits = ['s', 'h', 'd', 'c']
        for s1, s2 in combinations(suits, 2):
            self.hands.add((Card(rank, s1), Card(rank, s2)))

    def _add_pocket_pairs_plus(self, range_str: str):
        """Add pocket pairs from specified rank and higher"""
        start_rank = self._rank_from_char(range_str[0])
        for rank in range(start_rank, 15):
            rank_char = self._char_from_rank(rank)
            self._add_pocket_pair(rank_char + rank_char)

    def _add_pocket_pairs_range(self, range_str: str):
        """Add pocket pairs in a range (e.g., '77-99')"""
        parts = range_str.split('-')
        start_rank = self._rank_from_char(parts[0][0])
        end_rank = self._rank_from_char(parts[1][0])

        for rank in range(min(start_rank, end_rank), max(start_rank, end_rank) + 1):
            rank_char = self._char_from_rank(rank)
            self._add_pocket_pair(rank_char + rank_char)

    def _add_non_pair(self, hand_str: str):
        """Add non-pair hands (suited/offsuit)"""
        rank1 = self._rank_from_char(hand_str[0])
        rank2 = self._rank_from_char(hand_str[1])

        if rank1 == rank2:
            return  # Skip pairs

        is_suited = len(hand_str) > 2 and hand_str[2] == 's'
        is_offsuit = len(hand_str) > 2 and hand_str[2] == 'o'

        suits = ['s', 'h', 'd', 'c']

        if is_suited or (not is_offsuit and len(hand_str) == 2):
            # Add suited combinations
            for suit in suits:
                self.hands.add((Card(rank1, suit), Card(rank2, suit)))

        if is_offsuit or len(hand_str) == 2:
            # Add offsuit combinations
            for s1, s2 in product(suits, repeat=2):
                if s1 != s2:
                    self.hands.add((Card(rank1, s1), Card(rank2, s2)))

    def _rank_from_char(self, char: str) -> int:
        """Convert character to rank"""
        rank_map = {
            '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
            '8': 8, '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
        }
        return rank_map.get(char.upper(), 0)

    def _char_from_rank(self, rank: int) -> str:
        """Convert rank to character"""
        char_map = {
            2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7',
            8: '8', 9: '9', 10: 'T', 11: 'J', 12: 'Q', 13: 'K', 14: 'A'
        }
        return char_map.get(rank, '')

    def get_hands(self) -> Set[Tuple[Card, Card]]:
        """Get all hands in the range"""
        return self.hands

    def remove_conflicting_cards(self, cards: List[Card]):
        """Remove hands that conflict with given cards"""
        filtered_hands = set()
        for hand in self.hands:
            if not any(card in hand for card in cards):
                filtered_hands.add(hand)
        self.hands = filtered_hands


class EquityCalculator:
    """Calculates win equity using various methods"""

    def __init__(self, evaluator: Optional[HandEvaluator] = None):
        """
        Initialize the calculator
        Args:
            evaluator: HandEvaluator instance (creates new if not provided)
        """
        self.evaluator = evaluator or HandEvaluator()
        self.cache = {}
        self.deck = self._create_deck()

    def _create_deck(self) -> List[Card]:
        """Create a standard 52-card deck"""
        deck = []
        for rank in range(2, 15):
            for suit in ['s', 'h', 'd', 'c']:
                deck.append(Card(rank, suit))
        return deck

    def calculate_equity(
        self,
        hero_cards: List[Card],
        villain_range: Optional[Range] = None,
        board: Optional[List[Card]] = None,
        num_opponents: int = 1,
        iterations: int = 10000,
        method: str = 'monte_carlo'
    ) -> float:
        """
        Calculate hero's equity against opponent range

        Args:
            hero_cards: Hero's hole cards
            villain_range: Opponent's range (if None, assumes random)
            board: Community cards (can be empty)
            num_opponents: Number of opponents
            iterations: Number of Monte Carlo iterations
            method: 'monte_carlo' or 'exact'

        Returns:
            Win probability (0-1)
        """
        if board is None:
            board = []

        # Create cache key
        cache_key = self._create_cache_key(hero_cards, villain_range, board, num_opponents)
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Remove known cards from deck
        known_cards = set(hero_cards + board)
        available_deck = [card for card in self.deck if card not in known_cards]

        if method == 'exact' and self._can_use_exact(villain_range, len(board), num_opponents):
            equity = self._calculate_exact_equity(
                hero_cards, villain_range, board, available_deck
            )
        else:
            equity = self._calculate_monte_carlo_equity(
                hero_cards, villain_range, board, available_deck,
                num_opponents, iterations
            )

        # Cache the result
        self.cache[cache_key] = equity
        return equity

    def _can_use_exact(self, villain_range: Optional[Range], board_size: int, num_opponents: int) -> bool:
        """Check if exact calculation is feasible"""
        # Only use exact for single opponent with small range and complete board
        if num_opponents != 1 or board_size < 3:
            return False

        if villain_range is None:
            return False

        return len(villain_range.get_hands()) < 100

    def _calculate_exact_equity(
        self,
        hero_cards: List[Card],
        villain_range: Range,
        board: List[Card],
        available_deck: List[Card]
    ) -> float:
        """Calculate exact equity by enumerating all possibilities"""
        villain_range.remove_conflicting_cards(hero_cards + board)
        villain_hands = list(villain_range.get_hands())

        if not villain_hands:
            return 1.0

        wins = 0
        ties = 0
        total = 0

        cards_needed = 5 - len(board)

        if cards_needed == 0:
            # Board is complete, just compare hands
            hero_hand = hero_cards + board
            for villain_hand in villain_hands:
                villain_full = list(villain_hand) + board
                result = self.evaluator.compare_hands(hero_hand, villain_full)

                if result > 0:
                    wins += 1
                elif result == 0:
                    ties += 1
                total += 1
        else:
            # Need to enumerate possible boards
            for villain_hand in villain_hands:
                villain_cards = list(villain_hand)

                # Get remaining cards
                used_cards = set(hero_cards + villain_cards + board)
                remaining = [c for c in available_deck if c not in used_cards]

                for board_completion in combinations(remaining, cards_needed):
                    full_board = board + list(board_completion)
                    hero_full = hero_cards + full_board
                    villain_full = villain_cards + full_board

                    result = self.evaluator.compare_hands(hero_full, villain_full)

                    if result > 0:
                        wins += 1
                    elif result == 0:
                        ties += 1
                    total += 1

        if total == 0:
            return 0.5

        return (wins + ties * 0.5) / total

    def _calculate_monte_carlo_equity(
        self,
        hero_cards: List[Card],
        villain_range: Optional[Range],
        board: List[Card],
        available_deck: List[Card],
        num_opponents: int,
        iterations: int
    ) -> float:
        """Calculate equity using Monte Carlo simulation"""
        wins = 0
        ties = 0

        # Filter villain range if provided
        if villain_range:
            villain_range.remove_conflicting_cards(hero_cards + board)
            villain_hands = list(villain_range.get_hands())
            if not villain_hands:
                return 1.0
        else:
            villain_hands = None

        for _ in range(iterations):
            # Deal random board completion
            sim_deck = available_deck.copy()
            random.shuffle(sim_deck)

            cards_needed = 5 - len(board)
            board_completion = sim_deck[:cards_needed]
            full_board = board + board_completion

            hero_hand = hero_cards + full_board

            # Deal villain hands
            remaining_deck = sim_deck[cards_needed:]
            villain_hands_sim = []

            for opp in range(num_opponents):
                if villain_hands:
                    # Select from range
                    valid_hands = [h for h in villain_hands
                                  if all(c not in board_completion for c in h)]
                    if not valid_hands:
                        continue
                    villain_hand = random.choice(valid_hands)
                else:
                    # Random villain hand
                    if len(remaining_deck) < 2:
                        continue
                    villain_hand = remaining_deck[:2]
                    remaining_deck = remaining_deck[2:]

                villain_hands_sim.append(list(villain_hand) + full_board)

            if not villain_hands_sim:
                wins += 1
                continue

            # Evaluate hands
            hero_beats_all = True
            hero_ties_best = False

            for villain_hand in villain_hands_sim:
                result = self.evaluator.compare_hands(hero_hand, villain_hand)
                if result < 0:
                    hero_beats_all = False
                    break
                elif result == 0:
                    hero_ties_best = True
                    hero_beats_all = False

            if hero_beats_all:
                wins += 1
            elif hero_ties_best:
                ties += 1

        return (wins + ties * 0.5) / iterations

    def _create_cache_key(
        self,
        hero_cards: List[Card],
        villain_range: Optional[Range],
        board: List[Card],
        num_opponents: int
    ) -> str:
        """Create a cache key for the equity calculation"""
        hero_str = ''.join(sorted(str(c) for c in hero_cards))
        board_str = ''.join(sorted(str(c) for c in board))
        range_str = str(sorted(villain_range.get_hands())) if villain_range else "random"

        key_str = f"{hero_str}|{board_str}|{range_str}|{num_opponents}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def calculate_pot_odds(self, pot_size: float, bet_size: float) -> float:
        """
        Calculate pot odds
        Args:
            pot_size: Current pot size
            bet_size: Size of bet to call
        Returns:
            Required equity to call (0-1)
        """
        if pot_size + bet_size == 0:
            return 0
        return bet_size / (pot_size + bet_size)

    def calculate_implied_odds(
        self,
        pot_size: float,
        bet_size: float,
        future_bets: float,
        probability_of_hitting: float
    ) -> float:
        """
        Calculate implied odds
        Args:
            pot_size: Current pot size
            bet_size: Size of bet to call
            future_bets: Expected future bets if we hit
            probability_of_hitting: Probability of hitting our draw
        Returns:
            Adjusted required equity considering future bets
        """
        effective_pot = pot_size + future_bets * probability_of_hitting
        return bet_size / (effective_pot + bet_size)