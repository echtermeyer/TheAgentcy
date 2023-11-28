import logging
import threading
from sandbox.instantiate import PythonSandbox

sandbox = PythonSandbox()

init_container = sandbox.init_basic_environment()
container = sandbox.trigger_execution_pipeline("""
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
async def read_root():
    return {"Quick Cahange":"David"}

# Start the web server
uvicorn.run(app, host="0.0.0.0", port=8000)""")

# Stream and print container logs
def stream_docker_logs(container):
    """
    Streams logs from a Docker container.

    Args:
        container (docker.models.containers.Container): The Docker container to stream logs from.
    """
    try:
        for log_line in container.logs(stream=True):
            logging.info(f"Container {container.short_id}: {log_line.decode('utf-8', 'ignore').strip()}")
    except Exception as e:
        logging.error(f"Error streaming logs from container {container.short_id}: {str(e)}")

# Start a new thread to stream the logs
log_thread = threading.Thread(target=stream_docker_logs, args=(container,))
log_thread.start()