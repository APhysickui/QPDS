# QPDS - Quantitative Poker Decision System
## 量化扑克决策系统

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/)

A quantitative approach to Texas Hold'em poker decision-making, inspired by quantitative investment strategies.

## 🎯 Project Overview

QPDS implements a hybrid strategy combining:
- **Rule-based EV (Expected Value) engine** for core decision-making
- **Statistical/ML modules** for opponent modeling and strategy optimization
- **Real-time factor calculation** for comprehensive game state analysis

## 🏗️ Architecture

```
QPDS/
├── backend/                 # Python backend
│   ├── core/               # Core calculation modules
│   │   ├── evaluator/      # Hand evaluation
│   │   ├── calculator/     # Equity & odds calculation
│   │   └── engine/         # Decision & factor engines
│   ├── api/                # Flask/FastAPI endpoints
│   ├── models/             # Data models & schemas
│   ├── utils/              # Utility functions
│   └── config/             # Configuration files
├── frontend/               # Vue.js/React frontend
├── tests/                  # Test suites
├── docs/                   # Documentation
├── scripts/                # Utility scripts
└── data/                   # Sample data & hand histories
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 14+
- Redis (optional, for caching)
- PostgreSQL (optional, for persistence)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/QPDS.git
cd QPDS
```

2. Set up Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Install frontend dependencies:
```bash
cd frontend
npm install
```

4. Run the application:
```bash
# Backend
python backend/app.py

# Frontend (in another terminal)
cd frontend
npm run dev
```

## 📊 Core Features

### 1. Hand Evaluation
- Fast 7-card hand evaluator
- Hand strength percentile ranking
- Board texture analysis

### 2. Equity Calculation
- Monte Carlo simulation
- Exact enumeration for small scenarios
- Multi-opponent support

### 3. Factor Engine
- **Static Factors**: Hand Strength, Position
- **Dynamic Factors**: Pot Odds, Stack-to-Pot Ratio, Implied Odds
- **Behavioral Factors**: Opponent aggression, betting patterns

### 4. Decision Engine
- EV-based recommendations
- Risk preference adjustment
- Action explanation system

## 📈 Factor System

| Factor | Type | Description | Range |
|--------|------|-------------|-------|
| HandStrength (HS) | Static | Basic hand strength | [0,1] |
| Equity (E) | Dynamic | Win probability vs range | [0,1] |
| PotOdds (PO) | Dynamic | Required win rate to call | [0,1] |
| StackToPotRatio (SPR) | Dynamic | Effective stack / pot | [0,∞) |
| PositionFactor (PF) | Static | Table position advantage | [0,1] |
| OpponentAggression (OA) | Dynamic | Opponent's aggression level | [0,1] |

## 🔬 Mathematical Model

### Basic EV Calculation
```
EV_call = E × (P + B) - B
```
Where:
- E = Equity (win probability)
- P = Current pot
- B = Amount to call

### Risk-Adjusted Decision
```
requiredEquity = PotOdds + riskAdjustment
riskAdjustment = α × (1 - r/10)
```
Where:
- α = Risk factor coefficient (default 0.05)
- r = Risk slider value [0,10]

## 🧪 Testing

Run the test suite:
```bash
pytest tests/
```

Performance benchmarks:
```bash
python scripts/benchmark.py
```

## 📝 API Documentation

### Core Endpoints

- `POST /api/get_recommendation`
  - Input: Hand state + risk preference
  - Output: Action recommendation with explanation

- `POST /api/get_equity`
  - Input: Hero cards, board, opponent ranges
  - Output: Win probability

- `POST /api/get_factors`
  - Input: Game state
  - Output: All calculated factors

## 🐳 Docker Support

```bash
docker-compose up
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📊 Performance Metrics

- Core equity calculation: < 50ms (95th percentile)
- API response time: < 200ms
- Monte Carlo convergence: 10,000 iterations in < 100ms

## 🗺️ Roadmap

### Phase 1 (MVP) ✅
- [x] Basic hand evaluator
- [x] Equity calculator
- [x] Core factor engine
- [x] Rule-based decision engine
- [x] Simple API

### Phase 2 (In Progress)
- [ ] Hand history parser
- [ ] Backtesting framework
- [ ] Opponent modeling
- [ ] Advanced UI

### Phase 3 (Planned)
- [ ] Machine learning integration
- [ ] GTO solver approximation
- [ ] Real-time adaptation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Poker hand evaluator algorithms based on Cactus Kev's evaluator
- Monte Carlo methods inspired by PokerStove
- Quantitative framework adapted from modern portfolio theory

## 📧 Contact

For questions or suggestions, please open an issue on GitHub.

or contact with me ，my blog website address is
https://akuiro24.xyz/

---

**Disclaimer**: This tool is for educational purposes. Always check platform policies before using poker assistance tools.