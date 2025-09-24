"""Validation tests for Flask API input rules."""

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.api.app import app


@pytest.fixture(scope="module")
def client():
    """Flask test client fixture."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def base_payload():
    """Generate a baseline valid payload for recommendation endpoint."""
    return {
        'hero_cards': ['As', 'Kh'],
        'board': [],
        'pot_size': 100,
        'to_call': 10,
        'hero_stack': 500,
        'villain_stack': 450,
        'position': 'BTN',
        'street': 'PREFLOP',
        'risk_preference': 5
    }


def test_recommendation_rejects_duplicate_cards(client):
    payload = base_payload()
    payload['hero_cards'] = ['As', 'As']
    response = client.post('/api/get_recommendation', json=payload)
    assert response.status_code == 400
    assert 'Duplicate cards' in response.get_json()['error']


def test_recommendation_requires_correct_board_count(client):
    payload = base_payload()
    payload['street'] = 'FLOP'
    payload['board'] = ['Kd', 'Qs']  # Should be exactly three cards on the flop
    response = client.post('/api/get_recommendation', json=payload)
    assert response.status_code == 400
    assert 'requires exactly 3' in response.get_json()['error']


def test_equity_requires_two_hole_cards(client):
    response = client.post('/api/get_equity', json={
        'hero_cards': ['As'],
        'board': [],
        'iterations': 1000
    })
    assert response.status_code == 400
    assert 'two hero cards' in response.get_json()['error']
