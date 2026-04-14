import logging
import sys

def setup_logger(level=logging.INFO):
    """
    Set up the logging configuration for the application to output to standard out.
    """
    logging.basicConfig(
        stream=sys.stdout,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=level,
    )

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    """
    return logging.getLogger(name)