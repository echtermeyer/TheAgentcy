from src.instantiate import PythonSandbox, FrontendSandbox
from src.logger import Logger

sandbox_backend = PythonSandbox()
sandbox_frontend= FrontendSandbox()
# test_container = PythonSandbox("test", "testy", "test:latest")

startup_logger = Logger()

backend_string = """
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/test")
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
    <p id="apiResponse"></p>

    <script>
        // Embedded JavaScript
        document.getElementById('myButton').addEventListener('click', function() {
            fetch('http://localhost:8000/test')
                .then(response => response.text())
                .then(data => {
                    document.getElementById('apiResponse').textContent = data;
                })
                .catch(error => {
                    console.error('Error:', error);
                    document.getElementById('apiResponse').textContent = 'Failed to get response';
                });
        });
    </script>

</body>
</html>
"""

# test_container = test_container.trigger_execution_pipeline(backend_string, dependencies=["FastAPI", "uvicorn"], port="8001")


backend_container = sandbox_backend.trigger_execution_pipeline(backend_string, dependencies=["FastAPI", "uvicorn"])
ip_addr_backend = backend_container.attrs['NetworkSettings']['Networks']['Agentcy']['IPAddress']
print(backend_container.logs(tail=10).decode('utf-8'))
print("IP Adresse in Docker Netzwerk:" + ip_addr_backend)


frontend_container = sandbox_frontend.trigger_execution_pipeline(frontend_string)
ip_addr_frontend = backend_container.attrs['NetworkSettings']['Networks']['Agentcy']['IPAddress']
print(frontend_container.logs(tail=10).decode('utf-8'))
print("IP Adresse in Docker Netzwerk:" + ip_addr_frontend)