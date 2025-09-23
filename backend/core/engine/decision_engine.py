"""
Decision Engine Module
Makes poker decisions based on calculated factors and EV
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import numpy as np

from .factor_engine import Factors, GameState, FactorEngine


class Action(Enum):
    """Possible poker actions"""
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    RAISE = "raise"
    ALL_IN = "all_in"


@dataclass
class Decision:
    """Represents a poker decision with explanation"""
    action: Action
    amount: float  # For raises
    confidence: float  # 0-1 confidence in decision
    expected_value: float  # Expected value of action
    explanation: str  # Human-readable explanation
    factors_used: Dict[str, float]  # Key factors that influenced decision


class DecisionEngine:
    """Makes decisions based on EV and risk preferences"""

    def __init__(
        self,
        factor_engine: Optional[FactorEngine] = None,
        risk_preference: float = 5.0
    ):
        """
        Initialize decision engine

        Args:
            factor_engine: FactorEngine instance
            risk_preference: Risk slider value (0=conservative, 10=aggressive)
        """
        self.factor_engine = factor_engine or FactorEngine()
        self.risk_preference = risk_preference
        self.alpha = 0.05  # Risk adjustment coefficient

    def make_decision(
        self,
        game_state: GameState,
        opponent_stats: Optional[Dict] = None
    ) -> Decision:
        """
        Make a poker decision based on game state

        Args:
            game_state: Current game state
            opponent_stats: Optional opponent statistics

        Returns:
            Decision object with action and explanation
        """
        # Calculate all factors
        factors = self.factor_engine.calculate_factors(game_state, opponent_stats)

        # Calculate EVs for different actions
        ev_fold = 0  # Folding always has EV of 0
        ev_call = self._calculate_call_ev(game_state, factors)
        ev_raise = self._calculate_raise_ev(game_state, factors)

        # Apply risk adjustment
        risk_adj = self._calculate_risk_adjustment()
        required_equity = factors.pot_odds + risk_adj

        # Decision logic
        decision = self._determine_action(
            game_state, factors, ev_call, ev_raise, required_equity
        )

        # Add confidence based on factor strength
        decision.confidence = self._calculate_confidence(factors, decision.action)

        return decision

    def _calculate_call_ev(self, game_state: GameState, factors: Factors) -> float:
        """Calculate expected value of calling"""
        # Basic EV formula: equity * (pot + call) - call
        pot_after_call = game_state.pot_size + game_state.to_call
        ev = factors.equity * pot_after_call - game_state.to_call

        # Adjust for implied odds on draws
        if factors.outs > 4:  # Significant draw
            ev += factors.implied_odds * game_state.pot_size * 0.5

        return ev

    def _calculate_raise_ev(self, game_state: GameState, factors: Factors) -> float:
        """Calculate expected value of raising"""
        # Estimate raise size (pot-sized bet as default)
        raise_size = game_state.pot_size + game_state.to_call

        # Can't raise more than stack
        raise_size = min(raise_size, game_state.hero_stack)

        # EV = fold_equity * pot + (1 - fold_equity) * equity * final_pot - raise_size
        pot_if_called = game_state.pot_size + raise_size * 2
        ev_if_called = factors.equity * pot_if_called - raise_size

        ev = factors.fold_equity * game_state.pot_size + \
             (1 - factors.fold_equity) * ev_if_called

        # Bonus for position
        if factors.position_factor > 0.7:
            ev *= 1.1

        # Penalty for being out of position
        if factors.position_factor < 0.3:
            ev *= 0.9

        return ev

    def _calculate_risk_adjustment(self) -> float:
        """Calculate risk adjustment based on preference"""
        return self.alpha * (1 - self.risk_preference / 10)

    def _determine_action(
        self,
        game_state: GameState,
        factors: Factors,
        ev_call: float,
        ev_raise: float,
        required_equity: float
    ) -> Decision:
        """Determine the best action based on EVs and game state"""

        # Check if we can check
        can_check = game_state.to_call == 0

        # If we can check and have weak hand, check
        if can_check and factors.hand_strength < 0.3:
            return Decision(
                action=Action.CHECK,
                amount=0,
                confidence=0.7,
                expected_value=0,
                explanation="Checking with weak hand to see free card",
                factors_used={
                    'hand_strength': factors.hand_strength,
                    'equity': factors.equity
                }
            )

        # Strong hand logic
        if factors.hand_strength > 0.8 or factors.equity > 0.85:
            # Very strong hand - raise for value
            raise_amount = self._calculate_raise_amount(game_state, factors, 'value')

            return Decision(
                action=Action.RAISE if raise_amount < game_state.hero_stack else Action.ALL_IN,
                amount=raise_amount,
                confidence=0.9,
                expected_value=ev_raise,
                explanation=f"Raising for value with strong hand (equity: {factors.equity:.1%})",
                factors_used={
                    'hand_strength': factors.hand_strength,
                    'equity': factors.equity,
                    'position': factors.position_factor
                }
            )

        # Drawing hand logic
        if factors.outs >= 8 and factors.street < 3:  # Good draw, not on river
            if factors.implied_odds < factors.pot_odds * 0.8:
                # Good implied odds - call or raise
                if factors.fold_equity > 0.4 and ev_raise > ev_call:
                    raise_amount = self._calculate_raise_amount(game_state, factors, 'bluff')
                    return Decision(
                        action=Action.RAISE,
                        amount=raise_amount,
                        confidence=0.7,
                        expected_value=ev_raise,
                        explanation=f"Semi-bluffing with {factors.outs} outs (fold equity: {factors.fold_equity:.1%})",
                        factors_used={
                            'outs': factors.outs,
                            'fold_equity': factors.fold_equity,
                            'implied_odds': factors.implied_odds
                        }
                    )
                else:
                    return Decision(
                        action=Action.CALL,
                        amount=game_state.to_call,
                        confidence=0.75,
                        expected_value=ev_call,
                        explanation=f"Calling with draw ({factors.outs} outs, implied odds: {factors.implied_odds:.1%})",
                        factors_used={
                            'outs': factors.outs,
                            'implied_odds': factors.implied_odds,
                            'pot_odds': factors.pot_odds
                        }
                    )

        # Standard equity-based decision
        if factors.equity >= required_equity:
            # Decide between call and raise
            if ev_raise > ev_call * 1.2 and factors.stack_to_pot_ratio > 2:
                # Raise is significantly better and we have chips to play
                raise_amount = self._calculate_raise_amount(game_state, factors, 'standard')

                return Decision(
                    action=Action.RAISE,
                    amount=raise_amount,
                    confidence=0.7,
                    expected_value=ev_raise,
                    explanation=f"Raising with {factors.equity:.1%} equity (EV: ${ev_raise:.2f})",
                    factors_used={
                        'equity': factors.equity,
                        'ev_raise': ev_raise,
                        'position': factors.position_factor
                    }
                )
            else:
                # Call
                return Decision(
                    action=Action.CALL if game_state.to_call > 0 else Action.CHECK,
                    amount=game_state.to_call,
                    confidence=0.75,
                    expected_value=ev_call,
                    explanation=f"Calling with {factors.equity:.1%} equity vs required {required_equity:.1%}",
                    factors_used={
                        'equity': factors.equity,
                        'pot_odds': factors.pot_odds,
                        'required_equity': required_equity
                    }
                )

        # Not enough equity - fold or check
        if can_check:
            return Decision(
                action=Action.CHECK,
                amount=0,
                confidence=0.8,
                expected_value=0,
                explanation=f"Checking with insufficient equity ({factors.equity:.1%} < {required_equity:.1%})",
                factors_used={
                    'equity': factors.equity,
                    'required_equity': required_equity
                }
            )
        else:
            return Decision(
                action=Action.FOLD,
                amount=0,
                confidence=0.85,
                expected_value=0,
                explanation=f"Folding - equity {factors.equity:.1%} below required {required_equity:.1%}",
                factors_used={
                    'equity': factors.equity,
                    'pot_odds': factors.pot_odds,
                    'required_equity': required_equity
                }
            )

    def _calculate_raise_amount(
        self,
        game_state: GameState,
        factors: Factors,
        raise_type: str
    ) -> float:
        """Calculate appropriate raise size"""
        pot = game_state.pot_size + game_state.to_call

        if raise_type == 'value':
            # Value bet sizing - typically 50-100% pot
            multiplier = 0.5 + factors.board_wetness * 0.5
        elif raise_type == 'bluff':
            # Bluff sizing - typically 60-75% pot
            multiplier = 0.6 + factors.fold_equity * 0.15
        else:
            # Standard sizing - 66% pot
            multiplier = 0.66

        raise_amount = pot * multiplier + game_state.to_call

        # Adjust for stack sizes
        effective_stack = min(game_state.hero_stack, game_state.villain_stack)

        # Don't raise too small
        min_raise = game_state.to_call * 2.5
        raise_amount = max(raise_amount, min_raise)

        # Don't raise more than effective stack
        raise_amount = min(raise_amount, effective_stack)

        return round(raise_amount, 2)

    def _calculate_confidence(self, factors: Factors, action: Action) -> float:
        """Calculate confidence in the decision"""
        base_confidence = 0.5

        # Strong indicators increase confidence
        if factors.equity > 0.8:
            base_confidence += 0.3
        elif factors.equity > 0.6:
            base_confidence += 0.2
        elif factors.equity > 0.4:
            base_confidence += 0.1

        # Position advantage increases confidence
        base_confidence += factors.position_factor * 0.1

        # Clear pot odds situation increases confidence
        if action == Action.FOLD and factors.equity < factors.pot_odds * 0.8:
            base_confidence += 0.2
        elif action in [Action.CALL, Action.RAISE] and factors.equity > factors.pot_odds * 1.2:
            base_confidence += 0.2

        return min(0.95, base_confidence)

    def set_risk_preference(self, risk_level: float):
        """Update risk preference (0-10)"""
        self.risk_preference = max(0, min(10, risk_level))

    def get_action_distribution(
        self,
        game_state: GameState,
        factors: Factors
    ) -> Dict[Action, float]:
        """
        Get probability distribution over actions (for ML training)

        Args:
            game_state: Current game state
            factors: Calculated factors

        Returns:
            Dictionary mapping actions to probabilities
        """
        # Calculate EVs
        ev_fold = 0
        ev_call = self._calculate_call_ev(game_state, factors)
        ev_raise = self._calculate_raise_ev(game_state, factors)

        # Convert EVs to probabilities using softmax
        evs = np.array([ev_fold, ev_call, ev_raise])

        # Add noise to prevent overflow
        evs = evs / (np.std(evs) + 1e-8)

        # Softmax with temperature
        temperature = 1.0
        exp_evs = np.exp(evs / temperature)
        probs = exp_evs / np.sum(exp_evs)

        # Map to actions
        can_check = game_state.to_call == 0

        if can_check:
            return {
                Action.CHECK: probs[0] + probs[1] * 0.5,  # Combine fold and call probs
                Action.RAISE: probs[2],
            }
        else:
            return {
                Action.FOLD: probs[0],
                Action.CALL: probs[1],
                Action.RAISE: probs[2],
            }