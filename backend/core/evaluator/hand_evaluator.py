"""
Hand Evaluator Module
Provides fast poker hand evaluation and ranking
"""

from typing import List, Tuple, Dict, Optional
from enum import Enum
import numpy as np
from itertools import combinations
import hashlib
import json


class Rank(Enum):
    """Card ranks"""
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14


class Suit(Enum):
    """Card suits"""
    SPADES = 's'
    HEARTS = 'h'
    DIAMONDS = 'd'
    CLUBS = 'c'


class HandRank(Enum):
    """Poker hand rankings"""
    HIGH_CARD = 1
    ONE_PAIR = 2
    TWO_PAIR = 3
    THREE_OF_A_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    FOUR_OF_A_KIND = 8
    STRAIGHT_FLUSH = 9
    ROYAL_FLUSH = 10


class Card:
    """Represents a playing card"""

    RANK_SYMBOLS = {
        2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7',
        8: '8', 9: '9', 10: 'T', 11: 'J', 12: 'Q', 13: 'K', 14: 'A'
    }

    def __init__(self, rank: int, suit: str):
        """
        Initialize a card
        Args:
            rank: Card rank (2-14)
            suit: Card suit ('s', 'h', 'd', 'c')
        """
        self.rank = rank
        self.suit = suit

    @classmethod
    def from_string(cls, card_str: str) -> 'Card':
        """
        Create a card from string representation
        Args:
            card_str: String like 'As', 'Kh', '2d', 'Tc'
        """
        rank_char = card_str[0]
        suit_char = card_str[1].lower()

        rank_map = {
            '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
            '8': 8, '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
        }

        return cls(rank_map[rank_char.upper()], suit_char)

    def __str__(self):
        return f"{self.RANK_SYMBOLS[self.rank]}{self.suit}"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.rank == other.rank and self.suit == other.suit

    def __hash__(self):
        return hash((self.rank, self.suit))


