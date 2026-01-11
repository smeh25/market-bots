"""Momentum trading strategy using moving average crossover."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from .base_bot import BaseBot, BotConfig


@dataclass
class MomentumConfig(BotConfig):
    short_window: int = 5
    long_window: int = 20
    order_size: int = 10
    max_position: int = 100


class MomentumBot(BaseBot):
    def __init__(self, config: MomentumConfig):
        super().__init__(config)
        self.config: MomentumConfig = config
        self._price_history: Dict[str, List[float]] = {}
        self._signal: Dict[str, Optional[str]] = {}
    
    def on_start(self):
        print(f"[MOMENTUM] Starting: {self.config.symbols}")
    
    def on_tick(self, prices: Dict[str, float]):
        for symbol in self.config.symbols:
            if symbol not in prices:
                continue
            price = prices[symbol]
            if symbol not in self._price_history:
                self._price_history[symbol] = []
            self._price_history[symbol].append(price)
            if len(self._price_history[symbol]) > self.config.long_window + 10:
                self._price_history[symbol] = self._price_history[symbol][-(self.config.long_window + 10):]
            history = self._price_history[symbol]
            if len(history) < self.config.long_window:
                continue
            short_ma = sum(history[-self.config.short_window:]) / self.config.short_window
            long_ma = sum(history[-self.config.long_window:]) / self.config.long_window
            new_signal = "long" if short_ma > long_ma else "short"
            if new_signal != self._signal.get(symbol):
                self._signal[symbol] = new_signal
                position = self.get_position(symbol)
                if new_signal == "long":
                    if position < 0:
                        self.buy(symbol, abs(position), price)
                    if position < self.config.max_position:
                        qty = min(self.config.order_size, self.config.max_position - max(0, position))
                        if qty > 0:
                            self.buy(symbol, qty, price)
                else:
                    if position > 0:
                        self.sell(symbol, position, price)
    
    def on_fill(self, fill):
        print(f"[MOMENTUM] {fill.symbol} position: {self.get_position(fill.symbol)}")
