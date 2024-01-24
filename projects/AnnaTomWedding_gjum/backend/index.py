import asyncpg
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

DATABASE_URL = "postgresql://user:admin@database:5432"

app = FastAPI()

# Database Table Creation
async def create_db_table():
    # Establish a connection to the database
    connection = await asyncpg.connect(DATABASE_URL)
    
    # Create the table for storing RSVP responses
    await connection.execute('''
        CREATE TABLE IF NOT EXISTS rsvp_responses (
            id SERIAL PRIMARY KEY,
            guest_name VARCHAR(100) NOT NULL,
            meal_choice VARCHAR(50) NOT NULL
        )
    ''')
    
    # Create indexes for quick retrieval
    await connection.execute('CREATE INDEX IF NOT EXISTS idx_guest_name ON rsvp_responses (guest_name)')
    await connection.execute('CREATE INDEX IF NOT EXISTS idx_meal_choice ON rsvp_responses (meal_choice)')
    
    # Close the connection
    await connection.close()

# Pydantic model for JSON payload
class RSVPResponse(BaseModel):
    guest_name: str
    meal_choice: str

# API endpoint for handling RSVP form submissions
@app.post("/submit_rsvp/")
async def submit_rsvp(response: RSVPResponse):
    # Validate the data
    if len(response.guest_name) > 100 or len(response.meal_choice) > 50:
        raise HTTPException(status_code=400, detail="Input data too long")
    
    # Store the data in the database
    connection = await asyncpg.connect(DATABASE_URL)
    await connection.execute(
        "INSERT INTO rsvp_responses (guest_name, meal_choice) VALUES ($1, $2)",
        response.guest_name,
        response.meal_choice
    )
    await connection.close()
    return {"message": "RSVP response submitted successfully"}

# API endpoint for retrieving all RSVP responses
@app.get("/get_rsvp_responses/")
async def get_rsvp_responses():
    # Retrieve all RSVP responses from the database
    connection = await asyncpg.connect(DATABASE_URL)
    rows = await connection.fetch("SELECT * FROM rsvp_responses")
    await connection.close()
    return rows

# Lifespan event handler to create database table on startup
@app.on_event("startup")
async def startup_event():
    await create_db_table()

# Conditional block to run the server only when the script is executed directly
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)