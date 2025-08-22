# Replace test_free_data.py with this corrected version:

"""
Test data feed with free IEX data
"""

from datetime import datetime, timedelta
from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
import os
from dotenv import load_dotenv

load_dotenv()

# Get credentials
api_key = os.getenv('ALPACA_API_KEY')
secret_key = os.getenv('ALPACA_SECRET_KEY')

print("Testing Alpaca Free Data Access...\n")

# Create client with authentication (required even for free data)
client = StockHistoricalDataClient(
    api_key=api_key,      # Use your credentials
    secret_key=secret_key,
    raw_data=False
)

# Test 1: Get latest daily bars (always free)
print("1. Testing daily data (always free):")
request = StockBarsRequest(
    symbol_or_symbols=['AAPL', 'MSFT'],
    timeframe=TimeFrame.Day,
    start=datetime.now() - timedelta(days=5),
    end=datetime.now(),
    feed='iex'
)

try:
    bars = client.get_stock_bars(request)
    df = bars.df
    print(f"✓ Got {len(df)} daily bars")
    if not df.empty:
        # Show latest data
        for symbol in ['AAPL', 'MSFT']:
            if symbol in df.index.get_level_values('symbol'):
                symbol_data = df.xs(symbol, level='symbol')
                latest = symbol_data.iloc[-1]
                print(f"  {symbol}: ${latest['close']:.2f} (from {symbol_data.index[-1]})")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 2: Get minute data with IEX feed
print("\n2. Testing minute data with IEX feed:")
request = StockBarsRequest(
    symbol_or_symbols=['AAPL', 'MSFT'],
    timeframe=TimeFrame.Minute,
    start=datetime.now() - timedelta(hours=2),
    end=datetime.now(),
    feed='iex'  # Specify IEX feed
)

try:
    bars = client.get_stock_bars(request)
    df = bars.df
    print(f"✓ Got {len(df)} minute bars")
    print("  (Note: IEX data has 15-minute delay)")
except Exception as e:
    print(f"✗ Error: {e}")