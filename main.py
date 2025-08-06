#! /usr/bin/env python3
"""
Brot trading robot - Main entry point
"""
#Imports Section
import time # module for delays
import logging # module for logs
from datetime import datetime # module for date and time
import sys # module for system-spec<ic parameters and functions

# Configure logging
logging.basicConfig(
    level=logging.INFO, # Show informational messages and above
    format='%(asctime)s - %'(name)s - %(levelname)s - %(message)s', #timestamp, name, level, message
    handlers=[
        logging.FileHandler('brot.log'), # Log to a file
        logging.StreamHandler(sys.stdout) # Print to screen
    ]
)

#Create a logger object for this module
logger = logging.getLogger(__name__)
def check_trading_hours():
    """
    Check if market is open
    """
    current_hour = datetime.now().hour # Get current hour
    # Simplified check, let's timezone it later
    if 9 <= current_hour < 16:
        return True
    return False

def initialize_bot():
    """
    Initialize the trading bot
    """
    logger.info("Initializing Brot Trading Bot...")

    # TODO : Initialize components
    # Load configuration
    # Connect to the broker
    # Set up data feeds
    # Load strategies

    logger.info("Initialization complete.")
    
def main_trading_loop():
    """
    Main trading loop
    """
    logger.info("Starting main trading loop...")

    cycle_count = 0 # Keep track of cycles

    # Main loop
    while True:
        try:
            cycle_count += 1
            logger.info(f"Trading cycle{ cycle_count} starting...")

            #Check if market is open
            if not check_trading_hours():
                logger.info("Market is closed. Waiting...")
                time.sleep(300)  # Wait for 5 minutes
                continue

            # TODO: Implement trading logic
            # - Fetch market data
            # - Checkl positions
            # - Run strategies
            # - Execute trades

            logger.info("Trading cycle complete.")

            #Wait before next cycle
            time.sleep(60)  # Wait for 1 minute before next cycle

        except Keyboard interrupt
            # When ctrl+C is pressed, exit gracefully
            logger.info("Shutdown received. Exiting...")
            break # Exit the loop

        except Exception as e:
            # Catch other errors
            logger.error(f"Error in trading loop: {e}")
            time.sleep(30)  # Wait before retrying

def shutdown_bot():
    """
    Clean shutdown - close connections, save state, etc.
    """
    logger.info("Shutting down Brot Trading Robot...")
    # TODO: Cleanup tasks
    # - Close broker copnnections
    # - Save current state
    # - Close database connections
    logger.info("Shutdown complete.")

def __name__ == "__main__":
    """
    Check if the script is being run directly 
    (not imported as a module)
    """

    print("=== Brot the Brobot ===")
    print(f"Starting at {datetime.now()}")
    # Initialize the bot
    if initialize_bot():
        try:
            # Run the main trading loop
            main_trading_loop()
        finally:
            # This always runs, even on error
            shutdown_bot()
    else : 
        logger.error("Brot the brobot is not feeling it today")
        sys.exit(1) #Exit with error code 1w
