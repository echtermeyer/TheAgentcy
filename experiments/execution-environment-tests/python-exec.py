from io import BytesIO
import docker
import os
import re

def extract_dependencies(script_path: str):
    dependencies = set()
    with open(script_path, 'r') as file:
        for line in file:
            matches = re.findall(r'^import (\w+)|^from (\w+)', line)
            for match in matches:
                dependencies.add(match[0] or match[1])
    return dependencies

def extract_port(script_path: str) -> str:
    with open(script_path, 'r') as file:
        for line in file:
            match = re.search(r'port=(\d+)', line)
            if match:
                return match.group(1)
    return '8000'

def create_dockerfile_bytes(script_path: str, dependencies: set, port: str) -> BytesIO:
    dockerfile_str = (
        "FROM python:3.9-slim\n"
        "WORKDIR /app\n"
        "COPY . /app\n"
        f"RUN pip install --no-cache-dir {' '.join(dependencies)}\n"
        f"EXPOSE {port}\n"
        f'CMD ["python", "{os.path.basename(script_path)}"]\n'
    )
    return BytesIO(dockerfile_str.encode('utf-8'))

def execute_python_webserver(file_path) -> any:
    workspace_folder = os.path.dirname(file_path)
    file_name = os.path.basename(file_path)

    if not file_name.endswith(".py") or not os.path.isfile(file_path):
        return "Error: Invalid file type or file does not exist."

    print(f"Executing file '{file_name}' in workspace '{workspace_folder}'")

    try:
        client = docker.from_env()
        IMAGE_TAG = "python_webserver_image:latest"

        # Check for existing container and remove it
        containers = client.containers.list(all=True)
        for container in containers:
            if container.image.tags and IMAGE_TAG in container.image.tags:
                print(f"Found existing container {container.id}, stopping and removing it.")
                container.stop()
                container.remove()

        dependencies = extract_dependencies(file_path)
        port = extract_port(file_path)
        dockerfile_bytes = create_dockerfile_bytes(file_path, dependencies, port)

        # Build the Docker image using the Dockerfile bytes
        image, build_logs = client.images.build(
            path=workspace_folder,
            fileobj=dockerfile_bytes,
            rm=True,
            tag=IMAGE_TAG,
            quiet=False
        )
        for log in build_logs:
            print(log.get('stream', '').strip())

        # Run the container
        container = client.containers.run(
            image.id,
            ports={f"{port}/tcp": int(port)},
            volumes={os.path.abspath(workspace_folder): {'bind': '/app', 'mode': 'ro'}},
            working_dir='/app',
            stderr=True,
            stdout=True,
            detach=True,
        )

        print(f"Container started: {container.id}")
        return container

    except Exception as e:
        return f"Error: {str(e)}"

# Usage
output = execute_python_webserver("C:\\Users\\I551674\\Desktop\\5. Semester\\NLP\\Multi-Agent-Frontend-Dev\\sandbox\\backend\\4e761a17-43ca-41b2-8dd5-bc837a570135.py")
print(output)
