import threading
import requests
import io
from contextlib import redirect_stdout, redirect_stderr

def execute_code(code):
    # Redirect the standard output and error to capture them
    f = io.StringIO()
    with redirect_stdout(f), redirect_stderr(f):
        try:
            # Execute the code in a separate thread
            thread = threading.Thread(target=exec, args=(code,))
            thread.start()
            thread.join(timeout=10)  # Adjust the timeout as needed
            if thread.is_alive():
                return {'success': False, 'output': 'Execution timed out.'}
        except Exception as e:
            # Capture any exceptions
            return {'success': False, 'output': str(e)}

    # Capture the output
    output = f.getvalue()
    return {'success': True, 'output': output}

# Example usage
if __name__ == "__main__":
    webserver_code = """
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
async def read_root():
    return {"Hello": "World"}

# Start the web server
uvicorn.run(app, port=8000)
"""
    result = execute_code(webserver_code)
    print("Execution Successful:", result['success'])
    print("Output:\n", result['output'])

    # Example request to the server
    try:
        response = requests.get("http://localhost:8000")
        print("Response from server:", response.json())
    except requests.exceptions.RequestException as e:
        print("Error making request:", e)
