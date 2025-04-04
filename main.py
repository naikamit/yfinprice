# /main.py
# Simple entry point that just imports and runs the web server
import logging
import sys

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("stock_price_service")

logger.info("==== Starting Stock Price Service ====")

# Import the app - this will initialize the scheduler
from web_server import app

if __name__ == "__main__":
    # The app.run() is already defined in web_server.py
    # when it's run as __main__
    import web_server
