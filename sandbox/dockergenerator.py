from io import BytesIO
import docker
import os
import re
import tempfile
from typing import Any, Set, Tuple
import logging


def extract_dependencies_from_string(script: str) -> Set[str]:
    """
    Extracts Python module dependencies from a script string.

    Args:
        script (str): The Python script as a string.

    Returns:
        Set[str]: A set of Python module dependencies.
    """
    dependencies = set()
    for line in script.splitlines():
        matches = re.findall(r"^import (\w+)|^from (\w+)", line)
        for match in matches:
            dependencies.add(match[0] or match[1])
    return dependencies


def extract_port_from_string(script: str) -> str:
    """
    Extracts the port number from a script string.

    Args:
        script (str): The Python script as a string.

    Returns:
        str: The port number as a string, defaults to '8000' if not found.
    """
    for line in script.splitlines():
        match = re.search(r"port=(\d+)", line)
        if match:
            return match.group(1)
    return "8000"


def create_dockerfile_bytes_python(
    script_name: str, dependencies: Set[str], port: str
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


def create_dockerfile_bytes_frontend(port: str) -> BytesIO:
    """
    Creates a Dockerfile for an Nginx server as a BytesIO object.

    Args:
        html_script_name (str): The name of the HTML script.
        working_directory (str): The working directory where the script is located.
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


def execute_python(input_data: str) -> Any:
    """
    Executes a Python script in a Docker container.

    Args:
        input_data (str): The Python script as a string or a path to the script file.

    Returns:
        Any: The Docker container object or an error message.
    """
    try:
        workspace_folder, script_name, script_string = prepare_script_workspace(
            input_data
        )
        client = docker.from_env()
        IMAGE_TAG = "python_webserver_image:latest"

        dependencies = extract_dependencies_from_string(script_string)
        port = extract_port_from_string(script_string)
        dockerfile_bytes = create_dockerfile_bytes_python(
            script_name, dependencies, port
        )

        logging.info(f"Parsing file: {script_name}.")

        # Remove existing container if exists
        remove_existing_container_and_image(client, IMAGE_TAG)

        # Build and run the Docker image
        container = build_and_run_container(
            client, workspace_folder, dockerfile_bytes, IMAGE_TAG, port
        )

        logging.info(f"Container {container.id[:6]} started successfully.")

        return container

    except Exception as e:
        logging.error(f"Error in execute_python: {str(e)}")
        return f"Error: {str(e)}"


def execute_frontend(input_data):
    """
    Executes a Frontend(HTML) script in a Docker container.

    Args:
        input_data (str): The HTML script as a string or a path to the script file.

    Returns:
        Any: The Docker container object or an error message.
    """
    try:
        workspace_folder, script_name, script_string = prepare_script_workspace(
            input_data
        )
        client = docker.from_env()
        IMAGE_TAG = "nginx_webserver_image:latest"

        port = 80
        dockerfile_bytes = create_dockerfile_bytes_frontend(port)

        logging.info(f"Parsing file: {script_name}.")

        # Remove existing container if exists
        remove_existing_container_and_image(client, IMAGE_TAG)

        # Build and run the Docker image
        container = build_and_run_container(
            client, workspace_folder, dockerfile_bytes, IMAGE_TAG, port
        )

        logging.info(f"Container {container.id[:6]} started successfully.")

        return container

    except Exception as e:
        logging.error(f"Error in execute_frontend: {str(e)}")
        return f"Error: {str(e)}"


def prepare_script_workspace(input_data: str) -> Tuple[str, str, str]:
    """
    Prepares the workspace for the Python script.

    Args:
        input_data (str): The Python script as a string or a path to the script file.

    Returns:
        Tuple[str, str, str]: A tuple containing the workspace folder path, script name, and script string.
    """
    script_name = ""

    if os.path.isfile(input_data):
        workspace_folder = os.path.dirname(input_data)
        script_name = os.path.basename(input_data)
        script_string = read_file(input_data)
    else:
        workspace_folder = tempfile.mkdtemp()
        script_string = input_data
        write_file(os.path.join(workspace_folder, script_name), script_string)

    logging.info(f"Preparing '{script_name}' in workspace '{workspace_folder}'")

    return workspace_folder, script_name, script_string


def read_file(file_path: str) -> str:
    """
    Reads and returns the content of a file.

    Args:
        file_path (str): The path to the file.

    Returns:
        str: The content of the file.
    """
    with open(file_path, "r") as file:
        return file.read()


def write_file(file_path: str, content: str) -> None:
    """
    Writes content to a file.

    Args:
        file_path (str): The path to the file.
        content (str): The content to be written.
    """
    with open(file_path, "w") as file:
        file.write(content)


def remove_existing_container_and_image(
    client: docker.DockerClient, image_tag: str
) -> None:
    """
    Removes an existing Docker container with the specified image tag.

    Args:
        client (docker.DockerClient): The Docker client instance.
        image_tag (str): The image tag to identify the container.
    """
    try:
        containers = client.containers.list(all=True)
        for container in containers:
            if container.image.tags and image_tag in container.image.tags:
                logging.info(
                    f"Detected previous container: {container.id[:6]} deleting and replacing it now."
                )

                container.stop()
                container.remove()
                image = client.images.get(image_tag)
                client.images.remove(image.id)

    except Exception as e:
        logging.error(
            f"Error removing Docker image or container with tag {image_tag}: {str(e)}"
        )


def build_and_run_container(
    client: docker.DockerClient,
    workspace_folder: str,
    dockerfile_bytes: BytesIO,
    image_tag: str,
    port: str,
) -> docker.models.containers.Container:
    """
    Builds and runs a Docker container.

    Args:
        client (docker.DockerClient): The Docker client instance.
        workspace_folder (str): The workspace folder path.
        dockerfile_bytes (BytesIO): The Dockerfile as a BytesIO object.
        image_tag (str): The tag for the Docker image.
        port (str): The port number to expose.

    Returns:
        docker.models.containers.Container: The Docker container object.
    """
    image, build_logs = client.images.build(
        path=workspace_folder,
        fileobj=dockerfile_bytes,
        rm=True,
        tag=image_tag,
        quiet=False,
    )

    return client.containers.run(
        image.id,
        ports={f"{port}/tcp": int(port)},
        volumes={os.path.abspath(workspace_folder): {"bind": "/usr/share/nginx/html/"}},
        working_dir="/usr/share/nginx/html/",
        stderr=True,
        stdout=True,
        detach=True,
    )
