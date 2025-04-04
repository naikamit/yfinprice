# /storage.py
# In-memory storage for stock price data
import time
from datetime import datetime
from logger import logger

# Global storage for latest prices and timestamps
# Format: {"symbol": {"price": price, "timestamp": timestamp}}
price_data = {}

def update_price(symbol, price):
    """Update the price for a symbol with the current timestamp."""
    timestamp = time.time()
    logger.info(f"Updating price for {symbol}: {price} at {timestamp}")
    
    price_data[symbol] = {
        "price": price,
        "timestamp": timestamp
    }

def get_price(symbol):
    """Get the latest price data for a symbol."""
    return price_data.get(symbol, None)

def get_all_prices():
    """Get all price data."""
    return price_data

def get_price_staleness(symbol):
    """Get the staleness of price data in minutes."""
    data = get_price(symbol)
    if not data:
        return None
    
    current_time = time.time()
    staleness_seconds = current_time - data["timestamp"]
    return staleness_seconds / 60  # Convert to minutes

def format_staleness(minutes):
    """Format staleness time in a human-readable way (minutes/hours/days)."""
    if minutes is None:
        return "Unknown"
    elif minutes < 60:
        return f"{minutes:.1f} minutes"
    elif minutes < 1440:  # Less than a day
        return f"{minutes / 60:.1f} hours"
    else:
        return f"{minutes / 1440:.1f} days"

# No file persistence methods needed as data is only kept in memory while service is running
