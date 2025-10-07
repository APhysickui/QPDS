"""
Factor Engine Module
Calculates all quantitative factors for decision making
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict, field
import numpy as np
from enum import Enum

from ..evaluator import HandEvaluator, Card
from ..calculator import EquityCalculator, Range
from .opponent_model import OpponentModel, OpponentInsights


class Position(Enum):
    """Player positions at the table"""
    BTN = 9  # Button - Best position
    CO = 8   # Cutoff
    HJ = 7   # Hijack
    LJ = 6   # Lojack
    MP3 = 5  # Middle Position 3
    MP2 = 4  # Middle Position 2
    MP1 = 3  # Middle Position 1
    UTG2 = 2 # Under the Gun +2
    UTG1 = 1 # Under the Gun +1
    UTG = 0  # Under the Gun - Worst position
    SB = -1  # Small Blind
    BB = -2  # Big Blind


class Street(Enum):
    """Betting streets"""
    PREFLOP = 0
    FLOP = 1
    TURN = 2
    RIVER = 3


@dataclass
class GameState:
    """Current game state"""
    hero_cards: List[Card]
    board: List[Card]
    pot_size: float
    to_call: float
    hero_stack: float
    villain_stack: float
    hero_position: Position
    street: Street
    num_opponents: int = 1
    villain_range: Optional[Range] = None
    previous_actions: List[Dict] = None


@dataclass
class Factors:
    """All calculated factors"""
    # Core factors
    hand_strength: float        # [0, 1] - Basic hand strength
    equity: float               # [0, 1] - Win probability vs range
    pot_odds: float            # [0, 1] - Required equity to call

    # Stack factors
    stack_to_pot_ratio: float   # SPR - Stack depth relative to pot
    effective_stack: float      # Min(hero_stack, villain_stack)

    # Position factors
    position_factor: float      # [0, 1] - Position advantage

    # Board texture factors
    board_wetness: float        # [0, 1] - How coordinated the board is
    flush_possible: bool        # Is a flush possible on board
    straight_possible: bool     # Is a straight possible on board
    paired_board: bool         # Is the board paired

    # Draw factors
    outs: int                  # Number of outs to improve
    draw_probability: float     # Probability of hitting draw

    # Implied odds factors
    implied_odds: float        # Adjusted pot odds with future bets
    fold_equity: float         # Estimated fold probability

    # Opponent factors
    opponent_aggression: float  # [0, 1] - Opponent's aggression level
    opponent_tightness: float   # [0, 1] - How tight opponent plays
    betting_pressure: float = 0.0     # [0, 1] - Bet sizing pressure exerted
    board_pressure: float = 0.0       # [0, 1] - Pressure created by board texture vs range
    range_advantage: float = 0.5      # [0, 1] - Opponent range advantage estimation
    psychological_pressure: float = 0.0  # [0, 1] - Momentum/stack pressure
    bluff_tendency: float = 0.0       # [0, 1] - Estimated bluff frequency
    opponent_classification: str = ''  # Human-readable archetype
    opponent_summary: str = ''        # Short summary string
    opponent_notes: List[str] = field(default_factory=list)

    # Meta factors
    street: int                # Current street (0-3)
    pot_commitment: float      # [0, 1] - How committed we are

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)

    def to_vector(self) -> np.ndarray:
        """Convert to feature vector for ML models"""
        return np.array([
            self.hand_strength,
            self.equity,
            self.pot_odds,
            self.stack_to_pot_ratio,
            self.position_factor,
            self.board_wetness,
            float(self.flush_possible),
            float(self.straight_possible),
            float(self.paired_board),
            self.outs / 20.0,  # Normalize outs
            self.draw_probability,
            self.implied_odds,
            self.fold_equity,
            self.opponent_aggression,
            self.opponent_tightness,
            self.betting_pressure,
            self.board_pressure,
            self.range_advantage,
            self.psychological_pressure,
            self.bluff_tendency,
            self.street / 3.0,  # Normalize street
            self.pot_commitment
        ])


class FactorEngine:
    """Engine for calculating all decision factors"""

    def __init__(
        self,
        evaluator: Optional[HandEvaluator] = None,
        equity_calculator: Optional[EquityCalculator] = None
    ):
        """
        Initialize the factor engine
        Args:
            evaluator: HandEvaluator instance
            equity_calculator: EquityCalculator instance
        """
        self.evaluator = evaluator or HandEvaluator()
        self.equity_calculator = equity_calculator or EquityCalculator(self.evaluator)
        self._opponent_model = OpponentModel()
        self._latest_opponent_insights: Optional[OpponentInsights] = None

    def calculate_factors(
        self,
        game_state: GameState,
        opponent_stats: Optional[Dict] = None
    ) -> Factors:
        """
        Calculate all factors for the current game state

        Args:
            game_state: Current game state
            opponent_stats: Optional opponent statistics

        Returns:
            Factors object with all calculated values
        """
        # Calculate core factors
        hand_strength = self._calculate_hand_strength(game_state)
        equity = self._calculate_equity(game_state)
        pot_odds = self._calculate_pot_odds(game_state)

        # Stack factors
        effective_stack = min(game_state.hero_stack, game_state.villain_stack)
        spr = self._calculate_spr(game_state, effective_stack)

        # Position factor
        position_factor = self._calculate_position_factor(game_state)

        # Board texture
        board_analysis = self._analyze_board_texture(game_state.board)

        # Draw factors
        outs = self._calculate_outs(game_state)
        draw_prob = self._calculate_draw_probability(outs, game_state.street)

        # Implied odds
        opponent_insights = self._opponent_model.evaluate(
            opponent_stats=opponent_stats,
            previous_actions=game_state.previous_actions,
            board_analysis=board_analysis,
            hero_equity=equity,
            hero_hand_strength=hand_strength,
            pot_size=game_state.pot_size,
            hero_stack=game_state.hero_stack,
            villain_stack=game_state.villain_stack,
            street=game_state.street,
        )
        self._latest_opponent_insights = opponent_insights

        implied_odds = self._calculate_implied_odds(
            game_state, draw_prob, opponent_insights
        )

        # Opponent factors
        opp_aggression, opp_tightness, fold_equity = self._analyze_opponent(
            opponent_insights, game_state
        )

        # Meta factors
        pot_commitment = self._calculate_pot_commitment(game_state, effective_stack)

        return Factors(
            hand_strength=hand_strength,
            equity=equity,
            pot_odds=pot_odds,
            stack_to_pot_ratio=spr,
            effective_stack=effective_stack,
            position_factor=position_factor,
            board_wetness=board_analysis['wetness'],
            flush_possible=board_analysis['flush_possible'],
            straight_possible=board_analysis['straight_possible'],
            paired_board=board_analysis['paired'],
            outs=outs,
            draw_probability=draw_prob,
            implied_odds=implied_odds,
            fold_equity=fold_equity,
            opponent_aggression=opp_aggression,
            opponent_tightness=opp_tightness,
            betting_pressure=opponent_insights.betting_pressure,
            board_pressure=opponent_insights.board_pressure,
            range_advantage=opponent_insights.range_advantage,
            psychological_pressure=opponent_insights.psychological_pressure,
            bluff_tendency=opponent_insights.bluff_tendency,
            opponent_classification=opponent_insights.classification,
            opponent_summary=opponent_insights.summary,
            opponent_notes=opponent_insights.notes,
            street=game_state.street.value,
            pot_commitment=pot_commitment
        )

    def _calculate_hand_strength(self, game_state: GameState) -> float:
        """Calculate normalized hand strength"""
        all_cards = game_state.hero_cards + game_state.board
        if len(all_cards) < 5:
            return self._estimate_partial_strength(game_state)
        return self.evaluator.get_hand_strength(all_cards)

    def _estimate_partial_strength(self, game_state: GameState) -> float:
        """Estimate hand strength when fewer than 5 cards are known"""
        hole_cards = game_state.hero_cards

        if len(hole_cards) != 2:
            return 0.0

        # Preflop heuristic based on pair strength, connectivity, and suits
        ranks = sorted([card.rank for card in hole_cards], reverse=True)
        high, low = ranks
        suited = hole_cards[0].suit == hole_cards[1].suit
        gap = high - low

        if high == low:  # Pocket pair
            # Base between 0.5 (22) and ~0.95 (AA)
            normalized = (high - 2) / 12  # 0 for deuces, 1 for aces
            strength = 0.5 + normalized * 0.45
            return min(0.98, max(0.45, strength))

        # Non-pair hands
        strength = 0.18  # Baseline for unconnected, offsuit trash
        strength += (high / 14) * 0.45
        strength += (low / 14) * 0.22

        if suited:
            strength += 0.07

        if gap == 1:
            strength += 0.08
        elif gap == 2:
            strength += 0.05
        elif gap == 3:
            strength += 0.03
        elif gap > 3:
            strength -= min(0.02 * (gap - 3), 0.12)

        if high == 14:
            strength += 0.05
        if high >= 13 and low >= 10:
            strength += 0.03

        return min(0.9, max(0.05, strength))

    def _calculate_equity(self, game_state: GameState) -> float:
        """Calculate equity against opponent range"""
        return self.equity_calculator.calculate_equity(
            hero_cards=game_state.hero_cards,
            villain_range=game_state.villain_range,
            board=game_state.board,
            num_opponents=game_state.num_opponents,
            iterations=5000  # Reduced for speed
        )

    def _calculate_pot_odds(self, game_state: GameState) -> float:
        """Calculate pot odds"""
        if game_state.pot_size + game_state.to_call == 0:
            return 0
        return game_state.to_call / (game_state.pot_size + game_state.to_call)

    def _calculate_spr(self, game_state: GameState, effective_stack: float) -> float:
        """Calculate stack-to-pot ratio"""
        if game_state.pot_size == 0:
            return float('inf')
        return effective_stack / game_state.pot_size

    def _calculate_position_factor(self, game_state: GameState) -> float:
        """Calculate position advantage factor"""
        # Normalize position to 0-1 (BTN=1, UTG=0)
        if game_state.hero_position in [Position.SB, Position.BB]:
            # Blinds act last preflop but first postflop
            if game_state.street == Street.PREFLOP:
                return 0.5
            else:
                return 0.1

        # Map position value to 0-1 range
        pos_value = game_state.hero_position.value
        return (pos_value + 2) / 11.0  # Normalize from -2 to 9 -> 0 to 1

    def _analyze_board_texture(self, board: List[Card]) -> Dict:
        """Analyze board texture"""
        if not board:
            return {
                'wetness': 0,
                'flush_possible': False,
                'straight_possible': False,
                'paired': False
            }

        ranks = [card.rank for card in board]
        suits = [card.suit for card in board]

        # Check for flush possibilities
        suit_counts = {}
        for suit in suits:
            suit_counts[suit] = suit_counts.get(suit, 0) + 1
        flush_possible = any(count >= 3 for count in suit_counts.values())

        # Check for straight possibilities
        unique_ranks = sorted(set(ranks))
        straight_possible = False
        if len(unique_ranks) >= 3:
            for i in range(len(unique_ranks) - 2):
                if unique_ranks[i+2] - unique_ranks[i] <= 4:
                    straight_possible = True
                    break

        # Check for paired board
        paired = len(ranks) != len(set(ranks))

        # Calculate wetness (coordination score)
        wetness = 0.0
        if flush_possible:
            wetness += 0.3
        if straight_possible:
            wetness += 0.3
        if paired:
            wetness += 0.2

        # Add connectivity bonus
        if len(unique_ranks) >= 2:
            gaps = [unique_ranks[i+1] - unique_ranks[i] for i in range(len(unique_ranks)-1)]
            avg_gap = sum(gaps) / len(gaps)
            connectivity = max(0, 1 - (avg_gap - 1) / 4)  # Normalize gaps
            wetness += connectivity * 0.2

        wetness = min(1.0, wetness)

        return {
            'wetness': wetness,
            'flush_possible': flush_possible,
            'straight_possible': straight_possible,
            'paired': paired
        }

    def _calculate_outs(self, game_state: GameState) -> int:
        """Calculate number of outs"""
        outs_dict = self.evaluator.get_outs(
            game_state.hero_cards,
            game_state.board
        )
        return sum(outs_dict.values())

    def _calculate_draw_probability(self, outs: int, street: Street) -> float:
        """Calculate probability of hitting draw"""
        if street == Street.RIVER or outs == 0:
            return 0

        cards_remaining = 52 - 2  # Hero cards
        if street == Street.FLOP:
            cards_remaining -= 3
            cards_to_come = 2  # Turn and river
        elif street == Street.TURN:
            cards_remaining -= 4
            cards_to_come = 1  # River only
        else:
            return 0

        # Approximate probability (rule of 2 and 4)
        if cards_to_come == 2:
            return min(1.0, outs * 4 / 100)
        else:
            return min(1.0, outs * 2 / 100)

    def _calculate_implied_odds(
        self,
        game_state: GameState,
        draw_probability: float,
        opponent_insights: OpponentInsights
    ) -> float:
        """Calculate implied odds"""
        if draw_probability == 0:
            return self._calculate_pot_odds(game_state)

        # Estimate future bets based on opponent stats
        aggression = opponent_insights.aggression_index
        betting_pressure = opponent_insights.betting_pressure

        future_bet_multiplier = 0.25 + aggression * 0.4 + betting_pressure * 0.35
        future_bet_multiplier = min(1.5, max(0.1, future_bet_multiplier))

        expected_future_bets = game_state.pot_size * future_bet_multiplier

        effective_pot = game_state.pot_size + expected_future_bets * draw_probability

        if effective_pot + game_state.to_call == 0:
            return 0

        return game_state.to_call / (effective_pot + game_state.to_call)

    def _analyze_opponent(
        self,
        opponent_insights: OpponentInsights,
        game_state: GameState
    ) -> Tuple[float, float, float]:
        """Analyze opponent and estimate fold equity"""
        insights = opponent_insights

        aggression = insights.aggression_index
        tightness = insights.tightness_index

        fold_equity = (
            (1 - aggression) * 0.35 +
            tightness * 0.35 +
            (1 - insights.betting_pressure) * 0.2 +
            (1 - insights.psychological_pressure) * 0.1
        )

        # Adjust for hero position advantage
        if game_state.hero_position.value > 5:
            fold_equity *= 1.15
        elif game_state.hero_position.value < 1:
            fold_equity *= 0.9

        # Adjust for board favouring opponent
        fold_equity *= max(0.4, 1 - insights.board_pressure * 0.5)

        # Adjust for street (less folding later)
        if game_state.street == Street.TURN:
            fold_equity *= 0.9
        elif game_state.street == Street.RIVER:
            fold_equity *= 0.75

        fold_equity = min(1.0, max(0.0, fold_equity))

        return aggression, tightness, fold_equity

    def _calculate_pot_commitment(
        self,
        game_state: GameState,
        effective_stack: float
    ) -> float:
        """Calculate how pot-committed we are"""
        total_investment = game_state.hero_stack - effective_stack
        total_pot = game_state.pot_size + total_investment

        if total_pot == 0:
            return 0

        return min(1.0, total_investment / total_pot)

    def get_latest_opponent_profile(self) -> Optional[OpponentInsights]:
        """Expose cached opponent insight for downstream consumers."""
        return self._latest_opponent_insights
