from io import BytesIO
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
        match = re.search(r'port=(\d+)', line)
        if match:
            return match.group(1)
    return '8000'

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
        matches = re.findall(r'^import (\w+)|^from (\w+)', line)
        for match in matches:
            dependencies.add(match[0] or match[1])
    return dependencies

def execute_code(input_data: str, 
                 container_name: str,
                 dockerfile_method: callable, 
                 dependencies: Set[str],
                 port: str) -> Any:
    """
    Executes a script in a Docker container.

    Args:
        input_data (str): The script as a string or a path to the script file.

    Returns:
        Any: The Docker container object or an error message.
    """
    try:
        workspace_folder, script_name, script_string = prepare_script_workspace(input_data)
        client = docker.from_env()

        if not port:
            port = extract_port_from_string(script_string)
        if not dependencies:
            dependencies = extract_dependencies_from_string(script_string)


        dockerfile_bytes = dockerfile_method(script_name, dependencies, port)

        logging.info(f"Parsing file: {script_name}.")

        # Remove existing container if exists
        remove_existing_container_and_image(client, container_name)

        # Build and run the Docker image
        container = build_and_run_container(client, workspace_folder, dockerfile_bytes, container_name, port)
        
        logging.info(f"Container {container.id[:6]} started successfully.")

        return container

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
    with open(file_path, 'r') as file:
        return file.read()

def write_file(file_path: str, content: str) -> None:
    """
    Writes content to a file.

    Args:
        file_path (str): The path to the file.
        content (str): The content to be written.
    """
    with open(file_path, 'w') as file:
        file.write(content)

def remove_existing_container_and_image(client: docker.DockerClient, image_tag: str) -> None:
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

                logging.info(f"Detected previous container: {container.id[:6]} deleting and replacing it now.")

                container.stop()
                container.remove()
                image = client.images.get(image_tag)
                client.images.remove(image.id)

    except Exception as e:
        logging.error(f"Error removing Docker image or container with tag {image_tag}: {str(e)}")

def build_and_run_container(client: docker.DockerClient, 
                            workspace_folder: str, 
                            dockerfile_bytes: BytesIO, 
                            image_tag: str, 
                            port: str, 
                            network_name: str = "agentcy", 
                            container_name: str = None) -> docker.models.containers.Container:
    """
    Builds and runs a Docker container on a specified network.

    Args:
        client (docker.DockerClient): The Docker client instance.
        workspace_folder (str): The workspace folder path.
        dockerfile_bytes (BytesIO): The Dockerfile as a BytesIO object.
        image_tag (str): The tag for the Docker image.
        port (str): The port number to expose.
        network_name (str): The name of the Docker network to use.
        container_name (str, optional): The name of the Docker container. Defaults to None.

    Returns:
        docker.models.containers.Container: The Docker container object.
    """
    # Check if the network exists, if not, create it
    networks = client.networks.list(names=[network_name])
    if not networks:
        client.networks.create(network_name, driver="bridge")

    # Build the image
    image, build_logs = client.images.build(
        path=workspace_folder,
        fileobj=dockerfile_bytes,
        rm=True,
        tag=image_tag,
        quiet=False
    )

    # Run the container
    container = client.containers.run(
        image.id,
        ports={f"{port}/tcp": int(port)},
        volumes={os.path.abspath(workspace_folder): {'bind': '/usr/share/nginx/html/'}},
        working_dir='/usr/share/nginx/html/',
        network=network_name,
        name=container_name,  # This line sets the container name
        stderr=True,
        stdout=True,
        detach=True,
    )

    return container

