import requests
import time
import os
import logging
from dotenv import load_dotenv

# --- Logging Setup ---
# This will create a log file in the same directory as the script.
# It is essential for debugging the service's behavior.
log_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(log_dir, "crawler_app.log")

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

load_dotenv()

MIDDLEWARE_URL = os.getenv("MIDDLEWARE_API_URL")

def trigger_processing():
    """Calls the middleware API to start a processing batch."""
    if not MIDDLEWARE_URL:
        logging.error("FATAL: MIDDLEWARE_API_URL is not set in the .env file. Cannot proceed.")
        # Sleep for a minute to avoid spamming the log file with the same error.
        time.sleep(60)
        return

    logging.info(f"Attempting to call middleware at {MIDDLEWARE_URL}...")
    try:
        response = requests.post(MIDDLEWARE_URL, timeout=30) # Added a 30-second timeout
        response.raise_for_status() # This will raise an exception for 4xx or 5xx status codes
        logging.info(f"Middleware call successful. Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        # This will catch any network error, timeout, or bad status code.
        logging.error(f"CRITICAL: An error occurred while calling the middleware API.", exc_info=True)

def main_crawler_loop():
    """Main loop that triggers processing every 10 minutes."""
    logging.info("Crawler main loop started.")
    while True:
        trigger_processing()
        logging.info("Cycle complete. Waiting for 10 minutes...")
        time.sleep(600)

if __name__ == '__main__':
    main_crawler_loop()