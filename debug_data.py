# Create debug_data.py
"""
Debug script to see what data we're getting
"""

from datetime import datetime
from data.feed import DataFeed
from dotenv import load_dotenv

load_dotenv()

# Get some data
feed = DataFeed(['AAPL', 'MSFT'])
data = feed.get_historical_data(days=10)

print("=== Data Debug ===\\n")

for symbol, prices in data.items():
    print(f"{symbol}:")
    print(f"  Total bars: {len(prices)}")
    
    if prices:
        print(f"  First date: {prices[0].timestamp}")
        print(f"  Last date: {prices[-1].timestamp}")
        print(f"  Days of data: {(prices[-1].timestamp - prices[0].timestamp).days + 1}")
        
        # Show all dates
        print("  All dates:")
        for p in prices:
            print(f"    {p.timestamp.date()}: Close ${p.close:.2f}")
    
    print()