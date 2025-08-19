"""
Configuration settings for brot
This file manages all settings in one place
"""

import os
from pathlib import Path
from typing import List, Dict
import json

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Environment management
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
IS_PRODUCTION = ENVIRONMENT == 'production'

# Logging configuration
LOG_LEVEL = 'DEBUG' if not IS_PRODUCTION else 'INFO'
LOG_FILE = PROJECT_ROOT / 'logs' / 'brot.log'

# Trading configuration
TRADING_CONFIG = {
    'CHECK_INTERVAL_SECONDS': 60,
    'MAX_POSITIONS': 20,
    'POSITION_SIZE_PERCENT': 5,
    'STOP_LOSS_PERCENT': 15
}
# Strategies Parameters
MEAN_REVERSION_CONFIG = {
    'LOOKBACK_DAYS': 7,
    'DROP_THRESHOLD': 0.10,
    'GAIN_THRESHOLD': 0.10,
    'MAX_HOLDING_DAYS': 90,
    'MAX_ADDITIONS': 3
}

# Trading Universe
TRADING_UNIVERSE: List[str] = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META',
    'TSLA', 'NVDA', 'JPM', 'V', 'JNJ',
    'WMT', 'PG', 'DIS', 'HD', 'MA',
    'PYPL', 'BAC', 'NFLX', 'ADBE', 'CRM'
]

# Market hours (simplified, in production use pytz for timezones)
MARKET_HOURS = {
    'OPEN_HOUR': 9,
    'OPEN_MINUTE': 30,
    'CLOSE_HOUR': 16,
    'CLOSE_MINUTE': 0,
    'TIMEZONE': 'America/New_York'
}

# Create necessary directories
def setup_directories():
    # Create required directories if they do not exist
    directories = [
        PROJECT_ROOT / 'logs',  
        PROJECT_ROOT / 'data' / 'cache',
        PROJECT_ROOT / 'data' / 'historical',
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

# Load configuration from a JSON file (optional)
def load_config_from_json(filename: str = 'config.json') -> Dict:
    """
    Load additional configuration from a JSON file.
    
    """
    config_path = PROJECT_ROOT / filename
    
    if config_path.exists():
        with open(config_path, 'r') as f:
            return json.load(f)
    else:
        return {}

# Validate configuration
def validate_config():
    """ Check that all required settings are present """
    required_env_vars = []

    if IS_PRODUCTION:
        required_env_vars.extend([
            'ALPACA_API_KEY',
            'ALPACA_SECRET_KEY',
        ])  
    
    missing = [var for var in required_env_vars if not os.getenv(var)]

    if missing:
        raise ValueError(f"Missing required environment variables: {missing}")

# Run setup when module is imported
setup_directories()