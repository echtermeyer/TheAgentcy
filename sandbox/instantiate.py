import logging
import os
from src.utils import write_str_to_file
from sandbox.dockergenerator import execute_python
from sandbox.logger import setup_logger
import docker 

class PythonSandbox:
    """
    A class for creating and managing a Python sandbox environment using Docker.
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

        setup_logger(self.directory_path)


    def trigger_execution_pipeline(self, fulltext_code: str) -> docker.models.containers.Container:
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
        return running_container

    def init_basic_environment(self) -> docker.models.containers.Container:
        """
        Initializes a basic Python Docker environment.

        Returns:
            docker.models.containers.Container: The Docker container object.
        """
        logging.info(f"Init Container created for backend.")
        innit_container = execute_python("from fastapi import FastAPI\nimport uvicorn\napp = FastAPI()\n@app.get('/')\nasync def read_root():\n\treturn 'Setup Successfull!'\nuvicorn.run(app, host='0.0.0.0', port=8000)")
        return innit_container