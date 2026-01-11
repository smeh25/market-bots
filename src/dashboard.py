"""Terminal dashboard for displaying trading bot status and P&L."""
import signal
import time
from datetime import datetime
from typing import List
from .base_bot import BaseBot


class Dashboard:
    def __init__(self, bots: List[BaseBot], title: str = "TRADING DASHBOARD"):
        self.bots = bots
        self.title = title
        self._running = False
        self._start_time = None
    
    def start_bots(self):
        print("Starting bots...")
        for bot in self.bots:
            bot.start_threaded()
            print(f"  Started: {self._get_name(bot)}")
        print("All bots running.\n")
        time.sleep(0.5)
    
    def run(self, refresh_interval: float = 1.0):
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)
        self._running = True
        self._start_time = time.time()
        while self._running:
            try:
                print("\033[H\033[J", end="")
                self._display()
                time.sleep(refresh_interval)
            except:
                time.sleep(refresh_interval)
    
    def stop(self):
        if not self._running:
            return
        self._running = False
        print("\nStopping bots...")
        for bot in self.bots:
            print(f"  Stopping: {self._get_name(bot)}")
            bot.stop()
        print("\nAll bots stopped.")
        self._final_summary()
    
    def _shutdown(self, sig, frame):
        self.stop()
    
    def _display(self):
        w = 65
        print("=" * w)
        print(f"| {self.title:^{w-4}} |")
        print("=" * w)
        elapsed = time.time() - self._start_time if self._start_time else 0
        print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}    Runtime: {int(elapsed//3600):02d}:{int(elapsed%3600//60):02d}:{int(elapsed%60):02d}")
        print("-" * w)
        for bot in self.bots:
            self._display_bot(bot, w)
        self._display_totals(w)
        print("\nPress Ctrl+C to stop")
    
    def _display_bot(self, bot, w):
        name = self._get_name(bot)
        print(f"\n+{'-'*(w-2)}+")
        print(f"| {name} (ID: {bot.config.client_id}){' '*(w-len(name)-len(str(bot.config.client_id))-10)}|")
        print(f"+{'-'*(w-2)}+")
        positions = bot.get_portfolio().get_active_positions()
        if positions:
            print(f"| {'POSITIONS:':<{w-4}} |")
            for sym, pos in positions.items():
                line = f"   {sym}: {pos.quantity:+d} shares @ ${pos.avg_cost:.2f} avg"
                print(f"| {line:<{w-4}} |")
        else:
            print(f"| {'No active positions':<{w-4}} |")
        print(f"+{'-'*(w-2)}+")
        r, u = bot.get_realized_pnl(), bot.get_unrealized_pnl()
        print(f"| {'P&L:':<{w-4}} |")
        print(f"|   {'Realized:':<15} {self._fmt(r):>20}   |")
        print(f"|   {'Unrealized:':<15} {self._fmt(u):>20}   |")
        print(f"|   {'Total:':<15} {self._fmt(r+u):>20}   |")
        print(f"+{'-'*(w-2)}+")
    
    def _display_totals(self, w):
        tr = sum(b.get_realized_pnl() for b in self.bots)
        tu = sum(b.get_unrealized_pnl() for b in self.bots)
        print(f"\n{'='*w}")
        print(f"  {'TOTAL REALIZED:':<20} {self._fmt(tr):>20}")
        print(f"  {'TOTAL UNREALIZED:':<20} {self._fmt(tu):>20}")
        print(f"  {'TOTAL P&L:':<20} {self._fmt(tr+tu):>20}")
        print("=" * w)
    
    def _final_summary(self):
        w = 65
        print(f"\n{'='*w}\n| {'FINAL SUMMARY':^{w-4}} |\n{'='*w}")
        tr, tu = 0.0, 0.0
        for bot in self.bots:
            r, u = bot.get_realized_pnl(), bot.get_unrealized_pnl()
            tr += r
            tu += u
            print(f"\n{self._get_name(bot)}:\n  Realized: {self._fmt(r)}\n  Unrealized: {self._fmt(u)}\n  Total: {self._fmt(r+u)}")
        print(f"\n{'-'*w}\nGRAND TOTAL: {self._fmt(tr+tu)}\n{'='*w}")
    
    def _get_name(self, bot):
        return bot.config.name if bot.config.name else bot.__class__.__name__
    
    def _fmt(self, amt):
        return f"${amt:,.2f}" if amt >= 0 else f"-${abs(amt):,.2f}"
