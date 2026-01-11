"""
Position and P&L tracking for trading bots.
"""
import time
from dataclasses import dataclass, field
from typing import Dict, List

from .enums import Side


@dataclass
class Trade:
    """Record of a single trade."""
    symbol: str
    side: Side
    qty: int
    price: float
    realized_pnl: float = 0.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class Position:
    """Tracks holdings for a single symbol."""
    symbol: str
    quantity: int = 0
    avg_cost: float = 0.0
    realized_pnl: float = 0.0
    
    def update(self, side, fill_qty, fill_price):
        realized = 0.0
        signed_qty = fill_qty if side == Side.BUY else -fill_qty
        
        if self.quantity == 0:
            self.quantity = signed_qty
            self.avg_cost = float(fill_price)
        elif (self.quantity > 0 and signed_qty > 0) or (self.quantity < 0 and signed_qty < 0):
            old_value = abs(self.quantity) * self.avg_cost
            new_value = fill_qty * fill_price
            self.quantity = self.quantity + signed_qty
            self.avg_cost = (old_value + new_value) / abs(self.quantity)
        else:
            close_qty = min(fill_qty, abs(self.quantity))
            if self.quantity > 0:
                realized = close_qty * (fill_price - self.avg_cost)
            else:
                realized = close_qty * (self.avg_cost - fill_price)
            self.realized_pnl += realized
            old_quantity = self.quantity
            self.quantity = self.quantity + signed_qty
            if self.quantity != 0 and ((old_quantity > 0 and self.quantity < 0) or (old_quantity < 0 and self.quantity > 0)):
                self.avg_cost = float(fill_price)
            elif self.quantity == 0:
                self.avg_cost = 0.0
        return realized
    
    def unrealized_pnl(self, current_price):
        if self.quantity == 0:
            return 0.0
        if self.quantity > 0:
            return self.quantity * (current_price - self.avg_cost)
        return abs(self.quantity) * (self.avg_cost - current_price)
    
    def total_pnl(self, current_price):
        return self.realized_pnl + self.unrealized_pnl(current_price)


class Portfolio:
    """Tracks all positions and overall P&L for a bot."""
    
    def __init__(self):
        self._positions: Dict[str, Position] = {}
        self._trades: List[Trade] = []
    
    def get_position(self, symbol):
        if symbol not in self._positions:
            self._positions[symbol] = Position(symbol=symbol)
        return self._positions[symbol]
    
    def update(self, symbol, side, fill_qty, fill_price):
        position = self.get_position(symbol)
        realized = position.update(side, fill_qty, fill_price)
        self._trades.append(Trade(symbol=symbol, side=side, qty=fill_qty, price=fill_price, realized_pnl=realized))
        return realized
    
    def get_quantity(self, symbol):
        return self._positions[symbol].quantity if symbol in self._positions else 0
    
    def get_all_positions(self):
        return dict(self._positions)
    
    def get_active_positions(self):
        return {s: p for s, p in self._positions.items() if p.quantity != 0}
    
    def total_realized_pnl(self):
        return sum(p.realized_pnl for p in self._positions.values())
    
    def total_unrealized_pnl(self, prices):
        return sum(p.unrealized_pnl(prices[s]) for s, p in self._positions.items() if p.quantity != 0 and s in prices)
    
    def total_pnl(self, prices):
        return self.total_realized_pnl() + self.total_unrealized_pnl(prices)
    
    def get_trades(self):
        return list(self._trades)
    
    def summary(self, prices=None):
        lines = ["=" * 60, "PORTFOLIO SUMMARY", "=" * 60]
        active = self.get_active_positions()
        if active:
            lines.extend(["", "POSITIONS:", "-" * 60, f"{'Symbol':<10} {'Qty':>10} {'Avg Cost':>12} {'Realized':>12}", "-" * 60])
            for s, p in active.items():
                lines.append(f"{p.symbol:<10} {p.quantity:>10} {p.avg_cost:>12.2f} {p.realized_pnl:>12.2f}")
        else:
            lines.extend(["", "NO ACTIVE POSITIONS"])
        lines.extend(["", "-" * 60, f"{'Realized P&L:':<30} ${self.total_realized_pnl():>12.2f}"])
        if prices:
            unrealized = self.total_unrealized_pnl(prices)
            lines.extend([f"{'Unrealized P&L:':<30} ${unrealized:>12.2f}", f"{'Total P&L:':<30} ${self.total_realized_pnl() + unrealized:>12.2f}"])
        lines.append("=" * 60)
        return "\n".join(lines)
