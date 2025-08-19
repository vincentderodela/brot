"""
Test script for Brot components
Run this to verify everything is working
"""

import logging
import sys
from datetime import datetime

# Set up logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

print("=== Brot Component Tests ===")
print(f"Started at: {datetime.now()}\n")

# Test 1: Configuration
print("1. Testing Configuration...")
try:
    from config import settings
    print(f"✓ Environment: {settings.ENVIRONMENT}")
    print(f"✓ Trading Universe: {len(settings.TRADING_UNIVERSE)} symbols")
    print(f"✓ Check Interval: {settings.TRADING_CONFIG['CHECK_INTERVAL_SECONDS']}s")
except Exception as e:
    print(f"✗ Config Error: {e}")

# Test 2: Data Feed
print("\n2. Testing Data Feed...")
try:
    from data.feed import DataFeed
    
    # Test with just 2 symbols for speed
    feed = DataFeed(['AAPL', 'MSFT'])
    
    # Get latest prices
    prices = feed.get_latest_prices()
    
    if prices:
        for symbol, price_data in prices.items():
            print(f"✓ {symbol}: ${price_data.close:.2f}")
    else:
        print("✗ No price data received")
        
except Exception as e:
    print(f"✗ Data Feed Error: {e}")

# Test 3: Broker Connection
print("\n3. Testing Broker Connection...")
try:
    from execution.broker import AlpacaBroker
    
    broker = AlpacaBroker()
    account = broker.get_account_info()
    
    if account:
        print(f"✓ Cash Balance: ${account['cash']:,.2f}")
        print(f"✓ Buying Power: ${account['buying_power']:,.2f}")
        print(f"✓ Portfolio Value: ${account['portfolio_value']:,.2f}")
    else:
        print("✗ Could not get account info")
        
except Exception as e:
    print(f"✗ Broker Error: {e}")

# Test 4: Strategy
print("\n4. Testing Strategy...")
try:
    from strategies.mean_reversion import MeanReversionStrategy
    
    strategy = MeanReversionStrategy()
    print(f"✓ Strategy initialized")
    print(f"✓ Lookback days: {strategy.lookback_days}")
    print(f"✓ Drop threshold: {strategy.drop_threshold * 100}%")
    
except Exception as e:
    print(f"✗ Strategy Error: {e}")

print("\n=== Tests Complete ===")