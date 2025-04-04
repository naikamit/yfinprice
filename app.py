# app.py
from flask import Flask, jsonify
import yfinance as yf
import os
import logging
from apscheduler.schedulers.background import BackgroundScheduler
import time
import socket
import tempfile
import atexit

# Configure logging
log_level = os.environ.get('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get configuration from environment variables
fetch_interval = int(os.environ.get('FETCH_INTERVAL', '5'))
symbols = os.environ.get('SYMBOLS', 'MSTR,MSTU').split(',')

# Initialize Flask app
app = Flask(__name__)

# Store the latest stock data
stock_data = {}

def fetch_stock_prices():
    """Fetch stock prices and store them in the stock_data dictionary"""
    try:
        logger.info(f"Fetching stock prices for: {symbols}")
        for symbol in symbols:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d")
            if not data.empty:
                latest_price = data['Close'].iloc[-1]
                stock_data[symbol] = {
                    'price': latest_price,
                    'timestamp': time.time()
                }
                logger.info(f"Updated {symbol}: ${latest_price:.2f}")
            else:
                logger.warning(f"No data returned for {symbol}")
    except Exception as e:
        logger.error(f"Error fetching stock prices: {e}")

# Use a lock file to ensure only one scheduler runs
LOCK_FILE = os.path.join(tempfile.gettempdir(), 'stock_scheduler.lock')

def is_scheduler_running():
    """Check if scheduler is already running using a lock file"""
    try:
        # Try to create a server socket on a specific file
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.bind(LOCK_FILE)
        # If we got here, no other process has the lock
        return False
    except (socket.error, OSError):
        # Socket already in use or file exists
        return True

# Initialize the scheduler only on one worker
scheduler = None
if not is_scheduler_running():
    logger.info("Starting background scheduler")
    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_stock_prices, 'interval', minutes=fetch_interval)
    scheduler.start()
    
    # Register cleanup function
    def cleanup_scheduler():
        if scheduler:
            scheduler.shutdown()
        try:
            os.unlink(LOCK_FILE)
        except (OSError, FileNotFoundError):
            pass
    
    atexit.register(cleanup_scheduler)
    
    # Fetch initial data
    fetch_stock_prices()
else:
    logger.info("Scheduler already running in another process")

@app.route('/')
def home():
    return jsonify({
        'service': 'Stock Price Service',
        'status': 'running',
        'symbols': symbols
    })

@app.route('/prices')
def prices():
    return jsonify(stock_data)

@app.route('/price/<symbol>')
def price(symbol):
    symbol = symbol.upper()
    if symbol in stock_data:
        return jsonify(stock_data[symbol])
    else:
        return jsonify({'error': f'Symbol {symbol} not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
