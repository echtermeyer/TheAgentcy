import asyncpg
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

DATABASE_URL = "postgresql://user:admin@database:5432"

app = FastAPI()

# Database table creation
async def create_tables():
    # Connect to the database
    pool = await asyncpg.create_pool(DATABASE_URL)
    async with pool.acquire() as connection:
        # Create tables
        await connection.execute('''
            CREATE TABLE IF NOT EXISTS locations (
                location_id SERIAL PRIMARY KEY,
                location_name VARCHAR(100),
                address VARCHAR(255),
                city VARCHAR(100),
                state VARCHAR(50),
                country VARCHAR(50)
            )
        ''')
        await connection.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id SERIAL PRIMARY KEY,
                username VARCHAR(50),
                password VARCHAR(100),
                email VARCHAR(100)
            )
        ''')
        await connection.execute('''
            CREATE TABLE IF NOT EXISTS activities (
                activity_id SERIAL PRIMARY KEY,
                activity_name VARCHAR(100),
                activity_date DATE,
                location_id INT REFERENCES locations(location_id) DEFERRABLE INITIALLY DEFERRED,
                user_id INT REFERENCES users(user_id) DEFERRABLE INITIALLY DEFERRED
            )
        ''')

# Data population
async def populate_data():
    # Connect to the database
    pool = await asyncpg.create_pool(DATABASE_URL)
    async with pool.acquire() as connection:
        # Populate tables with exemplary data
        await connection.execute('''
            INSERT INTO locations (location_name, address, city, state, country) 
            VALUES ('Gym A', '123 Main St', 'Anytown', 'CA', 'USA')
        ''')
        await connection.execute('''
            INSERT INTO users (username, password, email) 
            VALUES ('user1', 'password1', 'user1@example.com')
        ''')
        await connection.execute('''
            INSERT INTO activities (activity_name, activity_date, location_id, user_id) 
            VALUES ('Yoga Class', '2022-10-15', 1, 1)
        ''')

# Define Pydantic models
class Location(BaseModel):
    location_name: str
    address: str
    city: str
    state: str
    country: str

class User(BaseModel):
    username: str
    password: str
    email: str

class Activity(BaseModel):
    activity_name: str
    activity_date: str
    location_id: int
    user_id: int

# API endpoints for data retrieval and user registration
@app.get("/activities/{activity_id}")
async def get_activity(activity_id: int):
    async with asyncpg.create_pool(DATABASE_URL) as pool:
        async with pool.acquire() as connection:
            result = await connection.fetchrow('SELECT * FROM activities WHERE activity_id = $1', activity_id)
            if result is None:
                raise HTTPException(status_code=404, detail="Activity not found")
            return result

@app.post("/activities/create")
async def create_activity(activity: Activity):
    async with asyncpg.create_pool(DATABASE_URL) as pool:
        async with pool.acquire() as connection:
            await connection.execute('''
                INSERT INTO activities (activity_name, activity_date, location_id, user_id) 
                VALUES ($1, $2, $3, $4)
            ''', activity.activity_name, activity.activity_date, activity.location_id, activity.user_id)
            return {"message": "Activity created successfully"}

@app.post("/users/register")
async def register_user(user: User):
    async with asyncpg.create_pool(DATABASE_URL) as pool:
        async with pool.acquire() as connection:
            await connection.execute('''
                INSERT INTO users (username, password, email) 
                VALUES ($1, $2, $3)
            ''', user.username, user.password, user.email)
            return {"message": "User registered successfully"}

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Call create_tables and populate_data functions inside an async function
async def startup_event():
    await create_tables()
    await populate_data()

# Start the FastAPI application
@app.on_event("startup")
async def startup():
    await startup_event()

uvicorn.run(app, host="0.0.0.0", port=8000)