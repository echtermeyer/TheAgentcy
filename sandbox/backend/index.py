
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/test")
async def read_root():
    return "Backend running!"

# Start the web server
uvicorn.run(app, host="0.0.0.0", port=8000)
