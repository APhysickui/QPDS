"""Tests for FactorEngine heuristics and factor outputs."""

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.engine import FactorEngine, GameState, Position, Street
from backend.core.evaluator import Card


class StubEquityCalculator:
    """Simple stub that returns a fixed equity value for deterministic tests."""

    def __init__(self, equity: float = 0.5):
        self._equity = equity

    def calculate_equity(self, **kwargs):
        return self._equity


@pytest.fixture
def engine():
    """Provide a FactorEngine with deterministic equity calculations."""
    return FactorEngine(equity_calculator=StubEquityCalculator(0.55))


def make_state(hero, board, street, position=Position.BTN):
    """Helper to build a GameState for tests."""
    return GameState(
        hero_cards=[Card.from_string(card) for card in hero],
        board=[Card.from_string(card) for card in board],
        pot_size=120,
        to_call=20,
        hero_stack=500,
        villain_stack=450,
        hero_position=position,
        street=street
    )


def test_preflop_pair_has_high_strength(engine):
    """Pocket aces preflop should score as a very strong hand."""
    state = make_state(['As', 'Ah'], [], Street.PREFLOP)
    factors = engine.calculate_factors(state)
    assert factors.hand_strength > 0.9


def test_preflop_trash_hand_scores_lower(engine):
    """Disconnected offsuit low cards should have modest strength."""
    state = make_state(['7d', '2c'], [], Street.PREFLOP, position=Position.UTG)
    factors = engine.calculate_factors(state)
    assert factors.hand_strength < 0.45


def test_pot_odds_matches_formula(engine):
    """Pot odds factor should equal call / (pot + call)."""
    state = GameState(
        hero_cards=[Card.from_string('Kd'), Card.from_string('Qs')],
        board=[],
        pot_size=150,
        to_call=30,
        hero_stack=600,
        villain_stack=400,
        hero_position=Position.CO,
        street=Street.PREFLOP
    )
    factors = engine.calculate_factors(state)
    expected = 30 / (150 + 30)
    assert pytest.approx(factors.pot_odds, rel=1e-3) == expected


def test_flush_draw_outs_counted(engine):
    """Four spades on flop should identify nine flush outs."""
    state = make_state(['As', 'Ks'], ['2s', '7s', '9d'], Street.FLOP)
    factors = engine.calculate_factors(state)
    assert factors.outs >= 9
    assert factors.draw_probability > 0
