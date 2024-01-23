from io import BytesIO
import os
from typing import Set
import docker

def create_dockerfile_bytes(
        self, script_name: str, dependencies = [], port = 8000
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




def build_and_run_container(client: docker.DockerClient, 
                            workspace_folder: str, 
                            dockerfile_bytes: BytesIO, 
                            image_tag: str, 
                            port: str, 
                            network_name: str = "Agentcy", 
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
        quiet=True,
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