"""VWAP/TWAP execution algorithm."""
import time
from dataclasses import dataclass
from typing import Dict, Optional
from .base_bot import BaseBot, BotConfig
from .enums import Side


@dataclass
class VWAPConfig(BotConfig):
    pass


@dataclass
class ExecutionOrder:
    symbol: str
    side: Side
    total_qty: int
    executed_qty: int = 0
    num_slices: int = 10
    slice_interval: float = 1.0
    start_time: float = 0.0
    last_slice_time: float = 0.0
    limit_price: Optional[float] = None


class VWAPBot(BaseBot):
    def __init__(self, config: VWAPConfig):
        super().__init__(config)
        self._execution: Optional[ExecutionOrder] = None
    
    def on_start(self):
        print("[VWAP] Ready")
    
    def execute(self, symbol: str, side: Side, total_qty: int, duration_seconds: float = 60.0, num_slices: int = 10, limit_price: Optional[float] = None):
        if self._execution:
            print("[VWAP] Already executing")
            return
        self._execution = ExecutionOrder(
            symbol=symbol, side=side, total_qty=total_qty, num_slices=num_slices,
            slice_interval=duration_seconds / num_slices, start_time=time.time(), limit_price=limit_price
        )
        print(f"[VWAP] Starting: {'BUY' if side == Side.BUY else 'SELL'} {total_qty} {symbol}")
    
    def on_tick(self, prices: Dict[str, float]):
        if not self._execution:
            return
        ex = self._execution
        now = time.time()
        if now - ex.last_slice_time < ex.slice_interval:
            return
        remaining = ex.total_qty - ex.executed_qty
        if remaining <= 0:
            self._complete()
            return
        slices_left = max(1, ex.num_slices - int(ex.executed_qty / (ex.total_qty / ex.num_slices)))
        qty = max(1, remaining // slices_left)
        price = ex.limit_price or prices.get(ex.symbol)
        if ex.side == Side.BUY:
            self.buy(ex.symbol, qty, price) if price else self.buy(ex.symbol, qty)
        else:
            self.sell(ex.symbol, qty, price) if price else self.sell(ex.symbol, qty)
        ex.executed_qty += qty
        ex.last_slice_time = now
        if ex.executed_qty >= ex.total_qty:
            self._complete()
    
    def on_fill(self, fill):
        if self._execution:
            print(f"[VWAP] Progress: {self._execution.executed_qty}/{self._execution.total_qty}")
    
    def _complete(self):
        if self._execution:
            print(f"[VWAP] Complete: {self._execution.total_qty} {self._execution.symbol}")
        self._execution = None
    
    def cancel_execution(self):
        if self._execution:
            print(f"[VWAP] Cancelled at {self._execution.executed_qty}/{self._execution.total_qty}")
        self._execution = None
    
    def is_executing(self) -> bool:
        return self._execution is not None
