# /web_server.py
# Flask web server for rendering dashboard and API endpoints
from flask import Flask, jsonify, render_template, request
from storage import get_all_prices, get_price_staleness, format_staleness
from logger import logger
from datetime import datetime
import time
import traceback
from config import SYMBOLS

# Create Flask app and point to current directory for templates
app = Flask(__name__, template_folder=".")

# Track API calls for dashboard display
api_calls = {
    "total": 0,
    "last_call_time": None,
    "last_ip": None
}

@app.route("/")
def dashboard():
    """Render the dashboard showing latest prices and staleness."""
    try:
        logger.info("Dashboard requested")
        
        # Track request metadata
        request_ip = request.remote_addr
        logger.debug(f"Dashboard request from IP: {request_ip}")
        
        prices = get_all_prices()
        formatted_data = {}
        
        for symbol in SYMBOLS:
            data = prices.get(symbol, {"price": None, "timestamp": None})
            price = data.get("price")
            timestamp = data.get("timestamp")
            
            # Calculate and format staleness
            staleness_minutes = get_price_staleness(symbol)
            staleness_display = format_staleness(staleness_minutes)
            
            # Format timestamp for display if it exists
            if timestamp:
                timestamp_display = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
            else:
                timestamp_display = "Never fetched"
            
            formatted_data[symbol] = {
                "price": price,
                "timestamp": timestamp_display,
                "staleness": staleness_display
            }
        
        # Include API call stats
        api_stats = {
            "total_calls": api_calls["total"],
            "last_call": "Never" if not api_calls["last_call_time"] else 
                        datetime.fromtimestamp(api_calls["last_call_time"]).strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return render_template("index.html", data=formatted_data, api_stats=api_stats)
    
    except Exception as e:
        error_msg = f"Error rendering dashboard: {str(e)}"
        logger.error(error_msg)
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
        
        prices = get_all_prices()
        response_data = {}
        
        for symbol in SYMBOLS:
            data = prices.get(symbol, {})
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
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": error_msg}), 500

@app.route("/health")
def health():
    """Health check endpoint for monitoring."""
    logger.debug("Health check requested")
    return jsonify({"status": "ok", "timestamp": time.time()})

# Error handler for 404
@app.errorhandler(404)
def page_not_found(e):
    logger.warning(f"404 error: {request.path}")
    return jsonify({"error": "Endpoint not found"}), 404

# Error handler for 500
@app.errorhandler(500)
def server_error(e):
    logger.error(f"500 error: {str(e)}")
    return jsonify({"error": "Internal server error"}), 500
