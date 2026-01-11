# Market Trading Bots

Python trading bots for a C++ market exchange simulation.

## Overview

Automated trading bots that communicate with a C++ exchange via ZeroMQ. Each bot runs its own trading strategy and tracks its P&L independently.

## Project Structure

```
market-bots/
├── src/
│   ├── __init__.py          # Package exports
│   ├── enums.py              # Side, OrdType, TimeInForce, MsgType
│   ├── messages.py           # Message structures and JSON serialization
│   ├── position.py           # Position and P&L tracking
│   ├── exchange_client.py    # ZeroMQ communication with exchange
│   ├── base_bot.py           # Base class for all trading bots
│   ├── momentum.py           # Momentum strategy (MA crossover)
│   ├── mean_reversion.py     # Mean reversion strategy (z-score)
│   ├── arbitrage.py          # Pairs trading strategy
│   ├── vwap.py               # TWAP execution algorithm
│   └── dashboard.py          # Terminal dashboard for monitoring
├── main.py                   # Example usage
├── requirements.txt          # Python dependencies
└── README.md
```

## Strategies

- **Momentum**: Follows trends using moving average crossover
- **Mean Reversion**: Bets against price extremes using z-score
- **Arbitrage**: Trades the spread between two correlated symbols
- **VWAP/TWAP**: Executes large orders gradually over time

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```python
from src import MomentumBot, MomentumConfig, Dashboard

bot = MomentumBot(MomentumConfig(
    client_id=1,
    name="My Bot",
    symbols=["AAPL"]
))

bot.start()  # Blocks until Ctrl+C
```

## Communication Protocol

- **Port 5555**: Bot sends orders to exchange (ZeroMQ PUSH → PULL)
- **Port 5556**: Exchange sends responses to bot (ZeroMQ PUSH → PULL)
- **Format**: JSON with header and body

## Message Types

| Direction | Type | Code | Purpose |
|-----------|------|------|---------|
| Bot → Exchange | NEW_ORDER | 1 | Place order |
| Bot → Exchange | CANCEL | 2 | Cancel order |
| Exchange → Bot | ACK | 100 | Order accepted |
| Exchange → Bot | REJECT | 101 | Order rejected |
| Exchange → Bot | FILL | 102 | Order executed |
