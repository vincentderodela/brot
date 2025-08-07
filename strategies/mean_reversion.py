"""
Mean Reversion Strategy Implementation
Buys when price drops 10% in 7 days, sells when up 10%
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd

from core.models import Signal, SignalType, PriceData, Position
from config.settings import MEAN_REVERSION_CONFIG

logger = logging.getLogger(__name__)

class MeanReversionStrategy:
    """
    Implements the 10% mean reversion strategy
    
    This strategy looks for assets that have moved significantly
    from their recent average and bets they will revert
    """
    
    def __init__(self, lookback_days: int = None, drop_threshold: float = None):
        """
        Initialize strategy with parameters
        
        Args:
            lookback_days: Days to look back for price comparison
            drop_threshold: Percentage drop to trigger buy signal
        """
        # Use provided values or defaults from config
        self.lookback_days = lookback_days or MEAN_REVERSION_CONFIG['LOOKBACK_DAYS']
        self.drop_threshold = drop_threshold or MEAN_REVERSION_CONFIG['DROP_THRESHOLD']
        self.gain_threshold = MEAN_REVERSION_CONFIG['GAIN_THRESHOLD']
        self.max_holding_days = MEAN_REVERSION_CONFIG['MAX_HOLDING_DAYS']
        self.max_additions = MEAN_REVERSION_CONFIG['MAX_ADDITIONS']
        
        # Track how many times we've added to each position
        self.position_additions: Dict[str, int] = {}
        
        logger.info(f"Initialized MeanReversionStrategy with {self.lookback_days} day lookback")
    
    def calculate_returns(self, price_history: pd.DataFrame) -> pd.Series:
        """
        Calculate rolling returns for all symbols
        
        Args:
            price_history: DataFrame with price data
            
        Returns:
            Series with returns for each symbol
        """
        # Calculate returns over lookback period
        current_prices = price_history.iloc[-1]  # Last row
        past_prices = price_history.iloc[-self.lookback_days - 1]
        
        returns = (current_prices - past_prices) / past_prices
        return returns
    
    def analyze(self, 
                price_data: Dict[str, List[PriceData]], 
                positions: Dict[str, Position]) -> List[Signal]:
        """
        Analyze market data and generate trading signals
        
        Args:
            price_data: Dictionary of symbol -> list of recent PriceData
            positions: Current positions
            
        Returns:
            List of trading signals
        """
        signals = []
        
        # Convert price data to DataFrame for easier analysis
        # This is where pandas shines!
        df_data = {}
        
        for symbol, prices in price_data.items():
            if len(prices) < self.lookback_days + 1:
                logger.warning(f"Insufficient data for {symbol}, skipping")
                continue
                
            # Extract closing prices
            df_data[symbol] = [p.close for p in prices]
        
        if not df_data:
            return signals
        
        # Create DataFrame with symbols as columns
        df = pd.DataFrame(df_data)
        
        # Calculate returns
        returns = self.calculate_returns(df)
        
        # Generate signals
        for symbol, return_pct in returns.items():
            signal = self._generate_signal_for_symbol(
                symbol, return_pct, positions.get(symbol), df[symbol].iloc[-1]
            )
            
            if signal:
                signals.append(signal)
        
        return signals
    
    def _generate_signal_for_symbol(self,
                                   symbol: str,
                                   return_pct: float,
                                   position: Optional[Position],
                                   current_price: float) -> Optional[Signal]:
        """
        Generate signal for a single symbol
        
        Args:
            symbol: Stock symbol
            return_pct: Return percentage over lookback period
            position: Current position (if any)
            current_price: Current price
            
        Returns:
            Signal or None
        """
        timestamp = datetime.now()
        
        # Check if we have a position
        if position:
            # Check for sell conditions
            
            # 1. Position gained 10%
            if position.unrealized_pnl_percent >= self.gain_threshold * 100:
                return Signal(
                    timestamp=timestamp,
                    symbol=symbol,
                    signal_type=SignalType.SELL,
                    strategy_name="MeanReversion",
                    confidence=0.8,
                    reason=f"Position up {position.unrealized_pnl_percent:.1f}% - taking profits"
                )
            
            # 2. Held for max holding period
            if position.days_held >= self.max_holding_days:
                return Signal(
                    timestamp=timestamp,
                    symbol=symbol,
                    signal_type=SignalType.SELL,
                    strategy_name="MeanReversion",
                    confidence=1.0,
                    reason=f"Position held for {position.days_held} days - max holding period reached"
                )
            
            # 3. Check if we should add to position
            if (return_pct <= -self.drop_threshold and 
                self.position_additions.get(symbol, 0) < self.max_additions):
                
                return Signal(
                    timestamp=timestamp,
                    symbol=symbol,
                    signal_type=SignalType.ADD_POSITION,
                    strategy_name="MeanReversion",
                    confidence=0.7,
                    reason=f"Adding to position - down {abs(return_pct)*100:.1f}% in {self.lookback_days} days",
                    metadata={'additions': self.position_additions.get(symbol, 0) + 1}
                )
        
        else:
            # No position - check for buy signal
            if return_pct <= -self.drop_threshold:
                return Signal(
                    timestamp=timestamp,
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    strategy_name="MeanReversion",
                    confidence=0.8,
                    reason=f"Price dropped {abs(return_pct)*100:.1f}% in {self.lookback_days} days",
                    metadata={'entry_price': current_price}
                )
        
        return None
    
    def update_position_tracking(self, symbol: str, action: str):
        """
        Update internal tracking when positions change
        
        Args:
            symbol: Stock symbol
            action: 'opened', 'added', 'closed'
        """
        if action == 'opened':
            self.position_additions[symbol] = 0
        elif action == 'added':
            self.position_additions[symbol] = self.position_additions.get(symbol, 0) + 1
        elif action == 'closed':
            self.position_additions.pop(symbol, None)