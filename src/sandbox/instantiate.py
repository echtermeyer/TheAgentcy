import time
import docker
import logging

from io import BytesIO
from pathlib import Path
from typing import Set, List
from abc import ABC, abstractmethod

from src.utils import write_str_to_file
from src.sandbox.dockergenerator import execute_code


class Sandbox(ABC):
    """
    A class for creating sandbox environments using Docker.
    """

    def __init__(self, project_title: str, subfolder_path: str = "") -> None:
        """
        Initializes the Sandbox environment.

        Args:
            subfolder_path (str): The subfolder path for the sandbox environment.
        """
        # Get the project path
        current_file_dir = Path(__file__).parent.parent.parent
        projects_dir = current_file_dir / "projects"

        # Append any subfolder path to the sandbox directory path
        self.directory_path = projects_dir / f"{project_title}/{subfolder_path}"
        self.directory_path.mkdir(exist_ok=True, parents=True)

    @abstractmethod
    def trigger_execution_pipeline(self):
        """
        Abstract method to setup the sandbox environment.
        Subclasses should provide their own implementation.
        """
        pass

    @abstractmethod
    def create_dockerfile_bytes(
        self, script_name: str, dependencies: Set[str], port: str
    ):
        """
        Abstract method to create a Dockerfile as a BytesIO object.
        Subclasses should provide their own implementation.
        """
        pass

    @property
    def path(self):
        return self.directory_path

    @property
    @abstractmethod
    def url(self):
        pass


class PythonSandbox(Sandbox):
    """
    A class for creating and managing a Python sandbox environment using Docker.
    """

    def __init__(
        self,
        project_title: str,
        subfolder_path: str = "backend",
        container_name: str = "backend",
        image_tag: str = "python_webserver:latest",
    ) -> None:
        self.image_name = image_tag
        self.container_name = container_name
        super().__init__(project_title, subfolder_path)

    @property
    def url(self) -> str:
        return f"http://localhost:{self.port}"

    def create_dockerfile_bytes(
        self, script_name: str, dependencies: Set[str], port: str
    ) -> BytesIO:
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
        return BytesIO(dockerfile_str.encode("utf-8"))

    def trigger_execution_pipeline(
        self,
        fulltext_python_code: str,
        dependencies: List[str] = None,
        port: str = "8000",
    ) -> docker.models.containers.Container:
        """
        Triggers the execution pipeline for the given Python code.

        Args:
            fulltext_code (str): The Python code to be executed.

        Returns:
            docker.models.containers.Container: The Docker container object.
        """
        logging.info(f"New Python Pipeline request for code: {fulltext_python_code}")

        self.port = port

        file_path = write_str_to_file(
            fulltext_python_code, self.directory_path / "index.py"
        )
        running_container = execute_code(
            file_path,
            self.image_name,
            self.container_name,
            self.create_dockerfile_bytes,
            dependencies,
            port,
        )
        # Wait until the container is either running or has exited
        try:
            while True:
                running_container.reload()  # Refresh the container data
                container_status = running_container.attrs["State"]["Status"]
                if container_status != "created":
                    break
                time.sleep(1)  # Wait for a second before checking again
        except Exception as e:
            print(e)

        return running_container


