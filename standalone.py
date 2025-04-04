# /standalone.py
# All-in-one application file for Render deployment
import os
import time
import logging
import signal
import sys
from datetime import datetime
from flask import Flask, jsonify, request
import yfinance as yf
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("stock_price_service")

# Load configuration from environment
FETCH_INTERVAL = int(os.environ.get("FETCH_INTERVAL", "5"))
SYMBOLS_ENV = os.environ.get("SYMBOLS", "MSTR,MSTU")
SYMBOLS = [sym.strip() for sym in SYMBOLS_ENV.split(",")]
PORT = int(os.environ.get("PORT", "8000"))
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# Set log level from environment
logger.setLevel(getattr(logging, LOG_LEVEL))

# In-memory storage
price_data = {}

# Flask app
app = Flask(__name__)

# Background scheduler
scheduler = BackgroundScheduler()

# Helper functions
def format_staleness(minutes):
    """Format staleness time in a human-readable way."""
    if minutes is None:
        return "Unknown"
    elif minutes < 60:
        return f"{minutes:.1f} minutes"
    elif minutes < 1440:  # Less than a day
        return f"{minutes / 60:.1f} hours"
    else:
        return f"{minutes / 1440:.1f} days"

def get_price_staleness(symbol):
    """Get the staleness of price data in minutes."""
    data = price_data.get(symbol)
    if not data:
        return None
    
    current_time = time.time()
    staleness_seconds = current_time - data["timestamp"]
    return staleness_seconds / 60  # Convert to minutes

def update_price(symbol, price):
    """Update the price for a symbol with the current timestamp."""
    timestamp = time.time()
    logger.info(f"Updating price for {symbol}: {price} at {timestamp}")
    
    price_data[symbol] = {
        "price": price,
        "timestamp": timestamp
    }

def fetch_prices():
    """Fetch prices for all configured symbols."""
    logger.info(f"Fetching prices for symbols: {SYMBOLS}")
    
    for symbol in SYMBOLS:
        try:
            fetch_start_time = time.time()
            logger.debug(f"Fetching price for {symbol}")
            ticker = yf.Ticker(symbol)
            
            # Get the latest data
            hist = ticker.history(period="1d")
            
            if hist.empty:
                logger.warning(f"No data received for {symbol}")
                continue
            
            # Get the closing price or current price
            if "Close" in hist.columns:
                price = float(hist["Close"].iloc[-1])
                logger.info(f"Fetched price for {symbol}: ${price:.2f}")
                
                # Update storage
                update_price(symbol, price)
            else:
                logger.warning(f"No 'Close' column in data for {symbol}")
                
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

