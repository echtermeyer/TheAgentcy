import asyncpg
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

DATABASE_URL = "postgresql://user:admin@database:5432"

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

# Database models
class User(BaseModel):
    username: str
    password: str
    email: str

class EmergencyContact(BaseModel):
    user_id: int
    contact_name: str
    contact_number: str

# Database connection setup
async def connect_to_db():
    return await asyncpg.connect(DATABASE_URL)

async def close_db_connection(connection):
    await connection.close()

async def startup_db_client():
    connection = await connect_to_db()
    app.state.connection = connection
    # Create tables
    await connection.execute(
        """
        CREATE TABLE IF NOT EXISTS Users (
            user_id SERIAL PRIMARY KEY,
            username VARCHAR(50) NOT NULL,
            password VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL
        )
        """
    )
    await connection.execute(
        """
        CREATE TABLE IF NOT EXISTS EmergencyContacts (
            contact_id SERIAL PRIMARY KEY,
            user_id INT REFERENCES Users(user_id),
            contact_name VARCHAR(100) NOT NULL,
            contact_number VARCHAR(20) NOT NULL
        )
        """
    )
    # Populate tables with exemplary data
    await connection.execute(
        """
        INSERT INTO Users (username, password, email) VALUES ('user1', 'password1', 'user1@example.com')
        """
    )
    await connection.execute(
        """
        INSERT INTO EmergencyContacts (user_id, contact_name, contact_number) VALUES (1, 'Emergency Contact 1', '1234567890')
        """
    )

async def shutdown_db_client():
    await close_db_connection(app.state.connection)

app.router.on_startup.append(startup_db_client)
app.router.on_shutdown.append(shutdown_db_client)

# API endpoints
@app.post("/register_user/")
async def register_user(user: User):
    query = "INSERT INTO Users (username, password, email) VALUES ($1, $2, $3) RETURNING user_id"
    values = (user.username, user.password, user.email)
    user_id = await app.state.connection.fetchval(query, *values)
    return {"user_id": user_id, "username": user.username, "email": user.email}

@app.post("/add_emergency_contact/")
async def add_emergency_contact(contact: EmergencyContact):
    query = "INSERT INTO EmergencyContacts (user_id, contact_name, contact_number) VALUES ($1, $2, $3) RETURNING contact_id"
    values = (contact.user_id, contact.contact_name, contact.contact_number)
    contact_id = await app.state.connection.fetchval(query, *values)
    return {"contact_id": contact_id, "contact_name": contact.contact_name, "contact_number": contact.contact_number}

@app.get("/get_emergency_contacts/{user_id}")
async def get_emergency_contacts(user_id: int):
    query = "SELECT * FROM EmergencyContacts WHERE user_id = $1"
    contacts = await app.state.connection.fetch(query, user_id)
    return contacts

# Start the backend server
uvicorn.run(app, host="0.0.0.0", port=8000)