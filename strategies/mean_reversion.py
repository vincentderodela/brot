""" Mean reversion Strategy implementation
Buys when price drops 10% in 7 days, sells when up 10%
"""
import logging  
from datetime import timedelta, datetime
from typing import Optional, Dict,List
import pandas as pd

from core.models import Signals, Signaltype, PriceData, Position
from config.settings import MEAN_REVERSION_CONFIG

logger = logging.getLogger(__name__)

class MeanReversionStrategy:
    """
    Implements the 10% mean reversion strategy
    """

    def __init__(self, lookback_days: int = none, drop_threshold: float = None):
        """ Initializes the strategy with parameters

        Args:
            lookback_days (int): The number of days to look back for price drops
            drop_threshold (float): The percentage drop threshold to trigger a buy signal
        """
        # Use provided values or defaults from config
        self.lookback_days = lookback_days or MEAN_REVERSION_CONFIG['LOOKBACK_DAYS']
        self.drop_threshold = drop_threshold or MEAN_REVERSION_CONFIG['DROP_THRESHOLD']
        self.gain_threshold = MEAN_REVERSION_CONFIG['GAIN_THRESHOLD']
        self.max_holdings_days = MEAN_REVERSION_CONFIG['MAX_HOLDINGS_DAYS']
        self.max_additions = MEAN_REVERSION_CONFIG['MAX_ADDITIONS']

        #track how many times we have added to each position
        self.addition_counts: Dict[str, int] = {}

        logger.info(f"Initialized MeanReversionStrategy with {self.lookback_days} day lookback")
    
    def calculate_returns(self, price_history: pd.DataFrame) -> pd.Series:
        """ 
        Calculate rolling returns fo all symbols

        Args:
            price_history: Dataframe with price data
        
        Returns:
            Series with returns for each symbols
        """
        # Calculate returns over lookback period
        current_prices = price_history.iloc[-1] # Last row
        past_prices = price_history.iloc[-self.lookback_days -1]

        returns = (current_prices - past_prices) / past_prices  
        return returns
    
    def analyze(self,
                price_data: Dict[str, List[PriceData]],
                positions: Dict[str, Position]) -> List[Signals]:
        """
        Analyze market data and generate trading signals
        
        Args:
            price_data: Dictionary of symbols -> List of PriceData
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

        if nor df_data:
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
                                    current_price: float) -> Optional[Signals]:
        """
        Generate signal for a single symbol
        
        Args:
            symbol: Stock symbol
            return_pct: Return percentage over the lookback period
            position: Current position, if any
            current_price: Current price
            
        Returns:
            Signals or None
        """
        timestamp = datetime.now()

        # Check if we have a position
        if position:
            # Check for sell conditions
            
            # 1.Position gained 10%
            if position.unrealized_pnl_percent >= self.gain_threshold * 100:
                return Signals(
                    timestamp=timestamp,
                    symbol=symbol,
                    signal_type=Signaltype.SELL,
                    strategy_name="MeanReversion",
                    confidence=0.8,
                    reason=f"Position up {position.unrealized_pnl_percent:.1f}% - taking profits"
                )
            
            # 2. Held for max holding period
            if position.days_held >= self.max_holdings_days:
                return Signals(
                    timestamp=timestamp,
                    symbol=symbol,
                    signal_type=Signaltype.SELL,
                    strategy_name="MeanReversion",
                    confidence=1,
                    reason=f"Position held for {position.days_held} days - max holding period reached"
                )
            # 3. Check if we should add to position
            if (return_pct <= -self.drop_threshold and
                self.position_addition.get(symbol, 0) < self.max_additions):

                return Signal(
                    timestamp=timestamp,
                    symbol=symbol,
                    signal_type=Signaltype.ADD_POSITION,
                    strategy_name="MeanReversion",
                    confidence=0.7,
                    reason=f"Adding to position - down {abs(return_pct)*100:.1f}% in {self.lookback_days} days",
                    metadata={'additions': self.position_addition.get(symbol, 0) + 1}
                )
            
        else:
            # No position, check for buy signal
            if return_pct <= -self.drop_threshold:
                return Signals(
                    timestamp=timestamp,
                    symbol=symbol,
                    signal_type=Signaltype.BUY,
                    strategy_name="MeanReversion",
                    confidence=0.8,
                    reason=f"Price dropped {abs(return_pct)*100:.1f}% in {self.lookback_days} days"
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
            self.positions_additions[symbol] =self.positions_additions.get(symbol, 0) + 1
        elif action == 'closed':
            self.position_additions.pop(symbol, None)

