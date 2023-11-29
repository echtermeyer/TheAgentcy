import asyncio
import logging
import os
import threading
from logging.handlers import RotatingFileHandler
from sandbox.instantiate import Sandbox

class Logger:

    def __init__(self, sandbox: Sandbox) -> None:
        self.setup_logger(sandbox.path)

        # Start a new event loop in a separate thread
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.start_loop, args=(self.loop,))
        self.thread.start()

        # Schedule the asynchronous logging task
        asyncio.run_coroutine_threadsafe(self.stream_docker_logs(None), self.loop)

    def start_loop(self, loop):
        """
        Starts the asyncio event loop in a separate thread.
        """
        asyncio.set_event_loop(loop)
        loop.run_forever()

    def stop(self):
        """
        Stops the asyncio event loop and joins the thread.
        """
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join()

    def setup_logger(self, subfolder_path: str, max_file_size: int = 1048576, backup_count: int = 5) -> None:
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

    async def stream_docker_logs(self, container):
        """
        Streams logs from a Docker container asynchronously using a thread.

        Args:
            container (docker.models.containers.Container): The Docker container to stream logs from.
        """
        log_queue = asyncio.Queue()

        def log_streamer():
            try:
                for log_line in container.logs(stream=True):
                    asyncio.run_coroutine_threadsafe(log_queue.put(log_line.decode('utf-8', 'ignore').strip()), self.loop)
            except Exception as e:
                asyncio.run_coroutine_threadsafe(log_queue.put(f"Error: {str(e)}"), self.loop)

        threading.Thread(target=log_streamer, daemon=True).start()

        while True:
            log_line = await log_queue.get()
            if log_line.startswith("Error:"):
                logging.error(log_line[6:])
                break
            logging.info(f"Container {container.short_id}: {log_line}")


    def schedule_log_streaming(self, container):
        """
        Schedules the asynchronous logging of Docker container logs.

        Args:
            container (docker.models.containers.Container): The Docker container to stream logs from.
        """
        asyncio.run_coroutine_threadsafe(self.stream_docker_logs(container), self.loop)

    def __del__(self):
        """
        Destructor to ensure that the event loop is stopped and the thread is joined.
        """
        self.stop()