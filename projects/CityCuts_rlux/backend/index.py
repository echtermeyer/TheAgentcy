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

# Models
class Customer(BaseModel):
    customer_name: str

class Service(BaseModel):
    service_name: str

class Appointment(BaseModel):
    customer_id: int
    service_id: int
    appointment_time: datetime
    confirmation_status: str

# Create tables and populate with exemplary data on startup
@app.on_event("startup")
async def startup():
    # Connect to the database
    async with asyncpg.create_pool(DATABASE_URL) as pool:
        async with pool.acquire() as connection:
            # Create customers table
            await connection.execute('''
                CREATE TABLE IF NOT EXISTS customers (
                    customer_id SERIAL PRIMARY KEY,
                    customer_name VARCHAR(100) NOT NULL
                )
            ''')
            # Populate customers table with exemplary data
            await connection.execute('''
                INSERT INTO customers (customer_name) VALUES ('John Doe'), ('Jane Smith')
            ''')
            
            # Create services table
            await connection.execute('''
                CREATE TABLE IF NOT EXISTS services (
                    service_id SERIAL PRIMARY KEY,
                    service_name VARCHAR(100) NOT NULL
                )
            ''')
            # Populate services table with exemplary data
            await connection.execute('''
                INSERT INTO services (service_name) VALUES ('Haircut'), ('Massage')
            ''')
            
            # Create appointments table
            await connection.execute('''
                CREATE TABLE IF NOT EXISTS appointments (
                    appointment_id SERIAL PRIMARY KEY,
                    customer_id INT REFERENCES customers(customer_id),
                    service_id INT REFERENCES services(service_id),
                    appointment_time TIMESTAMP NOT NULL,
                    confirmation_status VARCHAR(20) NOT NULL
                )
            ''')
            # Populate appointments table with exemplary data
            await connection.execute('''
                INSERT INTO appointments (customer_id, service_id, appointment_time, confirmation_status)
                VALUES (1, 1, '2022-12-01 10:00:00', 'confirmed'),
                       (2, 2, '2022-12-02 15:00:00', 'pending')
            ''')

# API endpoints
@app.post("/create_customer")
async def create_customer(customer: Customer):
    async with asyncpg.create_pool(DATABASE_URL) as pool:
        async with pool.acquire() as connection:
            await connection.execute('''
                INSERT INTO customers (customer_name) VALUES ($1)
            ''', customer.customer_name)

@app.post("/create_service")
async def create_service(service: Service):
    async with asyncpg.create_pool(DATABASE_URL) as pool:
        async with pool.acquire() as connection:
            await connection.execute('''
                INSERT INTO services (service_name) VALUES ($1)
            ''', service.service_name)

@app.post("/create_appointment")
async def create_appointment(appointment: Appointment):
    async with asyncpg.create_pool(DATABASE_URL) as pool:
        async with pool.acquire() as connection:
            await connection.execute('''
                INSERT INTO appointments (customer_id, service_id, appointment_time, confirmation_status)
                VALUES ($1, $2, $3, $4)
            ''', appointment.customer_id, appointment.service_id, appointment.appointment_time, appointment.confirmation_status)

@app.get("/get_appointments")
async def get_appointments():
    async with asyncpg.create_pool(DATABASE_URL) as pool:
        async with pool.acquire() as connection:
            result = await connection.fetch('''
                SELECT * FROM appointments
            ''')
            return result

# Start the backend server
uvicorn.run(app, host="0.0.0.0", port=8000)