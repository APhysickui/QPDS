"""
Test suite for HandEvaluator
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.core.evaluator import HandEvaluator, Card, HandRank


class TestHandEvaluator:
    """Test cases for HandEvaluator"""

    def setup_method(self):
        """Set up test fixtures"""
        self.evaluator = HandEvaluator()

    def test_royal_flush(self):
        """Test royal flush detection"""
        cards = [
            Card.from_string('As'),
            Card.from_string('Ks'),
            Card.from_string('Qs'),
            Card.from_string('Js'),
            Card.from_string('Ts')
        ]
        rank, _ = self.evaluator.evaluate(cards)
        assert rank == HandRank.ROYAL_FLUSH

    def test_straight_flush(self):
        """Test straight flush detection"""
        cards = [
            Card.from_string('9h'),
            Card.from_string('8h'),
            Card.from_string('7h'),
            Card.from_string('6h'),
            Card.from_string('5h')
        ]
        rank, values = self.evaluator.evaluate(cards)
        assert rank == HandRank.STRAIGHT_FLUSH
        assert values[0] == 9

    def test_four_of_a_kind(self):
        """Test four of a kind detection"""
        cards = [
            Card.from_string('Ah'),
            Card.from_string('As'),
            Card.from_string('Ad'),
            Card.from_string('Ac'),
            Card.from_string('Kh')
        ]
        rank, values = self.evaluator.evaluate(cards)
        assert rank == HandRank.FOUR_OF_A_KIND
        assert values[0] == 14  # Aces

    def test_full_house(self):
        """Test full house detection"""
        cards = [
            Card.from_string('Kh'),
            Card.from_string('Ks'),
            Card.from_string('Kd'),
            Card.from_string('7h'),
            Card.from_string('7s')
        ]
        rank, values = self.evaluator.evaluate(cards)
        assert rank == HandRank.FULL_HOUSE
        assert values[0] == 13  # Kings
        assert values[1] == 7   # Sevens

    def test_flush(self):
        """Test flush detection"""
        cards = [
            Card.from_string('Ah'),
            Card.from_string('Kh'),
            Card.from_string('Qh'),
            Card.from_string('9h'),
            Card.from_string('2h')
        ]
        rank, _ = self.evaluator.evaluate(cards)
        assert rank == HandRank.FLUSH

    def test_straight(self):
        """Test straight detection"""
        cards = [
            Card.from_string('9h'),
            Card.from_string('8d'),
            Card.from_string('7s'),
            Card.from_string('6c'),
            Card.from_string('5h')
        ]
        rank, values = self.evaluator.evaluate(cards)
        assert rank == HandRank.STRAIGHT
        assert values[0] == 9

    def test_wheel_straight(self):
        """Test A-2-3-4-5 straight (wheel)"""
        cards = [
            Card.from_string('Ah'),
            Card.from_string('2d'),
            Card.from_string('3s'),
            Card.from_string('4c'),
            Card.from_string('5h')
        ]
        rank, values = self.evaluator.evaluate(cards)
        assert rank == HandRank.STRAIGHT
        assert values[0] == 5  # Wheel high card is 5

    def test_three_of_a_kind(self):
        """Test three of a kind detection"""
        cards = [
            Card.from_string('Qh'),
            Card.from_string('Qs'),
            Card.from_string('Qd'),
            Card.from_string('7h'),
            Card.from_string('2s')
        ]
        rank, values = self.evaluator.evaluate(cards)
        assert rank == HandRank.THREE_OF_A_KIND
        assert values[0] == 12  # Queens

    def test_two_pair(self):
        """Test two pair detection"""
        cards = [
            Card.from_string('Jh'),
            Card.from_string('Js'),
            Card.from_string('9d'),
            Card.from_string('9h'),
            Card.from_string('2s')
        ]
        rank, values = self.evaluator.evaluate(cards)
        assert rank == HandRank.TWO_PAIR
        assert values[0] == 11  # Jacks
        assert values[1] == 9   # Nines

    def test_one_pair(self):
        """Test one pair detection"""
        cards = [
            Card.from_string('Th'),
            Card.from_string('Ts'),
            Card.from_string('8d'),
            Card.from_string('6h'),
            Card.from_string('2s')
        ]
        rank, values = self.evaluator.evaluate(cards)
        assert rank == HandRank.ONE_PAIR
        assert values[0] == 10  # Tens

    def test_high_card(self):
        """Test high card detection"""
        cards = [
            Card.from_string('Ah'),
            Card.from_string('Ks'),
            Card.from_string('Jd'),
            Card.from_string('9h'),
            Card.from_string('2s')
        ]
        rank, values = self.evaluator.evaluate(cards)
        assert rank == HandRank.HIGH_CARD
        assert values[0] == 14  # Ace high

    def test_seven_cards(self):
        """Test evaluation with 7 cards (Texas Hold'em scenario)"""
        cards = [
            Card.from_string('As'),
            Card.from_string('Ks'),  # Hole cards
            Card.from_string('Qs'),
            Card.from_string('Js'),
            Card.from_string('Ts'),  # Board makes royal flush
            Card.from_string('9h'),
            Card.from_string('2d')
        ]
        rank, _ = self.evaluator.evaluate(cards)
        assert rank == HandRank.ROYAL_FLUSH

    def test_compare_hands(self):
        """Test hand comparison"""
        hand1 = [
            Card.from_string('Ah'),
            Card.from_string('As'),
            Card.from_string('Kd'),
            Card.from_string('Kh'),
            Card.from_string('2s')
        ]  # Two pair, Aces and Kings

        hand2 = [
            Card.from_string('Qh'),
            Card.from_string('Qs'),
            Card.from_string('Qd'),
            Card.from_string('7h'),
            Card.from_string('2c')
        ]  # Three Queens

        result = self.evaluator.compare_hands(hand1, hand2)
        assert result < 0  # hand2 wins

    def test_hand_strength(self):
        """Test hand strength calculation"""
        cards = [
            Card.from_string('As'),
            Card.from_string('Ks'),
            Card.from_string('Qs'),
            Card.from_string('Js'),
            Card.from_string('Ts')
        ]
        strength = self.evaluator.get_hand_strength(cards)
        assert strength > 0.99  # Royal flush should be near maximum strength


if __name__ == '__main__':
    pytest.main([__file__])