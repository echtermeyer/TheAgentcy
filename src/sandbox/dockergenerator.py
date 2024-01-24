from io import BytesIO
import subprocess
import docker
import os
import re
import tempfile
from typing import Any, Set, Tuple
import logging


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


def execute_code(
    input_data: str,
    image_tag: str,
    container_name: str,
    dockerfile_method: callable,
    dependencies: Set[str],
    port: str,
) -> str:
    """
    Executes a script in a Docker container.

    Args:
        input_data (str): The script as a string or a path to the script file.

    Returns:
        str: The Docker container_id string.
    """
    try:
        workspace_folder, script_name, script_string = prepare_script_workspace(
            input_data
        )
        client = docker.from_env()

        if not port:
            port = extract_port_from_string(script_string)
        if not dependencies:
            dependencies = extract_dependencies_from_string(script_string)

        dockerfile_bytes = dockerfile_method(script_name, dependencies, port)

        logging.info(f"Parsing file: {script_name}.")

        # Remove existing container if exists
        remove_existing_container_and_image(client, container_name, image_tag)

        # Build and run the Docker image
        container_id = build_and_run_container(
            workspace_folder=workspace_folder,
            dockerfile_bytes=dockerfile_bytes,
            container_name=container_name,
            image_tag=image_tag,
            port=port,
        )

        logging.info(f"Container {container_id} started successfully.")

        return container_id

    except Exception as e:
        logging.error(f"Error in execute_code: {str(e)}")
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
    client: docker.DockerClient, container_name: str, image_tag: str
) -> None:
    """
    Removes an existing Docker container by its name and the associated image by its tag.

    Args:
        client (docker.DockerClient): The Docker client instance.
        container_name (str): The name of the container to remove.
        image_tag (str): The tag of the image to remove.
    """
    try:
        # Try to get the container by name and remove it
        try:
            container = client.containers.get(container_name)
            logging.info(f"Removing container: {container_name}")
            container.stop()
            container.remove()
        except docker.errors.NotFound:
            logging.info(f"No container found with name: {container_name}")

        # Remove the image associated with the given tag
        try:
            image = client.images.get(image_tag)
            logging.info(f"Removing image: {image_tag}")
            client.images.remove(image.id)
        except docker.errors.ImageNotFound:
            logging.info(f"No image found with tag: {image_tag}")
        except docker.errors.APIError as e:
            logging.error(f"Error removing image with tag {image_tag}: {str(e)}")

    except Exception as e:
        logging.error(f"General error in removing container or image: {str(e)}")


def build_and_run_container(
    workspace_folder: str,
    dockerfile_bytes: BytesIO,
    image_tag: str,
    port: str,
    network_name: str = "Agentcy",
    container_name: str = None,
):
    """
    Builds and runs a Docker container on a specified network.

    Args:
        workspace_folder (str): The workspace folder path.
        dockerfile_bytes (BytesIO): The Dockerfile as a BytesIO object.
        image_tag (str): The tag for the Docker image.
        port (str): The port number to expose.
        network_name (str): The name of the Docker network to use.
        container_name (str, optional): The name of the Docker container. Defaults to None.

    Returns:
        The container ID on success, None on failure.
    """
    try:
        # Write the Dockerfile bytes to a file
        dockerfile_path = os.path.join(workspace_folder, "Dockerfile")
        with open(dockerfile_path, "wb") as dockerfile:
            dockerfile.write(dockerfile_bytes.getvalue())

        # Check if the network exists, if not, create it
        networks_command = ["docker", "network", "ls", "--format", "{{.Name}}"]
        networks = subprocess.check_output(networks_command).decode().splitlines()
        if network_name not in networks:
            subprocess.run(["docker", "network", "create", network_name], check=True)

        # Build the image
        subprocess.run(
            ["docker", "build", "-t", image_tag, workspace_folder], check=True
        )

        # Run the container
        run_command = [
            "docker",
            "run",
            "-d",
            "--name",
            container_name or "",
            "-p",
            f"{port}:{port}",
            "-v",
            f"{os.path.abspath(workspace_folder)}:/usr/share/nginx/html/",
            "-w",
            "/usr/share/nginx/html/",
            "--network",
            network_name,
            image_tag,
        ]
        container_id = subprocess.check_output(run_command).decode().strip()

        return container_id

    except subprocess.CalledProcessError as e:
        print(
            f"An error occurred: {e}. Please make sure Docker Daemon is installed and running."
        )
        return None
