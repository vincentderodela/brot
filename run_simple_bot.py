#!/usr/bin/env python3
"""
Simple bot test - let's see Brot in action!
"""

import logging
import sys
from datetime import datetime
from typing import Dict

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

from dotenv import load_dotenv
load_dotenv()

from data.feed import DataFeed
from strategies.mean_reversion import MeanReversionStrategy
from core.models import Position
from execution.broker import AlpacaBroker

logger = logging.getLogger(__name__)


def main():
    """Run a simple test of the bot"""
    print("=== Brot Simple Test ===")
    print(f"Started at: {datetime.now()}\n")
    
    # 1. Initialize components
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'META']
    
    print("1. Initializing components...")
    feed = DataFeed(symbols)
    strategy = MeanReversionStrategy()
    broker = AlpacaBroker()
    
    # 2. Get current positions
    print("\n2. Checking current positions...")
    positions = broker.get_positions()
    if positions:
        for symbol, pos in positions.items():
            print(f"   {symbol}: {pos.quantity} shares @ ${pos.avg_entry_price:.2f}")
    else:
        print("   No current positions")
    
    # 3. Get market data
    print("\n3. Fetching market data...")
    price_data = feed.get_historical_data(days=20)
    
    # 4. Run strategy
    print("\n4. Running strategy analysis...")
    signals = strategy.analyze(price_data, positions)
    
    # 5. Display signals
    print("\n5. Generated signals:")
    if signals:
        for signal in signals:
            print(f"   {signal.signal_type.value.upper()}: {signal.symbol}")
            print(f"   Reason: {signal.reason}")
            print(f"   Confidence: {signal.confidence}")
            print()
    else:
        print("   No signals generated")
    
    # 6. Show account info
    print("\n6. Account status:")
    account = broker.get_account_info()
    print(f"   Cash: ${account['cash']:,.2f}")
    print(f"   Portfolio Value: ${account['portfolio_value']:,.2f}")
    
    print("\n=== Test Complete ===")


if __name__ == "__main__":
    main()