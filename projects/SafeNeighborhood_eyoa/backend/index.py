import asyncpg
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Database connection string
DATABASE_URL = "postgresql://user:admin@database:5432"

# Create tables and populate with exemplary data
async def create_tables_and_populate():
    # Connect to the database
    pool = await asyncpg.create_pool(DATABASE_URL)
    async with pool.acquire() as connection:
        # Create Users Table
        await connection.execute('''
            CREATE TABLE IF NOT EXISTS Users (
                user_id SERIAL PRIMARY KEY,
                username VARCHAR,
                email VARCHAR,
                password VARCHAR
            )
        ''')
        # Populate Users Table with exemplary data
        await connection.executemany('''
            INSERT INTO Users (username, email, password) VALUES ($1, $2, $3)
        ''', [
            ('user1', 'user1@example.com', 'password1'),
            ('user2', 'user2@example.com', 'password2')
        ])

        # Create Emergency Contacts Table
        await connection.execute('''
            CREATE TABLE IF NOT EXISTS Emergency_Contacts (
                contact_id SERIAL PRIMARY KEY,
                user_id INT REFERENCES Users(user_id),
                contact_name VARCHAR,
                contact_number VARCHAR
            )
        ''')
        # Populate Emergency Contacts Table with exemplary data
        await connection.executemany('''
            INSERT INTO Emergency_Contacts (user_id, contact_name, contact_number) VALUES ($1, $2, $3)
        ''', [
            (1, 'Emergency Contact 1', '1234567890'),
            (2, 'Emergency Contact 2', '9876543210')
        ])

# Model for user registration
class UserRegistration(BaseModel):
    username: str
    email: str
    password: str

# Model for emergency contact
class EmergencyContact(BaseModel):
    user_id: int
    contact_name: str
    contact_number: str

# API endpoint for user registration
@app.post("/register_user")
async def register_user(user: UserRegistration):
    pool = await asyncpg.create_pool(DATABASE_URL)
    async with pool.acquire() as connection:
        await connection.execute(
            "INSERT INTO Users (username, email, password) VALUES ($1, $2, $3)",
            user.username, user.email, user.password
        )
    return {"message": "User registered successfully"}

# API endpoint for adding emergency contact
@app.post("/add_emergency_contact")
async def add_emergency_contact(contact: EmergencyContact):
    pool = await asyncpg.create_pool(DATABASE_URL)
    async with pool.acquire() as connection:
        await connection.execute(
            "INSERT INTO Emergency_Contacts (user_id, contact_name, contact_number) VALUES ($1, $2, $3)",
            contact.user_id, contact.contact_name, contact.contact_number
        )
    return {"message": "Emergency contact added successfully"}

# API endpoint for retrieving user's emergency contacts
@app.get("/emergency_contacts/{user_id}")
async def get_emergency_contacts(user_id: int):
    pool = await asyncpg.create_pool(DATABASE_URL)
    async with pool.acquire() as connection:
        contacts = await connection.fetch(
            "SELECT contact_name, contact_number FROM Emergency_Contacts WHERE user_id = $1",
            user_id
        )
    return contacts

# Lifespan event handler to create tables and populate with exemplary data on startup
@app.on_event("startup")
async def startup_event():
    await create_tables_and_populate()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Start the backend server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)