from sandbox.instantiate import Python_Sandbox

sandbox = Python_Sandbox()
sandbox.trigger_execution_pipeline("""from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
async def read_root():
    return {"Quick Cahange":"David"}

# Start the web server
uvicorn.run(app, host="0.0.0.0", port=8000)""")