import logging
import os
import sys

def setup_logging(log_file="app.log", level=logging.INFO):
    """
    Sets up the logging configuration.
    """
    # Create logger
    logger = logging.getLogger("ImageProcessor")
    logger.setLevel(level)

    # Check if handlers already exist to avoid duplicates
    if not logger.handlers:
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Console handler (optional, but good for debugging)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    return logger