class FrontendSandbox(Sandbox):
    """""
    A class for creating and managing a Nginx sandbox environment using Docker.
    """ ""

    def __init__(
        self,
        project_title: str,
        subfolder_path: str = "frontend",
        container_name: str = "frontend",
        image_tag: str = "nginx_webserver:latest",
    ) -> None:
        self.image_name = image_tag
        self.container_name = container_name
        super().__init__(project_title, subfolder_path)

    @property
    def url(self) -> str:
        return f"http://localhost:{self.port}"

    def create_dockerfile_bytes(
        self, script_name: str, dependencies: Set[str], port: str
    ) -> BytesIO:
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

        return BytesIO(dockerfile_str.encode("utf-8"))

    def trigger_execution_pipeline(
        self, fulltext_html_code: str, dependencies=None
    ) -> docker.models.containers.Container:
        """
        Triggers the execution pipeline for the given HTML code.

        Args:
            fulltext_html_code (str): The HTML code to be executed.

        Returns:
            docker.models.containers.Container: The Docker container object.
        """
        logging.info(f"New Frontend Pipeline request for code: {fulltext_html_code}")

        self.port = "80"

        file_path = write_str_to_file(
            fulltext_html_code, self.directory_path / "index.html"
        )
        running_container = execute_code(
            file_path,
            self.image_name,
            self.container_name,
            self.create_dockerfile_bytes,
            dependencies=[],
            port=self.port,
        )

        # Wait until the container is either running or has exited
        while True:
            running_container.reload()  # Refresh the container data
            container_status = running_container.attrs["State"]["Status"]
            if container_status != "created":
                break
            time.sleep(1)  # Wait for a second before checking again

        return running_container


class DatabaseSandbox(Sandbox):
    """
    A class for creating and managing a Postgres sandbox environment using Docker.

    Args:
        subfolder_path (str): The subfolder path for the sandbox environment.
        container_name (str): The name of the Docker container.
        image_tag (str): The name of the Docker image.
        port (str): The port number to expose.
        db_user (str): The database user.
        db_pwd (str): The database password.

    Returns:
        str: The database connection string.
    """

    def __init__(
        self,
        project_title: str,
        subfolder_path: str = "database",
        container_name: str = "database",
        image_tag: str = "postgres_webserver:latest",
        port: str = "5432",
        db_user: str = "user",
        db_pwd: str = "admin",
    ) -> None:
        self.image_name = image_tag
        self.container_name = container_name
        self.port = port
        self.db_user = db_user
        self.db_pwd = db_pwd
        super().__init__(project_title, subfolder_path)

        self.trigger_execution_pipeline()

    @property
    def url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_pwd}@localhost:{self.port}"

    def create_dockerfile_bytes(
        self, script_name: str, dependencies: Set[str], port: str
    ) -> BytesIO:
        """
        Creates a Dockerfile for an Postgres server as a BytesIO object.

        Args:
            script_name (str): Not used yet.
            dependencies (Set[str]): Not used yet.
            port (str): The port number to expose.

        Returns:
            BytesIO: The Dockerfile as a BytesIO object.
        """
        dockerfile_str = (
            "FROM postgres:latest\n"
            f"ENV POSTGRES_USER={dependencies[0]}\n"
            f"ENV POSTGRES_PASSWORD={dependencies[1]}\n"
            f"EXPOSE {port}\n"
            'CMD ["postgres"]\n'
        )

        return BytesIO(dockerfile_str.encode("utf-8"))

    def trigger_execution_pipeline(
        self, fulltext_sql_code=None, dependencies=None
    ) -> docker.models.containers.Container:
        """
        Triggers the execution pipeline for the given SQL code.

        Args:

        Returns:
            docker.models.containers.Container: The Docker container DB.
        """
        logging.info(f"New Database Creation")
        try:
            file_path = write_str_to_file(
                "This is only the instantiation file, there is no code parsed yet.",
                self.directory_path / "INFO.md",
            )
            running_container = execute_code(
                file_path,
                self.image_name,
                self.container_name,
                self.create_dockerfile_bytes,
                dependencies=[self.db_user, self.db_pwd],
                port=self.port,
            )
        except Exception as e:
            return f"error when creating database, Error: {str(e)} or also {running_container}"
        # Wait until the container is either running or has exited
        while True:
            try:
                running_container.reload()  # Refresh the container data
                container_status = running_container.attrs["State"]["Status"]
                if container_status != "created":
                    break
                time.sleep(1)  # Wait for a second before checking again
            except Exception as e:
                return f"error when checking container, Error: {str(e)} or also {running_container}"

        return running_container
