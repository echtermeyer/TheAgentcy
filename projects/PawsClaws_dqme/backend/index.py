import asyncpg
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime

# Create FastAPI app
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection string
DATABASE_URL = "postgresql://user:admin@database:5432"

# Function to create table on startup
async def create_table():
    # Connect to the database
    async with asyncpg.create_pool(DATABASE_URL) as pool:
        async with pool.acquire() as connection:
            # Create table if not exists
            await connection.execute('''
                CREATE TABLE IF NOT EXISTS adoption_applications (
                    application_id SERIAL PRIMARY KEY,
                    applicant_name VARCHAR(100) NOT NULL,
                    applicant_email VARCHAR(100) NOT NULL,
                    preferred_pet_type VARCHAR(50) NOT NULL,
                    submission_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

# Pydantic model for adoption application
class AdoptionApplication(BaseModel):
    applicant_name: str
    applicant_email: str
    preferred_pet_type: str

# API endpoint to handle submission of adoption applications
@app.post("/submit_application")
async def submit_application(application: AdoptionApplication):
    # Connect to the database
    async with asyncpg.create_pool(DATABASE_URL) as pool:
        async with pool.acquire() as connection:
            try:
                # Insert application into the database using parameterized query
                await connection.execute(
                    '''
                    INSERT INTO adoption_applications (applicant_name, applicant_email, preferred_pet_type)
                    VALUES ($1, $2, $3)
                    ''',
                    application.applicant_name,
                    application.applicant_email,
                    application.preferred_pet_type
                )
                # Send notification to shelter staff (logic not implemented)
                # Return confirmation message
                return {"message": "Application submitted successfully"}
            except Exception as e:
                raise HTTPException(status_code=500, detail="Failed to submit application")

# API endpoint to retrieve all adoption applications
@app.get("/get_applications")
async def get_applications():
    # Connect to the database
    async with asyncpg.create_pool(DATABASE_URL) as pool:
        async with pool.acquire() as connection:
            # Retrieve all applications from the database
            applications = await connection.fetch('SELECT * FROM adoption_applications')
            return applications

# Lifespan event handler to create table on startup
@app.on_event("startup")
async def startup_event():
    await create_table()

# Start the backend server
uvicorn.run(app, host="0.0.0.0", port=8000)