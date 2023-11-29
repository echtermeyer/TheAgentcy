from sandbox.instantiate import PythonSandbox
from sandbox.logger import Logger


sandbox = PythonSandbox()

init_container = sandbox.init_basic_environment()
container = sandbox.trigger_execution_pipeline("""
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
async def read_root():
    return "Welcome to my life!"

# Start the web server
uvicorn.run(app, host="0.0.0.0", port=8000)""")

print(container.logs(tail=10).decode('utf-8'))
