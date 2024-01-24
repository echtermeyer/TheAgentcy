import asyncpg
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import date

app = FastAPI()

# Database connection function
async def connect_to_db():
    return await asyncpg.connect("postgresql://user:admin@database:5432")

# Create tables and populate with data on startup
async def create_tables_and_populate():
    connection = await connect_to_db()
    await connection.execute('''
        CREATE TABLE IF NOT EXISTS Customer (
            customer_id SERIAL PRIMARY KEY,
            first_name VARCHAR(50),
            last_name VARCHAR(50),
            email VARCHAR(100),
            phone_number VARCHAR(20)
        )
    ''')
    await connection.execute('''
        CREATE TABLE IF NOT EXISTS Sneaker (
            sneaker_id SERIAL PRIMARY KEY,
            brand VARCHAR(50),
            model VARCHAR(100),
            size VARCHAR(10),
            price DECIMAL(10, 2),
            inventory_quantity INT
        )
    ''')
    await connection.execute('''
        CREATE TABLE IF NOT EXISTS PreOrder (
            order_id SERIAL PRIMARY KEY,
            customer_id INT REFERENCES Customer(customer_id),
            sneaker_id INT REFERENCES Sneaker(sneaker_id),
            order_date DATE,
            status VARCHAR(20)
        )
    ''')
    
    # Populate tables with example data
    await connection.execute('''
        INSERT INTO Customer (first_name, last_name, email, phone_number) 
        VALUES ('John', 'Doe', 'john.doe@example.com', '123-456-7890')
    ''')
    await connection.execute('''
        INSERT INTO Sneaker (brand, model, size, price, inventory_quantity) 
        VALUES ('Nike', 'Air Max', '10', 150.00, 50)
    ''')
    await connection.close()

@app.on_event("startup")
async def startup_event():
    await create_tables_and_populate()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for input validation
class Customer(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone_number: str

class Sneaker(BaseModel):
    brand: str
    model: str
    size: str
    price: float
    inventory_quantity: int

class PreOrder(BaseModel):
    customer_id: int
    sneaker_id: int
    order_date: date
    status: str

# Define API endpoints
@app.post("/customer")
async def create_customer(customer: Customer):
    connection = await connect_to_db()
    await connection.execute('''
        INSERT INTO Customer (first_name, last_name, email, phone_number) 
        VALUES ($1, $2, $3, $4)
    ''', customer.first_name, customer.last_name, customer.email, customer.phone_number)
    await connection.close()
    return {"message": "Customer created successfully"}

@app.post("/sneaker")
async def create_sneaker(sneaker: Sneaker):
    connection = await connect_to_db()
    await connection.execute('''
        INSERT INTO Sneaker (brand, model, size, price, inventory_quantity) 
        VALUES ($1, $2, $3, $4, $5)
    ''', sneaker.brand, sneaker.model, sneaker.size, sneaker.price, sneaker.inventory_quantity)
    await connection.close()
    return {"message": "Sneaker created successfully"}

@app.post("/preorder")
async def create_preorder(preorder: PreOrder):
    connection = await connect_to_db()
    await connection.execute('''
        INSERT INTO PreOrder (customer_id, sneaker_id, order_date, status) 
        VALUES ($1, $2, $3, $4)
    ''', preorder.customer_id, preorder.sneaker_id, preorder.order_date, preorder.status)
    await connection.close()
    return {"message": "Pre-order created successfully"}

# Start the backend server
uvicorn.run(app, host="0.0.0.0", port=8000)