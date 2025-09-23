"""
Test suite for EquityCalculator
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.core.calculator import EquityCalculator, Range
from backend.core.evaluator import Card


class TestEquityCalculator:
    """Test cases for EquityCalculator"""

    def setup_method(self):
        """Set up test fixtures"""
        self.calculator = EquityCalculator()

    def test_pot_odds_calculation(self):
        """Test pot odds calculation"""
        pot_odds = self.calculator.calculate_pot_odds(100, 20)
        assert abs(pot_odds - 0.1667) < 0.01  # 20/120 = 16.67%

    def test_aa_vs_kk_preflop(self):
        """Test AA vs KK preflop (classic scenario)"""
        hero = [Card.from_string('As'), Card.from_string('Ah')]
        villain_range = Range('KK')

        equity = self.calculator.calculate_equity(
            hero_cards=hero,
            villain_range=villain_range,
            iterations=5000
        )

        # AA should win about 80-82% vs KK preflop
        assert 0.78 < equity < 0.84

    def test_flush_draw_equity(self):
        """Test flush draw on flop"""
        hero = [Card.from_string('As'), Card.from_string('Ks')]
        board = [Card.from_string('Qs'), Card.from_string('7s'), Card.from_string('2d')]

        # Assume villain has top pair
        villain_range = Range('QQ,AQ,KQ,QJ,QT')

        equity = self.calculator.calculate_equity(
            hero_cards=hero,
            villain_range=villain_range,
            board=board,
            iterations=5000
        )

        # Flush draw should have about 35-40% equity
        assert 0.30 < equity < 0.45

    def test_set_vs_overpair(self):
        """Test set vs overpair on flop"""
        hero = [Card.from_string('7h'), Card.from_string('7d')]
        board = [Card.from_string('7s'), Card.from_string('Qc'), Card.from_string('2h')]

        villain_range = Range('AA,KK')

        equity = self.calculator.calculate_equity(
            hero_cards=hero,
            villain_range=villain_range,
            board=board,
            iterations=5000
        )

        # Set should win about 88-92% vs overpair
        assert equity > 0.85

    def test_multiway_equity(self):
        """Test equity in multiway pot"""
        hero = [Card.from_string('As'), Card.from_string('Ks')]

        equity = self.calculator.calculate_equity(
            hero_cards=hero,
            num_opponents=3,
            iterations=5000
        )

        # AKs should have lower equity against 3 opponents
        assert equity < 0.35


class TestRange:
    """Test cases for Range parsing"""

    def test_pocket_pair_range(self):
        """Test pocket pair range parsing"""
        range_obj = Range('AA')
        hands = range_obj.get_hands()

        # AA has 6 combinations (C(4,2) = 6)
        assert len(hands) == 6

    def test_plus_range(self):
        """Test plus range parsing (e.g., 77+)"""
        range_obj = Range('QQ+')
        hands = range_obj.get_hands()

        # QQ+ includes QQ, KK, AA = 3 * 6 = 18 combinations
        assert len(hands) == 18

    def test_suited_range(self):
        """Test suited hand parsing"""
        range_obj = Range('AKs')
        hands = range_obj.get_hands()

        # AKs has 4 combinations (one per suit)
        assert len(hands) == 4

    def test_offsuit_range(self):
        """Test offsuit hand parsing"""
        range_obj = Range('AKo')
        hands = range_obj.get_hands()

        # AKo has 12 combinations (4 * 3)
        assert len(hands) == 12

    def test_mixed_range(self):
        """Test parsing mixed range"""
        range_obj = Range('AA,KK,AKs')
        hands = range_obj.get_hands()

        # AA (6) + KK (6) + AKs (4) = 16 combinations
        assert len(hands) == 16

    def test_range_removal(self):
        """Test removing conflicting cards from range"""
        range_obj = Range('AA,KK,AKs')
        blocker = [Card.from_string('As')]

        range_obj.remove_conflicting_cards(blocker)
        hands = range_obj.get_hands()

        # Should remove hands containing As
        # AA loses 3 combos (AsAh, AsAd, AsAc)
        # AKs loses 1 combo (AsKs)
        # Total: 16 - 4 = 12
        assert len(hands) == 12


if __name__ == '__main__':
    pytest.main([__file__])