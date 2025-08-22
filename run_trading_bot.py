#!/usr/bin/env python3
"""
Complete trading bot that analyzes and executes trades
"""

import logging
import sys
import time
import json
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

from dotenv import load_dotenv
load_dotenv()

from data.feed import DataFeed
from strategies.mean_reversion import MeanReversionStrategy
from execution.broker import AlpacaBroker
from execution.orders import OrderManager
from config import settings
from core.models import Order, OrderSide, OrderType, OrderStatus  # Added OrderStatus

logger = logging.getLogger(__name__)

def log_trade(action, symbol, quantity, price, reason):
    """Log trades to file"""
    # Create logs directory if it doesn't exist
    import os
    os.makedirs('logs', exist_ok=True)
    
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'action': action,
        'symbol': symbol,
        'quantity': quantity,
        'price': price,
        'reason': reason
    }
    
    with open('logs/trades.json', 'a') as f:
        f.write(json.dumps(log_entry) + '\n')


def execute_trading_cycle():
    """Execute one complete trading cycle"""
    
    print(f"\n{'='*50}")
    print(f"Trading Cycle - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")
    
    # Initialize components
    symbols = settings.TRADING_UNIVERSE[:10]  # Use first 10 symbols
    feed = DataFeed(symbols)
    strategy = MeanReversionStrategy()
    broker = AlpacaBroker()
    
    # Get account info
    account = broker.get_account_info()
    order_manager = OrderManager(capital=account['cash'])
    
    print(f"\nAccount Balance: ${account['cash']:,.2f}")
    
    # Get current positions
    positions = broker.get_positions()
    print(f"Current Positions: {len(positions)}")

    # Check positions for sell signals
    if positions:
        for symbol, pos in positions.items():
            print(f"  {symbol}: {pos.quantity} shares @ ${pos.avg_entry_price:.2f}")
            strategy.update_position_tracking(symbol, 'opened')
            
            # Check if position has gained enough
            if pos.unrealized_pnl_percent >= settings.MEAN_REVERSION_CONFIG['GAIN_THRESHOLD'] * 100:
                print(f"\nSELL SIGNAL: {symbol}")
                print(f"Reason: Position up {pos.unrealized_pnl_percent:.1f}%")
                
                # Create sell order - FIXED: using pos.quantity
                sell_order = Order(
                    symbol=symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=pos.quantity,  # FIXED: was position.quantity
                    order_id=f"ORD_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{symbol}",
                    status=OrderStatus.PENDING
                )
                
                order_id = broker.place_order(sell_order)
                if order_id:
                    print(f"✓ Sell order placed: {order_id}")
                    # Log the trade
                    log_trade('SELL', symbol, pos.quantity, pos.current_price, 
                             f"Position up {pos.unrealized_pnl_percent:.1f}%")
    
    # Get market data
    print("\nFetching market data...")
    historical_data = feed.get_historical_data(days=20)
    
    # Run strategy
    print("Analyzing for signals...")
    signals = strategy.analyze(historical_data, positions)
    
    if not signals:
        print("No trading signals generated")
        return
    
    # Initialize sets for tracking
    open_symbols = set()
    filled_symbols = set()
    
    # FIXED: Proper indentation for try-except blocks
    try:
        # Get all open orders
        from alpaca.trading.enums import QueryOrderStatus
        from alpaca.trading.requests import GetOrdersRequest
        
        open_orders = broker.client.get_orders()  # Get all orders
        open_symbols = {order.symbol for order in open_orders 
                       if order.status in ['new', 'pending_new', 'partially_filled', 'accepted']}
        
        if open_symbols:
            print(f"Open orders for: {', '.join(open_symbols)}")
            
    except Exception as e:
        open_symbols = set()
        logger.error(f"Could not get open orders: {e}")
    
    # FIXED: This try block is now at the correct indentation level
    try:
        # Also get filled orders from today to avoid re-buying
        from alpaca.trading.enums import QueryOrderStatus
        from alpaca.trading.requests import GetOrdersRequest
        
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        filled_request = GetOrdersRequest(
            status=QueryOrderStatus.FILLED,
            after=today_start
        )
        filled_orders = broker.client.get_orders(filter=filled_request)
        filled_symbols = {order.symbol for order in filled_orders}
        
        if filled_symbols:
            print(f"Already bought today: {', '.join(filled_symbols)}")
            
    except Exception as e:
        filled_symbols = set()
        logger.error(f"Could not get filled orders: {e}")

    # Process signals
    print(f"\nFound {len(signals)} signals:")
    
    for signal in signals:
        # Check if we should skip this symbol
        if signal.symbol in positions:
            print(f"Skipping {signal.symbol} - have position")
            continue
            
        if signal.symbol in open_symbols:
            print(f"Skipping {signal.symbol} - open order pending")
            continue
        
        print(f"\n{signal.signal_type.value.upper()}: {signal.symbol}")
        print(f"Reason: {signal.reason}")
        print(f"Confidence: {signal.confidence}")
        
        # Get current price - try latest first, then use last historical
        current_price = None

        # Try to get latest price
        latest_prices = feed.get_latest_prices()
        if signal.symbol in latest_prices:
            current_price = latest_prices[signal.symbol].close
        else:
            # Fall back to last historical price
            if signal.symbol in historical_data and historical_data[signal.symbol]:
                current_price = historical_data[signal.symbol][-1].close
                print(f"Using last historical price: ${current_price:.2f}")

        if not current_price:
            print(f"Could not get any price for {signal.symbol}")
            continue

        print(f"Current Price: ${current_price:.2f}")
        
        # Process signal
        order_request = order_manager.process_signal(signal, current_price)
        
        if order_request:
            # Create order
            order = order_manager.create_order(order_request)
            print(f"Order: {order.side.value} {order.quantity} shares")
            
            # Execute order
            order_id = broker.place_order(order)
            
            if order_id:
                print(f"✓ Order placed successfully! ID: {order_id}")
            else:
                print(f"✗ Failed to place order")


def main():
    """Main bot loop"""
    print("=== Brot Trading Bot Started ===")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Check Interval: {settings.TRADING_CONFIG['CHECK_INTERVAL_SECONDS']}s")
    
    while True:
        try:
            execute_trading_cycle()
            
            # Wait for next cycle
            print(f"\nWaiting {settings.TRADING_CONFIG['CHECK_INTERVAL_SECONDS']}s for next cycle...")
            print("Press Ctrl+C to stop")
            time.sleep(settings.TRADING_CONFIG['CHECK_INTERVAL_SECONDS'])
            
        except KeyboardInterrupt:
            print("\n\nShutting down...")
            break
        except Exception as e:
            logger.error(f"Error in trading cycle: {e}", exc_info=True)
            time.sleep(30)


if __name__ == "__main__":
    main()