"""
Check actual price movements in our data
"""

from datetime import datetime
from data.feed import DataFeed
from dotenv import load_dotenv

load_dotenv()

symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'META']
feed = DataFeed(symbols)
data = feed.get_historical_data(days=20)

print("=== 7-Day Price Movements ===\\n")

for symbol, prices in data.items():
    if len(prices) >= 8:
        # Get prices from 7 days ago and today
        current_price = prices[-1].close
        week_ago_price = prices[-8].close
        
        # Calculate percentage change
        change = ((current_price - week_ago_price) / week_ago_price) * 100
        
        print(f"{symbol}:")
        print(f"  7 days ago: ${week_ago_price:.2f}")
        print(f"  Current: ${current_price:.2f}")
        print(f"  Change: {change:+.2f}%")
        
        if change <= -10:
            print("  *** BUY SIGNAL! ***")
        elif change >= 10:
            print("  *** SELL SIGNAL! ***")
        
        print()