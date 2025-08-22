"""
Monitor bot performance
"""
from execution.broker import AlpacaBroker
from tabulate import tabulate

broker = AlpacaBroker()
positions = broker.get_positions()
account = broker.get_account_info()

# Calculate totals
total_value = sum(p.market_value for p in positions.values())
total_pnl = sum(p.unrealized_pnl for p in positions.values())

print("\n=== BROT PORTFOLIO STATUS ===")
print(f"Cash: ${account['cash']:,.2f}")
print(f"Positions Value: ${total_value:,.2f}")
print(f"Total P&L: ${total_pnl:+,.2f}")

# Position details
data = []
for symbol, pos in positions.items():
    data.append([
        symbol,
        pos.quantity,
        f"${pos.avg_entry_price:.2f}",
        f"${pos.current_price:.2f}",
        f"{pos.unrealized_pnl_percent:+.1f}%",
        f"${pos.unrealized_pnl:+,.2f}"
    ])

print("\nPositions:")
print(tabulate(data, headers=['Symbol', 'Qty', 'Avg Cost', 'Current', 'P&L %', 'P&L $']))