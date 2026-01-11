"""
Base class for trading bots.
"""
import signal
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .enums import Side
from .exchange_client import ExchangeClient
from .position import Portfolio


@dataclass
class BotConfig:
    """Configuration for a trading bot."""
    client_id: int
    name: str = ""
    host: str = "localhost"
    send_port: int = 5555
    recv_port: int = 5556
    tick_interval: float = 1.0
    symbols: List[str] = field(default_factory=list)


class BaseBot(ABC):
    """Base class for trading bots."""
    
    def __init__(self, config: BotConfig):
        self.config = config
        self.client = ExchangeClient(config.client_id, config.host, config.send_port, config.recv_port)
        self.portfolio = Portfolio()
        self._last_prices: Dict[str, float] = {}
        self._running = False
        self._bot_thread: Optional[threading.Thread] = None
        self.client.on_ack(self._internal_on_ack)
        self.client.on_reject(self._internal_on_reject)
        self.client.on_fill(self._internal_on_fill)
    
    def start(self):
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        self._start_internal()
        self._run_loop()
    
    def start_threaded(self):
        self._start_internal()
        self._bot_thread = threading.Thread(target=self._run_loop, daemon=True)
        self._bot_thread.start()
    
    def _start_internal(self):
        self.client.connect()
        self.client.start()
        self._running = True
        self.on_start()
    
    def stop(self):
        if not self._running:
            return
        self._running = False
        self.on_stop()
        if self._bot_thread and self._bot_thread.is_alive():
            self._bot_thread.join(timeout=2.0)
        self.client.disconnect()
    
    def _run_loop(self):
        while self._running:
            try:
                self.on_tick(self._get_prices())
                time.sleep(self.config.tick_interval)
            except Exception as e:
                if self._running:
                    print(f"[BOT] Error: {e}")
    
    def _handle_shutdown(self, signum, frame):
        print("\n[BOT] Shutting down...")
        self.stop()
    
    @abstractmethod
    def on_tick(self, prices: Dict[str, float]):
        pass
    
    @abstractmethod
    def on_fill(self, fill):
        pass
    
    def on_start(self):
        pass
    
    def on_stop(self):
        pass
    
    def on_ack(self, ack):
        pass
    
    def on_reject(self, reject):
        pass
    
    def _internal_on_fill(self, fill):
        self._last_prices[fill.symbol] = fill.fill_price
        self.portfolio.update(fill.symbol, fill.side, fill.fill_qty, fill.fill_price)
        self.on_fill(fill)
    
    def _internal_on_ack(self, ack):
        self.on_ack(ack)
    
    def _internal_on_reject(self, reject):
        self.on_reject(reject)
    
    def buy(self, symbol: str, qty: int, price: Optional[float] = None) -> int:
        if price is None:
            return self.client.send_market_order(symbol, Side.BUY, qty)
        return self.client.send_limit_order(symbol, Side.BUY, qty, int(price))
    
    def sell(self, symbol: str, qty: int, price: Optional[float] = None) -> int:
        if price is None:
            return self.client.send_market_order(symbol, Side.SELL, qty)
        return self.client.send_limit_order(symbol, Side.SELL, qty, int(price))
    
    def cancel(self, symbol: str, client_order_id: int):
        self.client.cancel_order(symbol, client_order_id)
    
    def get_position(self, symbol: str) -> int:
        return self.portfolio.get_quantity(symbol)
    
    def get_portfolio(self) -> Portfolio:
        return self.portfolio
    
    def get_realized_pnl(self) -> float:
        return self.portfolio.total_realized_pnl()
    
    def get_unrealized_pnl(self) -> float:
        return self.portfolio.total_unrealized_pnl(self._get_prices())
    
    def get_total_pnl(self) -> float:
        return self.get_realized_pnl() + self.get_unrealized_pnl()
    
    def _get_prices(self) -> Dict[str, float]:
        return dict(self._last_prices)
    
    def get_price(self, symbol: str) -> Optional[float]:
        return self._last_prices.get(symbol)
    
    def update_price(self, symbol: str, price: float):
        self._last_prices[symbol] = price
    
    def update_prices(self, prices: Dict[str, float]):
        self._last_prices.update(prices)
    
    def get_pending_orders(self) -> dict:
        return self.client.get_pending_orders()
    
    def is_running(self) -> bool:
        return self._running
