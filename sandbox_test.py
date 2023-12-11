from src.sandbox.logger import Logger
from src.sandbox.instantiate import PythonSandbox, FrontendSandbox

sandbox_backend = PythonSandbox()
sandbox_frontend = FrontendSandbox()

startup_logger = Logger()

backend_string = """
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
async def read_root():
    return "Backend running!"

# Start the web server
uvicorn.run(app, host="0.0.0.0", port=8000)
"""

frontend_string = """
<!DOCTYPE html>
<html>
<head>
    <title>My Web Page</title>
    <style>
        /* Embedded CSS */
        body {
            font-family: Arial, sans-serif;
            margin: 40px;
            background-color: #f0f0f0;
        }
        h1 {
            color: navy;
        }
        p {
            color: green;
        }
    </style>
</head>
<body>

    <h1>Hello, World!</h1>
    <p>This is my simple web page.</p>
    <button id="myButton">Click Me</button>

    <script>
        // Embedded JavaScript
        document.getElementById('myButton').addEventListener('click', function() {
            alert('Button clicked!');
        });
    </script>

</body>
</html>
"""

backend_container = sandbox_backend.trigger_execution_pipeline(backend_string)
print(backend_container.logs(tail=10).decode("utf-8"))

frontend_container = sandbox_frontend.trigger_execution_pipeline(frontend_string)
print(frontend_container.logs(tail=10).decode("utf-8"))
