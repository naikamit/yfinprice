# /price_fetcher.py
# Fetches stock price data using the yfinance library
import yfinance as yf
import time
import traceback
from logger import logger
from storage import update_price
from config import SYMBOLS

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
                
                # Log the fetch duration for performance monitoring
                fetch_duration = time.time() - fetch_start_time
                logger.debug(f"Fetch for {symbol} took {fetch_duration:.2f} seconds")
                
                # Update storage
                update_price(symbol, price)
            else:
                logger.warning(f"No 'Close' column in data for {symbol}")
                
        except Exception as e:
            # Detailed error logging with traceback for debugging
            logger.error(f"Error fetching price for {symbol}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
