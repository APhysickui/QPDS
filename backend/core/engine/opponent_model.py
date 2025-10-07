"""Opponent modeling utilities for factor engine"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - type hints only
    from .factor_engine import Street


def _clamp(value: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
    """Clamp numeric value into a range."""
    return max(min_value, min(max_value, value))


def _safe_ratio(numerator: float, denominator: float) -> float:
    """Return a safe division result."""
    if denominator == 0:
        return 0.0
    return numerator / denominator


@dataclass
class OpponentInsights:
    """Snapshot of inferred opponent tendencies."""

    aggression_index: float
    tightness_index: float
    betting_pressure: float
    board_pressure: float
    range_advantage: float
    psychological_pressure: float
    bluff_tendency: float
    volatility: float
    classification: str
    summary: str
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Transform into a serialisable dict."""
        return {
            'aggression_index': self.aggression_index,
            'tightness_index': self.tightness_index,
            'betting_pressure': self.betting_pressure,
            'board_pressure': self.board_pressure,
            'range_advantage': self.range_advantage,
            'psychological_pressure': self.psychological_pressure,
            'bluff_tendency': self.bluff_tendency,
            'volatility': self.volatility,
            'classification': self.classification,
            'summary': self.summary,
            'notes': self.notes,
        }


class OpponentModel:
    """Heuristic opponent modelling layer."""

    DEFAULT_STATS = {
        'aggression': 0.5,
        'tightness': 0.5,
        'bluff_frequency': 0.3,
        'recent_bet_pct': 65.0,
        'tilt': 0.4,
        'confidence': 0.6,
        'volatility': 0.5,
    }

    def evaluate(
        self,
        *,
        opponent_stats: Optional[Dict[str, Any]],
        previous_actions: Optional[List[Dict[str, Any]]],
        board_analysis: Dict[str, Any],
        hero_equity: float,
        hero_hand_strength: float,
        pot_size: float,
        hero_stack: float,
        villain_stack: float,
        street: 'Street',
    ) -> OpponentInsights:
        """Produce opponent insight snapshot."""
        stats = {**self.DEFAULT_STATS, **(opponent_stats or {})}

        observations = self._collect_observations(
            stats.get('observations'), previous_actions
        )

        bet_ratios = [obs['bet_ratio'] for obs in observations if obs['bet_ratio'] is not None]
        avg_bet_ratio = sum(bet_ratios) / len(bet_ratios) if bet_ratios else stats['recent_bet_pct'] / 100
        betting_pressure = _clamp(avg_bet_ratio / 1.5)  # 1.5 pot = very high pressure

        aggression_from_actions = self._estimate_aggression_from_actions(observations)
        aggression_index = _clamp(stats['aggression'] * 0.6 + aggression_from_actions * 0.4)

        tightness_from_actions = self._estimate_tightness_from_actions(observations, stats['tightness'])
        tightness_index = _clamp(tightness_from_actions)

        board_pressure = self._estimate_board_pressure(board_analysis, betting_pressure, aggression_index)

        stack_share = _safe_ratio(villain_stack - hero_stack, (hero_stack + villain_stack) or 1)
        pot_pressure = _clamp(_safe_ratio(pot_size, (hero_stack + villain_stack + pot_size) or 1))
        tilt_component = 1 - stats.get('tilt', 0.4)
        confidence_component = stats.get('confidence', 0.6)
        psychological_pressure = _clamp(
            0.35 * (stack_share * 0.5 + 0.5) +
            0.3 * betting_pressure +
            0.2 * aggression_index +
            0.1 * confidence_component * tilt_component +
            0.05 * pot_pressure
        )

        range_advantage = self._estimate_range_advantage(
            tightness_index,
            aggression_index,
            board_pressure,
            hero_equity,
            hero_hand_strength
        )

        bluff_tendency = _clamp(stats.get('bluff_frequency', 0.3) * 0.5 + (1 - tightness_index) * 0.3 + aggression_index * 0.2)

        volatility = _clamp(stats.get('volatility', 0.5) * 0.6 + self._calc_volatility(observations) * 0.4)

        classification = self._classify_player(aggression_index, tightness_index, bluff_tendency)
        summary, notes = self._build_summary(
            classification,
            betting_pressure,
            board_pressure,
            psychological_pressure,
            range_advantage,
            bluff_tendency,
            observations,
            street
        )

        return OpponentInsights(
            aggression_index=aggression_index,
            tightness_index=tightness_index,
            betting_pressure=betting_pressure,
            board_pressure=board_pressure,
            range_advantage=range_advantage,
            psychological_pressure=psychological_pressure,
            bluff_tendency=bluff_tendency,
            volatility=volatility,
            classification=classification,
            summary=summary,
            notes=notes,
        )

    def _collect_observations(
        self,
        explicit: Optional[List[Dict[str, Any]]],
        previous_actions: Optional[List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """Merge explicit observations with previous action log and normalise."""
        observations: List[Dict[str, Any]] = []
        source = explicit or []

        for entry in source:
            bet_ratio = None
            amount = entry.get('amount')
            pot = entry.get('pot') or entry.get('pot_before')
            if amount is not None and pot:
                bet_ratio = _safe_ratio(float(amount), float(pot))
            observations.append({
                'street': entry.get('street'),
                'action': entry.get('action'),
                'bet_ratio': bet_ratio,
            })

        if previous_actions:
            for entry in previous_actions:
                actor = (entry.get('actor') or entry.get('player') or '').lower()
                if actor not in ('villain', 'opponent', 'sb', 'bb', 'btn', 'co', 'hj', 'lj', 'mp', 'mp1', 'mp2', 'mp3'):
                    continue
                kind = (entry.get('action') or entry.get('type') or '').lower()
                if kind not in ('bet', 'raise', 'call', 'check', 'all-in', 'allin'):
                    continue
                amount = entry.get('amount') or entry.get('size')
                pot = entry.get('pot') or entry.get('pot_before')
                bet_ratio = None
                if amount is not None and pot:
                    bet_ratio = _safe_ratio(float(amount), float(pot))
                observations.append({
                    'street': entry.get('street'),
                    'action': kind,
                    'bet_ratio': bet_ratio,
                })

        return observations

    def _estimate_aggression_from_actions(self, observations: List[Dict[str, Any]]) -> float:
        """Aggression metric derived from action stream."""
        if not observations:
            return 0.5

        aggressive_actions = sum(1 for obs in observations if obs['action'] in ('bet', 'raise', 'all-in', 'allin'))
        passive_actions = sum(1 for obs in observations if obs['action'] in ('call', 'check'))
        total = aggressive_actions + passive_actions
        if total == 0:
            return 0.5
        ratio = aggressive_actions / total
        return _clamp(0.4 + ratio * 0.6)

    def _estimate_tightness_from_actions(
        self,
        observations: List[Dict[str, Any]],
        base_tightness: float
    ) -> float:
        """Heuristic tightening/loosening based on bet sizing."""
        if not observations:
            return base_tightness

        high_pressure = sum(1 for obs in observations if (obs['bet_ratio'] or 0) > 0.75)
        small_bets = sum(1 for obs in observations if 0 < (obs['bet_ratio'] or 0) <= 0.4)
        adjustments = 0.0
        if high_pressure:
            adjustments += 0.08 * high_pressure
        if small_bets:
            adjustments -= 0.05 * small_bets

        return _clamp(base_tightness + adjustments)

    def _estimate_board_pressure(
        self,
        board_analysis: Dict[str, Any],
        betting_pressure: float,
        aggression_index: float
    ) -> float:
        """Combine board texture and aggression into pressure metric."""
        wetness = float(board_analysis.get('wetness', 0.0))
        flush_possible = 1.0 if board_analysis.get('flush_possible') else 0.0
        straight_possible = 1.0 if board_analysis.get('straight_possible') else 0.0
        paired = 1.0 if board_analysis.get('paired') else 0.0

        texture = _clamp(0.45 * wetness + 0.2 * flush_possible + 0.2 * straight_possible + 0.15 * paired)
        return _clamp(texture * 0.55 + betting_pressure * 0.25 + aggression_index * 0.2)

    def _estimate_range_advantage(
        self,
        tightness_index: float,
        aggression_index: float,
        board_pressure: float,
        hero_equity: float,
        hero_hand_strength: float
    ) -> float:
        """Approximate villain range advantage vs hero."""
        hero_resilience = (hero_equity + hero_hand_strength) / 2
        opponent_range_threat = 0.35 * tightness_index + 0.3 * aggression_index + 0.35 * board_pressure

        delta = opponent_range_threat - hero_resilience
        return _clamp(0.5 + delta)

    def _calc_volatility(self, observations: List[Dict[str, Any]]) -> float:
        """Estimate volatility via bet dispersion."""
        bet_ratios = [obs['bet_ratio'] for obs in observations if obs['bet_ratio']]
        if len(bet_ratios) < 2:
            return 0.5

        avg = sum(bet_ratios) / len(bet_ratios)
        variance = sum((ratio - avg) ** 2 for ratio in bet_ratios) / len(bet_ratios)
        return _clamp(min(1.0, variance * 3))

    def _classify_player(
        self,
        aggression_index: float,
        tightness_index: float,
        bluff_tendency: float
    ) -> str:
        """Map metrics to human readable archetype."""
        if aggression_index >= 0.7 and tightness_index >= 0.6:
            return '紧凶型（TAG）'
        if aggression_index >= 0.7 and tightness_index < 0.45:
            return '松凶型（LAG）'
        if aggression_index < 0.4 and tightness_index >= 0.6:
            return '紧弱型（Nit）'
        if aggression_index < 0.45 and tightness_index < 0.45:
            if bluff_tendency < 0.35:
                return '跟注站（Calling Station）'
            return '被动松型'
        return '平衡型'

    def _build_summary(
        self,
        classification: str,
        betting_pressure: float,
        board_pressure: float,
        psychological_pressure: float,
        range_advantage: float,
        bluff_tendency: float,
        observations: List[Dict[str, Any]],
        street: Street
    ) -> (str, List[str]):
        """Create summary sentence and actionable notes."""
        notes: List[str] = []

        if betting_pressure > 0.7:
            notes.append('近期下注尺度偏大，面对施压需准备反击或缩短范围。')
        elif betting_pressure < 0.35:
            notes.append('下注尺度偏保守，可适度加大诈唬频率。')

        if bluff_tendency > 0.65:
            notes.append('诈唬倾向高，适合轻度跟注扩大摊牌频率。')
        elif bluff_tendency < 0.35:
            notes.append('诈唬频率低，重视价值下注。')

        if psychological_pressure > 0.7:
            notes.append('筹码与气势优势在对手侧，谨慎制定对抗计划。')
        elif psychological_pressure < 0.4:
            notes.append('对手压力较大，可增加持续下注。')

        if range_advantage > 0.65:
            notes.append('公共牌对对手更有利，警惕强力组合。')
        elif range_advantage < 0.45:
            notes.append('公共牌更利于我们，可增添攻击频率。')

        if not notes:
            notes.append('暂无明显倾向，保持平衡策略。')

        dominant_action = None
        if observations:
            counts: Dict[str, int] = {}
            for obs in observations:
                key = obs['action'] or 'unknown'
                counts[key] = counts.get(key, 0) + 1
            dominant_action = max(counts, key=counts.get)

        summary_parts = [classification]
        if dominant_action:
            summary_parts.append(f"常见动作：{dominant_action}")
        summary_parts.append(f"当前街：{getattr(street, 'name', street)}")

        summary = ' | '.join(summary_parts)
        return summary, notes
