import asyncpg
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import uvicorn

app = FastAPI()

# Database connection pool
DATABASE_URL = "postgresql://user:admin@database:5432"
pool = None

# Models
class Customer(BaseModel):
    customer_name: str

class Service(BaseModel):
    service_name: str

class Appointment(BaseModel):
    customer_id: int
    service_id: int
    appointment_time: datetime
    confirmation_status: bool

# API Endpoints
@app.on_event("startup")
async def startup():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL)

@app.post("/customers/")
async def create_customer(customer: Customer):
    async with pool.acquire() as connection:
        try:
            query = "INSERT INTO customers (customer_name) VALUES ($1) RETURNING customer_id"
            customer_id = await connection.fetchval(query, customer.customer_name)
            return {"customer_id": customer_id}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

@app.post("/services/")
async def create_service(service: Service):
    async with pool.acquire() as connection:
        try:
            query = "INSERT INTO services (service_name) VALUES ($1) RETURNING service_id"
            service_id = await connection.fetchval(query, service.service_name)
            return {"service_id": service_id}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

@app.post("/appointments/")
async def create_appointment(appointment: Appointment):
    async with pool.acquire() as connection:
        try:
            query = "INSERT INTO appointments (customer_id, service_id, appointment_time, confirmation_status) VALUES ($1, $2, $3, $4) RETURNING appointment_id"
            appointment_id = await connection.fetchval(query, appointment.customer_id, appointment.service_id, appointment.appointment_time, appointment.confirmation_status)
            return {"appointment_id": appointment_id}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

@app.get("/appointments/{appointment_id}")
async def get_appointment(appointment_id: int):
    async with pool.acquire() as connection:
        query = "SELECT * FROM appointments WHERE appointment_id = $1"
        appointment = await connection.fetchrow(query, appointment_id)
        if appointment:
            return appointment
        else:
            raise HTTPException(status_code=404, detail="Appointment not found")

@app.delete("/appointments/{appointment_id}")
async def delete_appointment(appointment_id: int):
    async with pool.acquire() as connection:
        query = "DELETE FROM appointments WHERE appointment_id = $1"
        result = await connection.execute(query, appointment_id)
        if result == "DELETE 1":
            return {"message": "Appointment deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Appointment not found")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Start the backend server
uvicorn.run(app, host="0.0.0.0", port=8000)