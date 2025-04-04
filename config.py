# /config.py
# Configuration settings for the application loaded from environment variables
import os
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()

# Fetch interval in minutes
FETCH_INTERVAL = int(os.getenv("FETCH_INTERVAL", "5"))

# Stock symbols to track (default: MSTR and MSTU)
SYMBOLS_ENV = os.getenv("SYMBOLS", "MSTR,MSTU")
SYMBOLS = [sym.strip() for sym in SYMBOLS_ENV.split(",")]

# Log level
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# No file persistence - data remains in memory only

# Port for the web server (Render sets this automatically)
PORT = int(os.getenv("PORT", "8000"))

# Maximum age (in seconds) for which we consider data valid
MAX_DATA_AGE_SECONDS = int(os.getenv("MAX_DATA_AGE_SECONDS", str(60 * 60 * 24)))  # Default 24 hours
