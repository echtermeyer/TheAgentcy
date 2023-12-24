import logging


class Logger:
    def __init__(self) -> None:
        self.setup_logger()

    def setup_logger(self) -> None:
        """
        Sets up a logger to write logs to the console.
        """
        # Create a stream handler (console output)
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)

        # Get the root logger and configure it
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)

        logging.info("Logger initialized.")
