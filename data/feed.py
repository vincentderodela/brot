"""
Data feed module for Brot Trading Robot
Handles fetching and caching price data from Alpaca
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Deque
from collections import deque, defaultdict
import pandas as pd
import os

# Import Alpaca's trading client
from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

# Import our own models
from core.models import PriceData
from config.settings import TRADING_UNIVERSE, MEAN_REVERSION_CONFIG

# Set up logging for this module
logger = logging.getLogger(__name__)


class DataFeed:
    """
    Manages real-time and historical price data
    
    This class is responsible for:
    1. Fetching data from Alpaca API
    2. Caching recent data in memory
    3. Converting raw data to our PriceData format
    """
    
    def __init__(self, symbols: List[str] = None):
        """
        Initialize the data feed
        
        Args:
            symbols: List of symbols to track. If None, uses TRADING_UNIVERSE
        """
        # Use provided symbols or default to our trading universe
        self.symbols = symbols or TRADING_UNIVERSE
        
        # Cache to store recent price data for each symbol
        # defaultdict automatically creates a new deque if key doesn't exist
        # deque = "double-ended queue" - efficient for adding/removing from ends
        self.price_cache: Dict[str, Deque[PriceData]] = defaultdict(
            lambda: deque(maxlen=MEAN_REVERSION_CONFIG['LOOKBACK_DAYS'] + 10)
            # maxlen automatically removes old items when full
        )
        
        # Initialize Alpaca client for data
        # Using environment variables for API keys (secure practice)
        api_key = os.getenv('ALPACA_API_KEY')
        secret_key = os.getenv('ALPACA_SECRET_KEY')
        
        if not api_key or not secret_key:
            # For paper trading, we can use free data
            logger.warning("No API keys found, using free tier data")
            self.client = StockHistoricalDataClient(
                api_key=None,
                secret_key=None,
                raw_data=False  # Get data as pandas DataFrame
            )
        else:
            self.client = StockHistoricalDataClient(
                api_key=api_key,
                secret_key=secret_key,
                raw_data=False
            )
        
        logger.info(f"DataFeed initialized for {len(self.symbols)} symbols")
    
    def get_latest_prices(self) -> Dict[str, PriceData]:
        """
        Get the most recent price for each symbol
        
        Returns:
            Dictionary mapping symbol to latest PriceData
            
        Example return:
            {
                'AAPL': PriceData(symbol='AAPL', close=150.00, ...),
                'MSFT': PriceData(symbol='MSFT', close=300.00, ...)
            }
        """
        latest_prices = {}
        
        # Get data from the last 2 minutes to ensure we have recent data
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=2)
        
        try:
            # Create request for 1-minute bars
            request = StockBarsRequest(
                symbol_or_symbols=self.symbols,  # Can pass list of symbols
                timeframe=TimeFrame.Minute,       # 1-minute candles
                start=start_time,
                end=end_time
            )
            
            # Fetch from Alpaca
            bars_df = self.client.get_stock_bars(request).df
            
            # Process each symbol
            for symbol in self.symbols:
                if symbol in bars_df.index.get_level_values('symbol'):
                    # Get the most recent bar for this symbol
                    symbol_data = bars_df.xs(symbol, level='symbol')
                    if not symbol_data.empty:
                        # Take the last (most recent) row
                        latest_bar = symbol_data.iloc[-1]
                        
                        # Convert to our PriceData format
                        price_data = self._convert_bar_to_price_data(
                            symbol=symbol,
                            bar=latest_bar,
                            timestamp=symbol_data.index[-1]
                        )
                        
                        latest_prices[symbol] = price_data
                        
                        # Add to cache
                        self.price_cache[symbol].append(price_data)
            
            logger.debug(f"Fetched latest prices for {len(latest_prices)} symbols")
            
        except Exception as e:
            logger.error(f"Error fetching latest prices: {e}")
            # Return cached data if available
            for symbol in self.symbols:
                if self.price_cache[symbol]:
                    latest_prices[symbol] = self.price_cache[symbol][-1]
        
        return latest_prices
    
    def get_historical_data(self, days: int = None) -> Dict[str, List[PriceData]]:
        """
        Get historical price data for analysis
        
        Args:
            days: Number of days of history to fetch.
                  Defaults to LOOKBACK_DAYS + 1
        
        Returns:
            Dictionary mapping symbol to list of PriceData objects
            
        The returned data structure looks like:
        {
            'AAPL': [PriceData(...), PriceData(...), ...],
            'MSFT': [PriceData(...), PriceData(...), ...]
        }
        """
        # Default to lookback period plus one extra day
        days = days or (MEAN_REVERSION_CONFIG['LOOKBACK_DAYS'] + 1)
        
        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        historical_data = {}
        
        try:
            # Create request for daily bars
            request = StockBarsRequest(
                symbol_or_symbols=self.symbols,
                timeframe=TimeFrame.Day,  # Daily candles for historical
                start=start_time,
                end=end_time
            )
            
            # Fetch from Alpaca
            bars_df = self.client.get_stock_bars(request).df
            
            # Process each symbol
            for symbol in self.symbols:
                if symbol in bars_df.index.get_level_values('symbol'):
                    # Extract data for this symbol
                    symbol_data = bars_df.xs(symbol, level='symbol')
                    
                    # Convert each row to PriceData
                    price_list = []
                    for timestamp, bar in symbol_data.iterrows():
                        price_data = self._convert_bar_to_price_data(
                            symbol=symbol,
                            bar=bar,
                            timestamp=timestamp
                        )
                        price_list.append(price_data)
                    
                    historical_data[symbol] = price_list
                    
                    # Update cache with historical data
                    self.price_cache[symbol].extend(price_list)
            
            logger.info(f"Fetched {days} days of history for {len(historical_data)} symbols")
            
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            # Return cached data
            for symbol in self.symbols:
                if self.price_cache[symbol]:
                    historical_data[symbol] = list(self.price_cache[symbol])
        
        return historical_data
    
    def _convert_bar_to_price_data(self, 
                                   symbol: str, 
                                   bar: pd.Series, 
                                   timestamp: datetime) -> PriceData:
        """
        Convert Alpaca bar data to our PriceData format
        
        Args:
            symbol: Stock symbol
            bar: Pandas Series with OHLCV data
            timestamp: Timestamp for this bar
            
        Returns:
            PriceData object
            
        This is a "private" method (indicated by _ prefix)
        It's only used internally by this class
        """
        return PriceData(
            symbol=symbol,
            timestamp=timestamp,
            open=float(bar['open']),      # Convert to float to ensure type
            high=float(bar['high']),
            low=float(bar['low']),
            close=float(bar['close']),
            volume=int(bar['volume'])     # Convert to int for volume
        )
    
    def update_symbols(self, symbols: List[str]):
        """
        Update the list of symbols to track
        
        Args:
            symbols: New list of symbols
            
        This method allows dynamic updating of what we're tracking
        """
        old_symbols = set(self.symbols)
        new_symbols = set(symbols)
        
        # Find symbols that were removed
        removed = old_symbols - new_symbols
        
        # Clear cache for removed symbols
        for symbol in removed:
            self.price_cache.pop(symbol, None)
        
        # Update symbol list
        self.symbols = symbols
        
        logger.info(f"Updated symbols. Now tracking {len(self.symbols)} symbols")
    
    def clear_cache(self, symbol: str = None):
        """
        Clear cached data
        
        Args:
            symbol: If provided, clear only this symbol's cache.
                   If None, clear all cached data.
        """
        if symbol:
            self.price_cache[symbol].clear()
            logger.debug(f"Cleared cache for {symbol}")
        else:
            self.price_cache.clear()
            logger.debug("Cleared all cached data")