# /logger.py
# Configures detailed logging for the application
import logging
import os
import sys
from config import LOG_LEVEL

def setup_logger():
    """Configure and return a logger instance with detailed formatting."""
    # Create logger
    logger = logging.getLogger("stock_price_service")
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # Create console handler and set level
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, LOG_LEVEL))
    
    # Create formatter with file and line number for detailed debugging
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    )
    
    # Add formatter to handler
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    # Try to create a file handler if possible
    try:
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(f"{log_dir}/stock_price_service.log")
        file_handler.setLevel(getattr(logging, LOG_LEVEL))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Failed to set up file logging: {e}")
    
    return logger

# Global logger instance for use throughout the application
logger = setup_logger()
