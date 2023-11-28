import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(subfolder_path: str, max_file_size: int = 1048576, backup_count: int = 5) -> None:
    """
    Sets up a logger to write logs to a file in the specified subfolder. 
    Uses a RotatingFileHandler to limit the log file size.

    Args:
        subfolder_path (str): Path to the subfolder where the log file will be stored.
        max_file_size (int): Maximum log file size in bytes. Default is 1 MB.
        backup_count (int): Number of backup files to keep. Default is 5.
    """
    log_file_path = os.path.join(subfolder_path, 'python_sandbox.log')

    # Create a rotating file handler
    handler = RotatingFileHandler(log_file_path, maxBytes=max_file_size, backupCount=backup_count)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    logging.info("Logger initialized.")