"""
Order management module for Brot Trading Robot
Handles order creation, tracking, and execution
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

from core.models import Order, OrderStatus, OrderType, OrderSide, Signal, SignalType
from config.settings import TRADING_CONFIG

logger = logging.getLogger(__name__)

@dataclass
class OrderRequest:
    """
    Represents a request to place an order
    This is what we send to the broker
    """
    symbol: str
    side: OrderSide
    quantity: float
    order_type: OrderType = OrderType.MARKET
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    
    def validate(self) -> bool:
        """
        Validate the order request
        
        Returns:
            True if valid, raises ValueError if not
        """
        if self.quantity <= 0:
            raise ValueError(f"Quantity must be positive, got {self.quantity}")
            
        if self.order_type == OrderType.LIMIT and self.limit_price is None:
            raise ValueError("Limit orders require a limit price")
            
        if self.order_type in [OrderType.STOP, OrderType.STOP_LIMIT] and self.stop_price is None:
            raise ValueError("Stop orders require a stop price")
            
        return True

class OrderManager:
    """
    Manages order lifecycle and execution
    
    Responsibilities:
    1. Convert signals to order requests
    2. Track order status
    3. Handle order fills
    """
    
    def __init__(self, capital: float = 10000.0):
        """
        Initialize order manager
        
        Args:
            capital: Starting capital for position sizing
        """
        self.capital = capital
        self.available_capital = capital
        self.pending_orders: Dict[str, Order] = {}  # order_id -> Order
        self.order_history: List[Order] = []
        
        logger.info(f"OrderManager initialized with ${capital:,.2f} capital")

    def process_signal(self, signal: Signal, current_price: float) -> Optional[OrderRequest]:
        """
        Convert a trading signal into an order request
        
        Args:
            signal: Trading signal from strategy
            current_price: Current market price
            
        Returns:
            OrderRequest if signal should be executed, None otherwise
        """
        # Skip low confidence signals
        if signal.confidence < 0.5:
            logger.debug(f"Skipping low confidence signal: {signal.confidence}")
            return None
            
        # Calculate position size
        position_size = self._calculate_position_size(signal, current_price)
        
        if position_size == 0:
            logger.warning(f"No capital available for {signal.symbol}")
            return None
            
        # Create order request based on signal type
        if signal.signal_type == SignalType.BUY:
            return OrderRequest(
                symbol=signal.symbol,
                side=OrderSide.BUY,
                quantity=position_size,
                order_type=OrderType.MARKET
            )
            
        elif signal.signal_type == SignalType.SELL:
            return OrderRequest(
                symbol=signal.symbol,
                side=OrderSide.SELL,
                quantity=position_size,  # Should be from actual position
                order_type=OrderType.MARKET
            )
            
        return None
    
    def _calculate_position_size(self, signal: Signal, current_price: float) -> float:
        """
        Calculate how many shares to buy/sell
        
        Args:
            signal: Trading signal
            current_price: Current stock price
            
        Returns:
            Number of shares (can be fractional)
        """
        # Use percentage of capital per position
        position_value = self.available_capital * (TRADING_CONFIG['POSITION_SIZE_PERCENT'] / 100)
        
        # Don't exceed available capital
        position_value = min(position_value, self.available_capital)
        
        # Calculate shares
        shares = position_value / current_price
        
        # Round to 2 decimal places (Alpaca supports fractional shares)
        return round(shares, 2)
    
    def create_order(self, request: OrderRequest) -> Order:
        """
        Create an order from request
        
        Args:
            request: Validated order request
            
        Returns:
            Order object ready to send to broker
        """
        # Validate first
        request.validate()
        
        # Generate order ID (in production, broker provides this)
        order_id = f"ORD_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{request.symbol}"
        
        # Create order
        order = Order(
            symbol=request.symbol,
            side=request.side,
            order_type=request.order_type,
            quantity=request.quantity,
            price=request.limit_price,
            stop_price=request.stop_price,
            order_id=order_id,
            submitted_at=datetime.now()
        )
        
        # Track the order
        self.pending_orders[order_id] = order
        
        # Reserve capital
        if order.side == OrderSide.BUY:
            estimated_cost = order.quantity * (request.limit_price or 0)  # Use 0 for market orders temporarily
            self.available_capital -= estimated_cost
            
        logger.info(f"Created order: {order_id} - {order.side.value} {order.quantity} {order.symbol}")
        
        return order