from io import BytesIO
import logging
import os
import time
from typing import Set, List
from src.utils import write_str_to_file
from src.sandbox.dockergenerator import execute_code
import docker 

from abc import ABC, abstractmethod
import os

class Sandbox(ABC):
    """
    A class for creating sandbox environments using Docker.
    """

    def __init__(self, subfolder_path: str = "") -> None:
        """
        Initializes the Sandbox environment.

        Args:
            subfolder_path (str): The subfolder path for the sandbox environment.
        """
        # Get the current file directory (src)
        current_file_dir = os.path.dirname(__file__)

        sandbox_dir = os.path.join(current_file_dir, 'sandbox')

        # Append any subfolder path to the sandbox directory path
        self.directory_path = os.path.join(sandbox_dir, subfolder_path)
        if not os.path.exists(self.directory_path):
            os.makedirs(self.directory_path)

    @abstractmethod
    def trigger_execution_pipeline(self):
        """
        Abstract method to setup the sandbox environment.
        Subclasses should provide their own implementation.
        """
        pass

    @abstractmethod
    def create_dockerfile_bytes(self, script_name: str, dependencies: Set[str], port: str):
        """
        Abstract method to create a Dockerfile as a BytesIO object.
        Subclasses should provide their own implementation.
        """
        pass
    
    @property
    def path(self):
        return self.directory_path


class PythonSandbox(Sandbox):
    """
    A class for creating and managing a Python sandbox environment using Docker.
    """
    def __init__(self, subfolder_path: str = "backend", container_name: str = "backend", image_tag: str = "python_webserver:latest") -> None:
        self.image_name = image_tag
        self.container_name = container_name
        super().__init__(subfolder_path)
    
    def create_dockerfile_bytes(self, script_name: str, dependencies: Set[str], port: str) -> BytesIO:
        """
        Creates a Dockerfile as a BytesIO object.

        Args:
            script_name (str): The name of the Python script.
            dependencies (Set[str]): A set of Python module dependencies.
            port (str): The port number to expose.

        Returns:
            BytesIO: The Dockerfile as a BytesIO object.
        """

        dockerfile_str = (
            "FROM python:3.9-slim\n"
            "WORKDIR /app\n"
            f"COPY . /app\n"
            f"EXPOSE {port}\n"
            f"RUN pip install --no-cache-dir wheel\n"
            f"RUN pip install --no-cache-dir {' '.join(dependencies)}\n"
            f'CMD ["python", "{script_name}"]\n'
        )
        return BytesIO(dockerfile_str.encode('utf-8'))

    def trigger_execution_pipeline(self, fulltext_python_code: str, dependencies: List[str] = None, port: str = None) -> docker.models.containers.Container:
        """
        Triggers the execution pipeline for the given Python code.

        Args:
            fulltext_code (str): The Python code to be executed.

        Returns:
            docker.models.containers.Container: The Docker container object.
        """
        logging.info(f"New Python Pipeline request for code: {fulltext_python_code}")
        
        file_path = write_str_to_file(fulltext_python_code, os.path.join(self.directory_path, 'index.py'))
        running_container = execute_code(file_path, self.image_name, self.container_name, self.create_dockerfile_bytes, dependencies, port)
        # Wait until the container is either running or has exited
        while True:
            running_container.reload()  # Refresh the container data
            container_status = running_container.attrs['State']['Status']
            if container_status != 'created':
                break
            time.sleep(1)  # Wait for a second before checking again

        return running_container    


class FrontendSandbox(Sandbox):
    """
    A class for creating and managing a Nginx sandbox environment using Docker.
    """
    def __init__(self, subfolder_path: str = "frontend", container_name: str = "frontend", image_tag: str = "nginx_webserver:latest") -> None:
        self.image_name = image_tag
        self.container_name = container_name
        super().__init__(subfolder_path)

    def create_dockerfile_bytes(self, script_name: str, dependencies: Set[str], port: str) -> BytesIO:
        """
        Creates a Dockerfile for an Nginx server as a BytesIO object.

        Args:
            script_name (str): Not used yet.
            dependencies (Set[str]): Not used yet.
            port (str): The port number to expose.

        Returns:
            BytesIO: The Dockerfile as a BytesIO object.
        """
        dockerfile_str = (
            "FROM nginx:alpine\n"
            f"COPY . .\n"
            f"EXPOSE {port}\n"
            f'CMD ["nginx", "-g", "daemon off;"]\n'
        )

        return BytesIO(dockerfile_str.encode('utf-8'))

    def trigger_execution_pipeline(self, fulltext_html_code: str) -> docker.models.containers.Container:
        """
        Triggers the execution pipeline for the given HTML code.

        Args:
            fulltext_html_code (str): The HTML code to be executed.

        Returns:
            docker.models.containers.Container: The Docker container object.
        """
        logging.info(f"New Frontend Pipeline request for code: {fulltext_html_code}")
        file_path = write_str_to_file(fulltext_html_code, os.path.join(self.directory_path, 'index.html'))
        running_container = execute_code(file_path, self.image_name, self.container_name, self.create_dockerfile_bytes, dependencies=[], port="80")

        # Wait until the container is either running or has exited
        while True:
            running_container.reload()  # Refresh the container data
            container_status = running_container.attrs['State']['Status']
            if container_status != 'created':
                break
            time.sleep(1)  # Wait for a second before checking again

        return running_container
