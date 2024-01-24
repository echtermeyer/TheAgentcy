import asyncpg
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import date, datetime

app = FastAPI()

# Database connection
DATABASE_URL = "postgresql://user:admin@database:5432"

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class FitnessActivity(BaseModel):
    activity_name: str
    activity_date: date
    location_id: int
    user_id: int

class Location(BaseModel):
    location_name: str
    address: str
    city: str
    state: str
    country: str

class UserRegistration(BaseModel):
    user_id: int
    activity_id: int
    registration_date: datetime

# Database setup
async def create_tables():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS fitness_activities (
                activity_id SERIAL PRIMARY KEY,
                activity_name VARCHAR(100),
                activity_date DATE,
                location_id INT,
                user_id INT
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS locations (
                location_id SERIAL PRIMARY KEY,
                location_name VARCHAR(100),
                address VARCHAR(255),
                city VARCHAR(100),
                state VARCHAR(50),
                country VARCHAR(50)
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS user_registrations (
                registration_id SERIAL PRIMARY KEY,
                user_id INT,
                activity_id INT,
                registration_date TIMESTAMP
            )
        ''')
    finally:
        await conn.close()

@app.on_event("startup")
async def startup_event():
    await create_tables()

# API Endpoints
@app.get("/fitness_activities/{activity_id}")
async def read_fitness_activity(activity_id: int):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        result = await conn.fetchrow('SELECT * FROM fitness_activities WHERE activity_id = $1', activity_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Fitness activity not found")
        return result
    finally:
        await conn.close()

@app.get("/user_registrations/{registration_id}")
async def read_user_registration(registration_id: int):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        result = await conn.fetchrow('SELECT * FROM user_registrations WHERE registration_id = $1', registration_id)
        if result is None:
            raise HTTPException(status_code=404, detail="User registration not found")
        return result
    finally:
        await conn.close()

@app.post("/user_registrations/")
async def create_user_registration(user_registration: UserRegistration):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute('''
            INSERT INTO user_registrations (user_id, activity_id, registration_date)
            VALUES ($1, $2, $3)
        ''', user_registration.user_id, user_registration.activity_id, user_registration.registration_date)
        return {"message": "User registration created successfully"}
    finally:
        await conn.close()

# Populate tables with exemplary data
async def populate_tables():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Populate locations table
        await conn.execute('''
            INSERT INTO locations (location_name, address, city, state, country)
            VALUES ($1, $2, $3, $4, $5)
        ''', "Gym A", "123 Main St", "Anytown", "CA", "USA")
        
        # Populate fitness_activities table
        await conn.execute('''
            INSERT INTO fitness_activities (activity_name, activity_date, location_id, user_id)
            VALUES ($1, $2, $3, $4)
        ''', "Yoga Class", date(2022, 10, 15), 1, 1)
        
        # Populate user_registrations table
        await conn.execute('''
            INSERT INTO user_registrations (user_id, activity_id, registration_date)
            VALUES ($1, $2, $3)
        ''', 1, 1, datetime.now())
    finally:
        await conn.close()

@app.on_event("startup")
async def populate_data():
    await populate_tables()

# Start the backend server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)