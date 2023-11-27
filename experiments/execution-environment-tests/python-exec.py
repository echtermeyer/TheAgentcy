import docker
import os

def execute_python_webserver(file_path):
    """Execute a Python web server file in a Docker container."""
    # Assuming the workspace is the parent directory of the file
    workspace_folder = os.path.dirname(file_path)

    # Extract the filename from the path
    file_name = os.path.basename(file_path)

    print(f"Executing file '{file_name}' in workspace '{workspace_folder}'")

    if not file_name.endswith(".py"):
        return "Error: Invalid file type. Only .py files are allowed."

    if not os.path.isfile(file_path):
        return f"Error: File '{file_name}' does not exist."

    try:
        client = docker.from_env()

        # Replace 'python:3.10' with an image that contains all the necessary dependencies
        container = client.containers.run(
            'python:3.10',  # Replace with your custom image name
            f'python {file_name}',
            ports={'8000/tcp': 8000},  # Map the container port to a host port, adjust as needed
            volumes={os.path.abspath(workspace_folder): {'bind': '/workspace', 'mode': 'ro'}},
            working_dir='/workspace',
            stderr=True,
            stdout=True,
            detach=True,
        )

        print(f"Container started: {container.id}")
        return f"Web server running in container {container.id}"

    except Exception as e:
        return f"Error: {str(e)}"

# Usage
output = execute_python_webserver("C:\\Users\\Lasse\\Desktop\\5. Semester\\NLP\\Agentcy\\Multi-Agent-Frontend-Dev\\execution-environment-tests\\test.py")
print(output)
