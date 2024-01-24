import asyncpg
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime

app = FastAPI()

# Database connection string
DATABASE_URL = "postgresql://user:admin@database:5432"

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables and populate with exemplary data on startup
@app.on_event("startup")
async def startup():
    # Connect to the database
    conn = await asyncpg.connect(DATABASE_URL)
    
    # Create tables
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS Applicant (
            applicant_id SERIAL PRIMARY KEY,
            first_name VARCHAR(50),
            last_name VARCHAR(50),
            email VARCHAR(100),
            phone_number VARCHAR(20),
            address VARCHAR(100)
        )
    ''')
    
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS PetPreference (
            preference_id SERIAL,
            applicant_id INT,
            pet_type VARCHAR(50),
            pet_breed VARCHAR(50),
            pet_age INT,
            PRIMARY KEY (preference_id, applicant_id),
            FOREIGN KEY (applicant_id) REFERENCES Applicant(applicant_id) ON DELETE CASCADE
        )
    ''')
    
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS ApplicationSubmission (
            submission_id SERIAL PRIMARY KEY,
            applicant_id INT,
            submission_timestamp TIMESTAMP,
            FOREIGN KEY (applicant_id) REFERENCES Applicant(applicant_id) ON DELETE CASCADE
        )
    ''')
    
    # Populate tables with exemplary data
    await conn.execute('''
        INSERT INTO Applicant (first_name, last_name, email, phone_number, address)
        VALUES ('John', 'Doe', 'john.doe@example.com', '123-456-7890', '123 Main St')
    ''')
    
    await conn.execute('''
        INSERT INTO PetPreference (applicant_id, pet_type, pet_breed, pet_age)
        VALUES (1, 'Dog', 'Golden Retriever', 3)
    ''')
    
    await conn.execute('''
        INSERT INTO ApplicationSubmission (applicant_id, submission_timestamp)
        VALUES (1, '2022-01-01 12:00:00')
    ''')
    
    # Close the connection
    await conn.close()

# Pydantic models for JSON payloads
class ApplicantData(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone_number: str
    address: str

class PetPreferenceData(BaseModel):
    applicant_id: int
    pet_type: str
    pet_breed: str
    pet_age: int

class SubmissionData(BaseModel):
    applicant_id: int

# API endpoints
@app.post("/submit_application")
async def submit_application(applicant_data: ApplicantData, pet_preference_data: PetPreferenceData):
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Insert applicant data into Applicant table
        await conn.execute('''
            INSERT INTO Applicant (first_name, last_name, email, phone_number, address)
            VALUES ($1, $2, $3, $4, $5)
        ''', applicant_data.first_name, applicant_data.last_name, applicant_data.email, applicant_data.phone_number, applicant_data.address)
        
        # Get the applicant_id of the newly inserted applicant
        applicant_id = await conn.fetchval('''
            SELECT applicant_id FROM Applicant
            WHERE email = $1
        ''', applicant_data.email)
        
        # Insert pet preference data into PetPreference table
        await conn.execute('''
            INSERT INTO PetPreference (applicant_id, pet_type, pet_breed, pet_age)
            VALUES ($1, $2, $3, $4)
        ''', applicant_id, pet_preference_data.pet_type, pet_preference_data.pet_breed, pet_preference_data.pet_age)
        
        # Insert submission data into ApplicationSubmission table
        await conn.execute('''
            INSERT INTO ApplicationSubmission (applicant_id, submission_timestamp)
            VALUES ($1, $2)
        ''', applicant_id, datetime.now())
        
        return {"message": "Application submitted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
    finally:
        await conn.close()

@app.get("/get_applicant/{applicant_id}")
async def get_applicant(applicant_id: int):
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Get applicant details
        applicant = await conn.fetchrow('''
            SELECT * FROM Applicant
            WHERE applicant_id = $1
        ''', applicant_id)
        
        if applicant is None:
            raise HTTPException(status_code=404, detail="Applicant not found")
        
        return applicant
    finally:
        await conn.close()

@app.delete("/delete_application/{applicant_id}")
async def delete_application(applicant_id: int):
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Delete applicant and related data
        await conn.execute('''
            DELETE FROM ApplicationSubmission
            WHERE applicant_id = $1
        ''', applicant_id)
        
        await conn.execute('''
            DELETE FROM PetPreference
            WHERE applicant_id = $1
        ''', applicant_id)
        
        await conn.execute('''
            DELETE FROM Applicant
            WHERE applicant_id = $1
        ''', applicant_id)
        
        return {"message": "Application deleted successfully"}
    finally:
        await conn.close()

# Start the backend server
uvicorn.run(app, host="0.0.0.0", port=8000)