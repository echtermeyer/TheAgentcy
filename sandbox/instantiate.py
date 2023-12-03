import logging
import os
import time
from src.utils import write_str_to_file
from sandbox.dockergenerator import execute_python, execute_frontend
import docker

from abc import ABC, abstractmethod
import os


class Sandbox(ABC):
    """
    A class for creating sandbox environments using Docker.
    """

    def __init__(self, subfolder_path: str = "backend") -> None:
        """
        Initializes the Python sandbox environment.

        Args:
            subfolder_path (str): The subfolder path for the sandbox environment.
        """
        current_file_dir = os.path.dirname(__file__)
        self.directory_path = os.path.join(current_file_dir, subfolder_path)
        if not os.path.exists(self.directory_path):
            os.makedirs(self.directory_path)

        self.setup_sandbox()

    @abstractmethod
    def setup_sandbox(self):
        """
        Abstract method to setup the sandbox environment.
        Subclasses should provide their own implementation.
        """
        pass

    @abstractmethod
    def trigger_execution_pipeline(self):
        """
        Abstract method to setup the sandbox environment.
        Subclasses should provide their own implementation.
        """
        pass

    @property
    def path(self):
        return self.directory_path

    @property
    def type(self):
        return self.directory_path


class PythonSandbox(Sandbox):
    """
    A class for creating and managing a Python sandbox environment using Docker.
    """

    def __init__(self, subfolder_path: str = "backend") -> None:
        super().__init__(subfolder_path)

    def trigger_execution_pipeline(
        self, fulltext_code: str
    ) -> docker.models.containers.Container:
        """
        Triggers the execution pipeline for the given Python code.

        Args:
            fulltext_code (str): The Python code to be executed.

        Returns:
            docker.models.containers.Container: The Docker container object.
        """
        logging.info(f"New Python Pipeline request for code: {fulltext_code}")
        file_path = write_str_to_file(fulltext_code, self.directory_path, ".py")
        running_container = execute_python(file_path)
        time.sleep(1)  # breathing time so logs can be displayed
        return running_container

    def setup_sandbox(self) -> None:
        """
        Initializes a basic Python Docker environment.

        Returns:
            docker.models.containers.Container: The Docker container object.
        """
        logging.info(f"Init Container created for backend.")
        execute_python("from fastapi import FastAPI\nimport uvicorn")


class FrontendSandbox(Sandbox):
    """
    A class for creating and managing a Python sandbox environment using Docker.
    """

    def __init__(self, subfolder_path: str = "frontend") -> None:
        super().__init__(subfolder_path)

    def trigger_execution_pipeline(
        self, fulltext_html_code: str
    ) -> docker.models.containers.Container:
        """
        Triggers the execution pipeline for the given Python code.

        Args:
            fulltext_code (str): The Python code to be executed.

        Returns:
            docker.models.containers.Container: The Docker container object.
        """
        logging.info(f"New Frontend Pipeline request for code: {fulltext_html_code}")
        file_path = write_str_to_file(fulltext_html_code, self.directory_path, ".html")
        running_container = execute_frontend(file_path)
        time.sleep(1)  # breathing time so logs can be displayed
        return running_container

    def setup_sandbox(self) -> None:
        """
        Initializes a basic Python Docker environment.

        Returns:
            docker.models.containers.Container: The Docker container object.
        """
        logging.info(f"Init for frontend. (no container here)")