class HandEvaluator:
    """Fast poker hand evaluator"""

    def __init__(self):
        """Initialize the evaluator with lookup tables"""
        self.cache = {}
        self.prime_map = self._init_prime_map()

    def _init_prime_map(self) -> Dict[int, int]:
        """Initialize prime number mapping for ranks"""
        primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41]
        return {rank: prime for rank, prime in zip(range(2, 15), primes)}

    def evaluate(self, cards: List[Card]) -> Tuple[HandRank, List[int]]:
        """
        Evaluate a poker hand
        Args:
            cards: List of Card objects (5-7 cards)
        Returns:
            Tuple of (HandRank, tiebreaker values)
        """
        if len(cards) < 5:
            raise ValueError("Need at least 5 cards to evaluate")

        # If more than 5 cards, find best 5-card combination
        if len(cards) > 5:
            best_rank = HandRank.HIGH_CARD
            best_values = []

            for combo in combinations(cards, 5):
                rank, values = self._evaluate_5_cards(list(combo))
                if rank.value > best_rank.value or (rank == best_rank and values > best_values):
                    best_rank = rank
                    best_values = values

            return best_rank, best_values

        return self._evaluate_5_cards(cards)

    def _evaluate_5_cards(self, cards: List[Card]) -> Tuple[HandRank, List[int]]:
        """Evaluate exactly 5 cards"""
        # Count ranks and suits
        ranks = [card.rank for card in cards]
        suits = [card.suit for card in cards]

        rank_counts = {}
        for rank in ranks:
            rank_counts[rank] = rank_counts.get(rank, 0) + 1

        # Sort by count then rank
        sorted_counts = sorted(rank_counts.items(), key=lambda x: (x[1], x[0]), reverse=True)
        counts = [count for _, count in sorted_counts]
        unique_ranks = [rank for rank, _ in sorted_counts]

        # Check for flush
        is_flush = len(set(suits)) == 1

        # Check for straight
        is_straight, straight_high = self._check_straight(sorted(ranks))

        # Determine hand rank
        if is_straight and is_flush:
            if straight_high == 14:  # Ace high straight
                return HandRank.ROYAL_FLUSH, [14]
            return HandRank.STRAIGHT_FLUSH, [straight_high]

        if counts == [4, 1]:
            return HandRank.FOUR_OF_A_KIND, unique_ranks[:2]

        if counts == [3, 2]:
            return HandRank.FULL_HOUSE, unique_ranks[:2]

        if is_flush:
            return HandRank.FLUSH, sorted(ranks, reverse=True)

        if is_straight:
            return HandRank.STRAIGHT, [straight_high]

        if counts == [3, 1, 1]:
            return HandRank.THREE_OF_A_KIND, unique_ranks

        if counts == [2, 2, 1]:
            return HandRank.TWO_PAIR, unique_ranks

        if counts == [2, 1, 1, 1]:
            return HandRank.ONE_PAIR, unique_ranks

        return HandRank.HIGH_CARD, sorted(ranks, reverse=True)

    def _check_straight(self, sorted_ranks: List[int]) -> Tuple[bool, int]:
        """Check if cards form a straight"""
        # Regular straight check
        if sorted_ranks == list(range(sorted_ranks[0], sorted_ranks[0] + 5)):
            return True, sorted_ranks[-1]

        # Check for A-2-3-4-5 (wheel)
        if sorted_ranks == [2, 3, 4, 5, 14]:
            return True, 5

        return False, 0

    def get_hand_strength(self, cards: List[Card]) -> float:
        """
        Get normalized hand strength (0-1)
        Args:
            cards: List of Card objects
        Returns:
            Float between 0 and 1 representing hand strength
        """
        rank, values = self.evaluate(cards)

        # Simple scoring system
        base_score = rank.value * 1000000

        # Add tiebreaker values
        for i, value in enumerate(values[:5]):
            base_score += value * (10000 // (10 ** i))

        # Normalize to 0-1 range
        max_score = 10000000  # Royal flush
        return min(base_score / max_score, 1.0)

    def compare_hands(self, hand1: List[Card], hand2: List[Card]) -> int:
        """
        Compare two poker hands
        Args:
            hand1: First hand
            hand2: Second hand
        Returns:
            1 if hand1 wins, -1 if hand2 wins, 0 if tie
        """
        rank1, values1 = self.evaluate(hand1)
        rank2, values2 = self.evaluate(hand2)

        if rank1.value > rank2.value:
            return 1
        elif rank1.value < rank2.value:
            return -1

        # Same rank, compare tiebreakers
        for v1, v2 in zip(values1, values2):
            if v1 > v2:
                return 1
            elif v1 < v2:
                return -1

        return 0

    def get_outs(self, hole_cards: List[Card], board: List[Card]) -> Dict[str, int]:
        """
        Calculate outs for various draws
        Args:
            hole_cards: Player's hole cards
            board: Community cards
        Returns:
            Dictionary of draw types and number of outs
        """
        all_cards = hole_cards + board
        outs = {
            'flush_draw': 0,
            'straight_draw': 0,
            'two_pair': 0,
            'trips': 0
        }

        # Flush draws
        suits = [card.suit for card in all_cards]
        for suit in set(suits):
            if suits.count(suit) == 4:
                outs['flush_draw'] = 9  # 13 - 4 = 9 remaining

        # Straight draws (simplified)
        ranks = sorted([card.rank for card in all_cards])
        unique_ranks = sorted(set(ranks))

        # Check for open-ended straight draws
        for i in range(len(unique_ranks) - 3):
            if unique_ranks[i+3] - unique_ranks[i] == 3:
                outs['straight_draw'] = 8  # 4 cards on each end
                break

        # Check for gutshot
        if outs['straight_draw'] == 0:
            for i in range(len(unique_ranks) - 3):
                if unique_ranks[i+3] - unique_ranks[i] == 4:
                    outs['straight_draw'] = 4  # 4 cards for the gap
                    break

        return outs