from io import BytesIO
import docker
import os
import re
import tempfile

def extract_dependencies_from_string(script: str):
    dependencies = set()
    for line in script.splitlines():
        matches = re.findall(r'^import (\w+)|^from (\w+)', line)
        for match in matches:
            dependencies.add(match[0] or match[1])
    return dependencies

def extract_port_from_string(script: str) -> str:
    for line in script.splitlines():
        match = re.search(r'port=(\d+)', line)
        if match:
            return match.group(1)
    return '8000'

def create_dockerfile_bytes(script_path: str, script_string: str, dependencies: set, port: str) -> BytesIO:
    if script_path:
        script_name = os.path.basename(script_path)
    else:
        script_name = "script.py"

    dockerfile_str = (
        "FROM python:3.9-slim\n"
        "WORKDIR /app\n"
        "COPY . /app\n"
        f"RUN pip install --no-cache-dir {' '.join(dependencies)}\n"
        f"EXPOSE {port}\n"
        f'CMD ["python", "{script_name}"]\n'
    )
    return BytesIO(dockerfile_str.encode('utf-8'))

def execute_python(input_data) -> any:
    if os.path.isfile(input_data):
        # Handle as file path
        workspace_folder = os.path.dirname(input_data)
        file_name = os.path.basename(input_data)
        with open(input_data, 'r') as file:
            script_string = file.read()
        dependencies = extract_dependencies_from_string(script_string)
        port = extract_port_from_string(script_string)
    else:
        # Handle as script string
        workspace_folder = tempfile.mkdtemp()
        file_name = "script.py"
        script_string = input_data
        with open(os.path.join(workspace_folder, file_name), 'w') as file:
            file.write(script_string)
        dependencies = extract_dependencies_from_string(script_string)
        port = extract_port_from_string(script_string)

    if not file_name.endswith(".py"):
        return "Error: Invalid file type."

    print(f"Executing '{file_name}' in workspace '{workspace_folder}'")

    try:
        client = docker.from_env()
        IMAGE_TAG = "python_webserver_image:latest"

    except Exception as e:
        return f"Error: {str(e)}"

# Usage
# For file path
output = execute_python("path/to/script.py")
print(output)

# For script as a string
script_str = """import flask
app = flask.Flask(__name__)
@app.route('/')
def home():
    return "Hello, World!"
if __name__ == '__main__':
    app.run(port=8000)"""
output = execute_python(script_str)
print(output)
