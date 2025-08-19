"""
Broker interface for Brot Trading Robot
Handles communication with Alpaca API
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
import os

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.common.exceptions import APIError

from core.models import Order, OrderStatus, OrderType, Position, Trade
from config.settings import IS_PRODUCTION

logger = logging.getLogger(__name__)


class AlpacaBroker:
    """
    Broker interface for Alpaca
    
    This class handles all communication with the Alpaca API
    including placing orders, checking positions, and account info
    """
    
    def __init__(self):
        """Initialize Alpaca client"""
        # Get API credentials from environment
        api_key = os.getenv('ALPACA_API_KEY')
        secret_key = os.getenv('ALPACA_SECRET_KEY')
        
        if not api_key or not secret_key:
            raise ValueError("Alpaca API credentials not found in environment")
        
        # Initialize trading client
        # paper=True means we're using paper trading
        self.client = TradingClient(
            api_key=api_key,
            secret_key=secret_key,
            paper=not IS_PRODUCTION  # Use paper trading unless in production
        )
        
        logger.info(f"AlpacaBroker initialized (paper_trading={not IS_PRODUCTION})")
        
        # Get account info
        self.account = self.client.get_account()
        logger.info(f"Account balance: ${float(self.account.cash):,.2f}")
    
    def place_order(self, order: Order) -> Optional[str]:
        """
        Place an order with Alpaca
        
        Args:
            order: Order object to place
            
        Returns:
            Order ID if successful, None if failed
        """
        try:
            # Create order request based on type
            if order.order_type == OrderType.MARKET:
                order_data = MarketOrderRequest(
                    symbol=order.symbol,
                    qty=order.quantity,
                    side=OrderSide.BUY if order.side.value == "buy" else OrderSide.SELL,
                    time_in_force=TimeInForce.DAY
                )
            else:
                # For now, only support market orders
                logger.error(f"Order type {order.order_type} not implemented yet")
                return None
            
            # Submit order
            alpaca_order = self.client.submit_order(order_data)
            
            logger.info(f"Order placed: {alpaca_order.id} - "
                       f"{order.side.value} {order.quantity} {order.symbol}")
            
            return alpaca_order.id
            
        except APIError as e:
            logger.error(f"Alpaca API error placing order: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error placing order: {e}")
            return None
    
    def get_positions(self) -> Dict[str, Position]:
        """
        Get all current positions
        
        Returns:
            Dictionary of symbol -> Position
        """
        positions = {}
        
        try:
            alpaca_positions = self.client.get_all_positions()
            
            for pos in alpaca_positions:
                position = Position(
                    symbol=pos.symbol,
                    quantity=float(pos.qty),
                    avg_entry_price=float(pos.avg_entry_price),
                    current_price=float(pos.current_price or 0),
                    opened_at=datetime.now(),  # Alpaca doesn't provide this
                    last_updated=datetime.now()
                )
                positions[pos.symbol] = position
                
            logger.debug(f"Retrieved {len(positions)} positions")
            
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            
        return positions
    
    def get_account_info(self) -> Dict[str, float]:
        """
        Get account information
        
        Returns:
            Dictionary with account details
        """
        try:
            account = self.client.get_account()
            
            return {
                'cash': float(account.cash),
                'buying_power': float(account.buying_power),
                'portfolio_value': float(account.portfolio_value),
                'day_trade_count': int(account.daytrade_count),
                'pattern_day_trader': account.pattern_day_trader
            }
            
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return {}
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order
        
        Args:
            order_id: Alpaca order ID
            
        Returns:
            True if successful
        """
        try:
            self.client.cancel_order_by_id(order_id)
            logger.info(f"Cancelled order {order_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False