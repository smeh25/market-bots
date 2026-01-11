"""Example: Running multiple bots with a dashboard."""
from src import Dashboard, MomentumBot, MomentumConfig, MeanReversionBot, MeanReversionConfig, ArbitrageBot, ArbitrageConfig

def main():
    bots = [
        MomentumBot(MomentumConfig(client_id=1, name="Momentum AAPL/MSFT", symbols=["AAPL", "MSFT"], short_window=5, long_window=20, order_size=10)),
        MeanReversionBot(MeanReversionConfig(client_id=2, name="MeanRev GOOGL", symbols=["GOOGL"], lookback_window=20, entry_threshold=2.0, exit_threshold=0.5, order_size=10)),
        ArbitrageBot(ArbitrageConfig(client_id=3, name="Arbitrage AAPL/MSFT", symbol_a="AAPL", symbol_b="MSFT", entry_threshold=2.0, exit_threshold=0.5, order_size=10)),
    ]
    dashboard = Dashboard(bots, title="MY TRADING BOTS")
    dashboard.start_bots()
    dashboard.run(refresh_interval=1.0)

if __name__ == "__main__":
    main()
