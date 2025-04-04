# /main.py
# Entry point for the application that initializes and starts all components
import os
import signal
import sys
import time
from logger import logger
from scheduler import init_scheduler, shutdown_scheduler
from web_server import app
from config import PORT, SYMBOLS, FETCH_INTERVAL

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {sig}, shutting down...")
    shutdown_scheduler()
    sys.exit(0)

def main():
    """Main entry point of the application."""
    start_time = time.time()
    
    logger.info("==== Starting Stock Price Service ====")
    logger.info(f"Monitoring symbols: {SYMBOLS}")
    logger.info(f"Fetch interval: {FETCH_INTERVAL} minutes")
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize and start the scheduler
    logger.info("Initializing scheduler")
    init_scheduler()
    
    # Log startup time
    startup_duration = time.time() - start_time
    logger.info(f"Startup completed in {startup_duration:.2f} seconds")
    
    # Start the web server (this will block)
    logger.info(f"Starting web server on port {PORT}")
    app.run(host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    main()
