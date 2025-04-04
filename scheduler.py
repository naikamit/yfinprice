# /scheduler.py
# Background scheduler for periodic price fetching
import time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from price_fetcher import fetch_prices
from logger import logger
from config import FETCH_INTERVAL

# Global scheduler instance
scheduler = BackgroundScheduler()

def init_scheduler():
    """Initialize and start the scheduler."""
    logger.info(f"Initializing scheduler with interval: {FETCH_INTERVAL} minutes")
    
    # Add job to fetch prices at regular intervals
    scheduler.add_job(
        fetch_prices,
        IntervalTrigger(minutes=FETCH_INTERVAL),
        id="fetch_prices_job",
        replace_existing=True,
        max_instances=1  # Prevent overlapping runs if previous fetch takes too long
    )
    
    # Add listener for job execution events
    scheduler.add_listener(
        job_execution_listener,
        mask=(1 << 0)  # EVENT_JOB_EXECUTED
    )
    
    # Run once immediately to fetch initial data
    fetch_job_id = "fetch_prices_initial"
    logger.info(f"Running initial price fetch (job_id: {fetch_job_id})")
    scheduler.add_job(
        fetch_prices, 
        id=fetch_job_id, 
        replace_existing=True
    )
    
    # Start the scheduler
    try:
        scheduler.start()
        logger.info("Scheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        raise

def job_execution_listener(event):
    """Listener for job execution events to log job completion."""
    logger.info(f"Job {event.job_id} executed successfully")

def shutdown_scheduler():
    """Shutdown the scheduler gracefully."""
    logger.info("Shutting down scheduler")
    scheduler.shutdown()
