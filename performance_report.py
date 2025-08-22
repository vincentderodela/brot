import json

def generate_report():
    with open('logs/trades.json', 'r') as f:
        trades = [json.loads(line) for line in f]
    
    # Calculate metrics
    buys = [t for t in trades if t['action'] == 'BUY']
    sells = [t for t in trades if t['action'] == 'SELL']
    
    print(f"Total Buys: {len(buys)}")
    print(f"Total Sells: {len(sells)}")
    # Add more metrics...