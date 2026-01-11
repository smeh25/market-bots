"""Pairs trading / statistical arbitrage strategy."""
import math
from dataclasses import dataclass
from typing import Dict, List, Optional
from .base_bot import BaseBot, BotConfig


@dataclass
class ArbitrageConfig(BotConfig):
    symbol_a: str = ""
    symbol_b: str = ""
    lookback_window: int = 20
    entry_threshold: float = 2.0
    exit_threshold: float = 0.5
    order_size: int = 10


class ArbitrageBot(BaseBot):
    def __init__(self, config: ArbitrageConfig):
        super().__init__(config)
        self.config: ArbitrageConfig = config
        self._spread_history: List[float] = []
        self._in_position: bool = False
    
    def on_start(self):
        print(f"[ARBITRAGE] Pair: {self.config.symbol_a}/{self.config.symbol_b}")
    
    def on_tick(self, prices: Dict[str, float]):
        a, b = self.config.symbol_a, self.config.symbol_b
        if a not in prices or b not in prices or prices[b] == 0:
            return
        spread = prices[a] / prices[b]
        self._spread_history.append(spread)
        if len(self._spread_history) > self.config.lookback_window + 10:
            self._spread_history = self._spread_history[-(self.config.lookback_window + 10):]
        if len(self._spread_history) < self.config.lookback_window:
            return
        recent = self._spread_history[-self.config.lookback_window:]
        mean = sum(recent) / len(recent)
        std = math.sqrt(sum((s - mean) ** 2 for s in recent) / len(recent))
        z = (spread - mean) / std if std > 0 else 0
        if not self._in_position:
            if z > self.config.entry_threshold:
                self.sell(a, self.config.order_size, prices[a])
                self.buy(b, self.config.order_size, prices[b])
                self._in_position = True
            elif z < -self.config.entry_threshold:
                self.buy(a, self.config.order_size, prices[a])
                self.sell(b, self.config.order_size, prices[b])
                self._in_position = True
        elif abs(z) < self.config.exit_threshold:
            pos_a, pos_b = self.get_position(a), self.get_position(b)
            if pos_a > 0: self.sell(a, pos_a, prices[a])
            elif pos_a < 0: self.buy(a, abs(pos_a), prices[a])
            if pos_b > 0: self.sell(b, pos_b, prices[b])
            elif pos_b < 0: self.buy(b, abs(pos_b), prices[b])
            self._in_position = False
    
    def on_fill(self, fill):
        print(f"[ARBITRAGE] {self.config.symbol_a}={self.get_position(self.config.symbol_a)}, {self.config.symbol_b}={self.get_position(self.config.symbol_b)}")