def init_scheduler():
    """Initialize and start the scheduler."""
    logger.info(f"Initializing scheduler with interval: {FETCH_INTERVAL} minutes")
    
    # Add job to fetch prices at regular intervals
    scheduler.add_job(
        fetch_prices,
        IntervalTrigger(minutes=FETCH_INTERVAL),
        id="fetch_prices_job",
        replace_existing=True,
        max_instances=1
    )
    
    # Run once immediately to fetch initial data
    scheduler.add_job(
        fetch_prices, 
        id="fetch_prices_initial", 
        replace_existing=True
    )
    
    # Start the scheduler
    try:
        scheduler.start()
        logger.info("Scheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        raise

# API call tracking
api_calls = {
    "total": 0,
    "last_call_time": None,
    "last_ip": None
}

# Fixed HTML template without f-strings or JavaScript
HTML_TOP = """<!DOCTYPE html>
<html>
<head>
    <title>Stock Price Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; margin: 0; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        .header { display: flex; justify-content: space-between; margin-bottom: 20px; }
        .price-card { border: 1px solid #ddd; padding: 15px; margin-bottom: 15px; }
        .symbol { font-size: 24px; font-weight: bold; }
        .price { font-size: 36px; margin: 10px 0; }
        .refresh-button { padding: 8px 16px; background: #4a90e2; color: white; border: none; cursor: pointer; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Stock Price Dashboard</h1>
            <div>Last updated: <span id="current-time">"""

HTML_MIDDLE = """</span></div>
        </div>
"""

HTML_BOTTOM = """        <button class="refresh-button" onclick="location.reload()">Refresh Dashboard</button>
    </div>
    
    <script>
        setTimeout(function() { 
            location.reload(); 
        }, 60000);
    </script>
</body>
</html>"""

# Flask routes
@app.route("/")
def dashboard():
    """Render the dashboard showing latest prices and staleness."""
    try:
        logger.info("Dashboard requested")
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Build HTML in pieces to avoid f-string issues
        html = HTML_TOP + current_time + HTML_MIDDLE
        
        # Add price cards
        for symbol in SYMBOLS:
            data = price_data.get(symbol, {})
            price = data.get("price")
            timestamp = data.get("timestamp")
            
            staleness_minutes = get_price_staleness(symbol)
            staleness_text = format_staleness(staleness_minutes) if staleness_minutes else "Unknown"
            
            timestamp_text = "Never fetched"
            if timestamp:
                timestamp_text = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
            
            price_text = "No data"
            if price is not None:
                price_text = f"${price}"
            
            html += f"""
                <div class="price-card">
                    <div class="symbol">{symbol}</div>
                    <div class="price">{price_text}</div>
                    <div>Data is {staleness_text} old</div>
                    <div>Last fetched: {timestamp_text}</div>
                </div>
            """
        
        # Add API stats
        api_last_call = "Never"
        if api_calls["last_call_time"]:
            api_last_call = datetime.fromtimestamp(api_calls["last_call_time"]).strftime("%Y-%m-%d %H:%M:%S")
            
        html += f"""
            <div class="price-card">
                <h3>API Statistics</h3>
                <div>Total API Calls: {api_calls["total"]}</div>
                <div>Last API Call: {api_last_call}</div>
                <div style="margin-top: 10px; font-family: monospace; background: #eee; padding: 10px;">
                    API Endpoint: <code>/check</code>
                </div>
            </div>
        """
        
        # Add bottom part with JavaScript (no f-strings)
        html += HTML_BOTTOM
        
        return html
    
    except Exception as e:
        error_msg = f"Error rendering dashboard: {str(e)}"
        logger.error(error_msg)
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return f"<h1>Error</h1><p>{error_msg}</p>", 500

@app.route("/check")
def check():
    """Return JSON with latest prices."""
    try:
        # Track API usage
        api_calls["total"] += 1
        api_calls["last_call_time"] = time.time()
        api_calls["last_ip"] = request.remote_addr
        
        logger.info(f"/check endpoint requested (call #{api_calls['total']} from {api_calls['last_ip']})")
        
        response_data = {}
        
        for symbol in SYMBOLS:
            data = price_data.get(symbol, {})
            if data:
                response_data[symbol] = {
                    "price": data.get("price"),
                    "timestamp": data.get("timestamp")
                }
            else:
                response_data[symbol] = {
                    "price": None,
                    "timestamp": None,
                    "error": "No data available"
                }
        
        return jsonify(response_data)
    
    except Exception as e:
        error_msg = f"Error in /check endpoint: {str(e)}"
        logger.error(error_msg)
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": error_msg}), 500

@app.route("/health")
def health():
    """Health check endpoint for monitoring."""
    logger.debug("Health check requested")
    return jsonify({"status": "ok", "timestamp": time.time()})

# Main entry point
if __name__ == "__main__":
    try:
        # Initialize scheduler
        init_scheduler()
        
        # Handle shutdown signals
        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}, shutting down...")
            scheduler.shutdown()
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start web server
        logger.info(f"Starting web server on port {PORT}")
        app.run(host="0.0.0.0", port=PORT, debug=False)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
