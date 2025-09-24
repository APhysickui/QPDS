"""
Flask API for QPDS
Main application entry point with REST endpoints
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from typing import Dict, List, Optional
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import (
    HandEvaluator, Card, EquityCalculator, Range,
    FactorEngine, GameState, Position, Street,
    DecisionEngine, Decision
)


class InvalidCardError(ValueError):
    """Raised when provided cards violate Texas Hold'em rules"""


REQUIRED_BOARD_CARDS = {
    Street.PREFLOP: 0,
    Street.FLOP: 3,
    Street.TURN: 4,
    Street.RIVER: 5,
}

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize core components
hand_evaluator = HandEvaluator()
equity_calculator = EquityCalculator(hand_evaluator)
factor_engine = FactorEngine(hand_evaluator, equity_calculator)
decision_engine = DecisionEngine(factor_engine)


def parse_cards(card_strings: List[str]) -> List[Card]:
    """Parse card strings into Card objects"""
    cards = []
    for raw in card_strings:
        card_str = (raw or "").strip()
        if len(card_str) < 2:
            raise InvalidCardError(f"Invalid card format: '{raw}'")

        try:
            card = Card.from_string(card_str)
        except (KeyError, IndexError, ValueError):
            raise InvalidCardError(f"Invalid card format: '{raw}'")

        cards.append(card)

    return cards


def validate_unique_cards(cards: List[Card]):
    """Ensure no duplicate cards are present"""
    if len(cards) != len(set(cards)):
        raise InvalidCardError("Duplicate cards detected in input")


def validate_board_for_street(board_size: int, street: Street):
    """Ensure community cards match the selected street"""
    required = REQUIRED_BOARD_CARDS.get(street, 0)
    if board_size != required:
        street_name = street.name.capitalize()
        raise InvalidCardError(
            f"{street_name} requires exactly {required} community cards, received {board_size}"
        )


def parse_position(position_str: str) -> Position:
    """Parse position string into Position enum"""
    position_map = {
        'BTN': Position.BTN,
        'CO': Position.CO,
        'HJ': Position.HJ,
        'LJ': Position.LJ,
        'MP3': Position.MP3,
        'MP2': Position.MP2,
        'MP1': Position.MP1,
        'UTG2': Position.UTG2,
        'UTG1': Position.UTG1,
        'UTG': Position.UTG,
        'SB': Position.SB,
        'BB': Position.BB
    }
    return position_map.get(position_str.upper(), Position.BTN)


def parse_street(street_str: str) -> Street:
    """Parse street string into Street enum"""
    street_map = {
        'PREFLOP': Street.PREFLOP,
        'FLOP': Street.FLOP,
        'TURN': Street.TURN,
        'RIVER': Street.RIVER
    }
    return street_map.get(street_str.upper(), Street.PREFLOP)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'QPDS API'}), 200


