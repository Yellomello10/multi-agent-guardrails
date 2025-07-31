# utils/logger.py
import logging
import sys
import os

def setup_logger():
    """
    Sets up a centralized logger for the application.
    """
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Configure logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler("logs/guardrails.log"),
            logging.StreamHandler(sys.stdout) # Also print logs to the console
        ]
    )
    logger = logging.getLogger("MultiAgentGuardrail")
    return logger

# Create a single instance of the logger to be imported by other modules
logger = setup_logger()