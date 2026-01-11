"""Mean reversion trading strategy using z-score."""
import math
from dataclasses import dataclass
from typing import Dict, List, Optional
from .base_bot import BaseBot, BotConfig


@dataclass
class MeanReversionConfig(BotConfig):
    lookback_window: int = 20
    entry_threshold: float = 2.0
    exit_threshold: float = 0.5
    order_size: int = 10
    max_position: int = 100


class MeanReversionBot(BaseBot):
    def __init__(self, config: MeanReversionConfig):
        super().__init__(config)
        self.config: MeanReversionConfig = config
        self._price_history: Dict[str, List[float]] = {}
    
    def on_start(self):
        print(f"[MEAN_REV] Starting: {self.config.symbols}")
    
    def on_tick(self, prices: Dict[str, float]):
        for symbol in self.config.symbols:
            if symbol not in prices:
                continue
            price = prices[symbol]
            if symbol not in self._price_history:
                self._price_history[symbol] = []
            self._price_history[symbol].append(price)
            if len(self._price_history[symbol]) > self.config.lookback_window + 10:
                self._price_history[symbol] = self._price_history[symbol][-(self.config.lookback_window + 10):]
            history = self._price_history[symbol]
            if len(history) < self.config.lookback_window:
                continue
            recent = history[-self.config.lookback_window:]
            mean = sum(recent) / len(recent)
            std = math.sqrt(sum((p - mean) ** 2 for p in recent) / len(recent))
            z = (price - mean) / std if std > 0 else 0
            position = self.get_position(symbol)
            if position == 0:
                if z < -self.config.entry_threshold:
                    self.buy(symbol, self.config.order_size, price)
                elif z > self.config.entry_threshold:
                    self.sell(symbol, self.config.order_size, price)
            else:
                if abs(z) < self.config.exit_threshold:
                    if position > 0:
                        self.sell(symbol, position, price)
                    else:
                        self.buy(symbol, abs(position), price)
    
    def on_fill(self, fill):
        print(f"[MEAN_REV] {fill.symbol} position: {self.get_position(fill.symbol)}")