@app.route('/api/evaluate_hand', methods=['POST'])
def evaluate_hand():
    """
    Evaluate poker hand strength

    Request body:
    {
        "cards": ["As", "Kh", "Qd", "Jc", "Ts"]  // 5-7 cards
    }
    """
    try:
        data = request.json
        card_strings = data.get('cards', [])

        if len(card_strings) < 5:
            return jsonify({'error': 'Need at least 5 cards'}), 400

        cards = parse_cards(card_strings)

        # Evaluate hand
        hand_rank, values = hand_evaluator.evaluate(cards)
        strength = hand_evaluator.get_hand_strength(cards)

        return jsonify({
            'hand_rank': hand_rank.name,
            'rank_value': hand_rank.value,
            'strength': strength,
            'tiebreakers': values[:5]
        }), 200

    except InvalidCardError as exc:
        return jsonify({'error': str(exc)}), 400
    except Exception as e:
        logger.error(f"Error evaluating hand: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/get_equity', methods=['POST'])
def get_equity():
    """
    Calculate equity against opponent range

    Request body:
    {
        "hero_cards": ["As", "Kh"],
        "board": ["Qd", "Jc", "Ts"],  // Optional
        "villain_range": "AA,KK,QQ,AKs",  // Optional, defaults to random
        "num_opponents": 1,
        "iterations": 10000
    }
    """
    try:
        data = request.json

        hero_card_strings = data.get('hero_cards', [])
        board_strings = data.get('board', [])

        if len(hero_card_strings) != 2:
            raise InvalidCardError("Texas Hold'em requires exactly two hero cards")
        if len(board_strings) > 5:
            raise InvalidCardError("Community cards cannot exceed five")

        hero_cards = parse_cards(hero_card_strings)
        board = parse_cards(board_strings)

        validate_unique_cards(hero_cards + board)
        num_opponents = data.get('num_opponents', 1)
        iterations = data.get('iterations', 10000)

        # Parse villain range
        villain_range = None
        if 'villain_range' in data and data['villain_range']:
            villain_range = Range(data['villain_range'])

        # Calculate equity
        equity = equity_calculator.calculate_equity(
            hero_cards=hero_cards,
            villain_range=villain_range,
            board=board,
            num_opponents=num_opponents,
            iterations=iterations
        )

        return jsonify({
            'equity': equity,
            'win_percentage': equity * 100,
            'hero_cards': [str(c) for c in hero_cards],
            'board': [str(c) for c in board]
        }), 200

    except InvalidCardError as exc:
        return jsonify({'error': str(exc)}), 400
    except Exception as e:
        logger.error(f"Error calculating equity: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/get_factors', methods=['POST'])
def get_factors():
    """
    Calculate all decision factors

    Request body:
    {
        "hero_cards": ["As", "Kh"],
        "board": ["Qd", "Jc", "Ts"],
        "pot_size": 100,
        "to_call": 20,
        "hero_stack": 500,
        "villain_stack": 450,
        "position": "BTN",
        "street": "FLOP",
        "villain_range": "AA,KK,QQ,AKs",  // Optional
        "opponent_stats": {  // Optional
            "aggression": 0.7,
            "tightness": 0.3
        }
    }
    """
    try:
        data = request.json

        # Parse core inputs
        hero_card_strings = data.get('hero_cards', [])
        board_strings = data.get('board', [])
        position = parse_position(data.get('position', 'BTN'))
        street = parse_street(data.get('street', 'PREFLOP'))

        if len(hero_card_strings) != 2:
            raise InvalidCardError("Texas Hold'em requires exactly two hero cards")
        if len(board_strings) > 5:
            raise InvalidCardError("Community cards cannot exceed five")

        validate_board_for_street(len(board_strings), street)

        hero_cards = parse_cards(hero_card_strings)
        board = parse_cards(board_strings)

        validate_unique_cards(hero_cards + board)

        villain_range = None
        if 'villain_range' in data and data['villain_range']:
            villain_range = Range(data['villain_range'])

        game_state = GameState(
            hero_cards=hero_cards,
            board=board,
            pot_size=float(data.get('pot_size', 0)),
            to_call=float(data.get('to_call', 0)),
            hero_stack=float(data.get('hero_stack', 1000)),
            villain_stack=float(data.get('villain_stack', 1000)),
            hero_position=position,
            street=street,
            num_opponents=data.get('num_opponents', 1),
            villain_range=villain_range
        )

        opponent_stats = data.get('opponent_stats')

        # Calculate factors
        factors = factor_engine.calculate_factors(game_state, opponent_stats)

        return jsonify(factors.to_dict()), 200

    except InvalidCardError as exc:
        return jsonify({'error': str(exc)}), 400
    except Exception as e:
        logger.error(f"Error calculating factors: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/get_recommendation', methods=['POST'])
def get_recommendation():
    """
    Get action recommendation

    Request body:
    {
        "hero_cards": ["As", "Kh"],
        "board": ["Qd", "Jc", "Ts"],
        "pot_size": 100,
        "to_call": 20,
        "hero_stack": 500,
        "villain_stack": 450,
        "position": "BTN",
        "street": "FLOP",
        "risk_preference": 5,  // 0-10
        "villain_range": "AA,KK,QQ,AKs",  // Optional
        "opponent_stats": {  // Optional
            "aggression": 0.7,
            "tightness": 0.3
        }
    }
    """
    try:
        data = request.json

        # Parse inputs with validation
        hero_card_strings = data.get('hero_cards', [])
        board_strings = data.get('board', [])
        position = parse_position(data.get('position', 'BTN'))
        street = parse_street(data.get('street', 'PREFLOP'))

        if len(hero_card_strings) != 2:
            raise InvalidCardError("Texas Hold'em requires exactly two hero cards")
        if len(board_strings) > 5:
            raise InvalidCardError("Community cards cannot exceed five")

        validate_board_for_street(len(board_strings), street)

        hero_cards = parse_cards(hero_card_strings)
        board = parse_cards(board_strings)

        validate_unique_cards(hero_cards + board)

        villain_range = None
        if 'villain_range' in data and data['villain_range']:
            villain_range = Range(data['villain_range'])

        game_state = GameState(
            hero_cards=hero_cards,
            board=board,
            pot_size=float(data.get('pot_size', 0)),
            to_call=float(data.get('to_call', 0)),
            hero_stack=float(data.get('hero_stack', 1000)),
            villain_stack=float(data.get('villain_stack', 1000)),
            hero_position=position,
            street=street,
            num_opponents=data.get('num_opponents', 1),
            villain_range=villain_range
        )

        # Set risk preference
        risk_pref = float(data.get('risk_preference', 5))
        decision_engine.set_risk_preference(risk_pref)

        opponent_stats = data.get('opponent_stats')

        # Get decision
        decision = decision_engine.make_decision(game_state, opponent_stats)

        # Calculate factors for additional info
        factors = factor_engine.calculate_factors(game_state, opponent_stats)

        return jsonify({
            'action': decision.action.value,
            'amount': decision.amount,
            'confidence': decision.confidence,
            'expected_value': decision.expected_value,
            'explanation': decision.explanation,
            'factors_used': decision.factors_used,
            'all_factors': factors.to_dict()
        }), 200

    except InvalidCardError as exc:
        return jsonify({'error': str(exc)}), 400
    except Exception as e:
        logger.error(f"Error getting recommendation: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/parse_hand_history', methods=['POST'])
def parse_hand_history():
    """
    Parse hand history text

    Request body:
    {
        "history_text": "..."
    }
    """
    # TODO: Implement hand history parser
    return jsonify({
        'message': 'Hand history parser not yet implemented',
        'status': 'pending'
    }), 501


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500


def main():
    """Main entry point"""
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'

    logger.info(f"Starting QPDS API on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)


if __name__ == '__main__':
    main()
