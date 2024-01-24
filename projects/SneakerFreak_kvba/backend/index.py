import asyncpg
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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
    # Establish a connection to the database
    async with asyncpg.create_pool(DATABASE_URL) as pool:
        async with pool.acquire() as connection:
            # Create Sneaker table
            await connection.execute('''
                CREATE TABLE IF NOT EXISTS Sneaker (
                    sneaker_id SERIAL PRIMARY KEY,
                    model VARCHAR(100) NOT NULL,
                    brand VARCHAR(50),
                    color VARCHAR(50),
                    size VARCHAR(10),
                    price DECIMAL(10, 2),
                    inventory_quantity INT
                )
            ''')
            # Populate Sneaker table with exemplary data
            await connection.execute('''
                INSERT INTO Sneaker (model, brand, color, size, price, inventory_quantity)
                VALUES 
                    ('Air Max', 'Nike', 'Black', 'US10', 150.00, 100),
                    ('Classic Leather', 'Reebok', 'White', 'US9', 80.00, 75),
                    ('Old Skool', 'Vans', 'Red', 'US8', 65.00, 120)
            ''')

            # Create Customer table
            await connection.execute('''
                CREATE TABLE IF NOT EXISTS Customer (
                    customer_id SERIAL PRIMARY KEY,
                    first_name VARCHAR(50) NOT NULL,
                    last_name VARCHAR(50) NOT NULL,
                    email VARCHAR(100) UNIQUE,
                    phone_number VARCHAR(20),
                    address VARCHAR(255)
                )
            ''')
            # Populate Customer table with exemplary data
            await connection.execute('''
                INSERT INTO Customer (first_name, last_name, email, phone_number, address)
                VALUES 
                    ('John', 'Doe', 'john.doe@example.com', '123-456-7890', '123 Main St'),
                    ('Jane', 'Smith', 'jane.smith@example.com', '987-654-3210', '456 Elm St')
            ''')

            # Create PreOrder table
            await connection.execute('''
                CREATE TABLE IF NOT EXISTS PreOrder (
                    order_id SERIAL PRIMARY KEY,
                    customer_id INT,
                    sneaker_id INT,
                    order_date DATE,
                    status VARCHAR(20),
                    FOREIGN KEY (customer_id) REFERENCES Customer(customer_id),
                    FOREIGN KEY (sneaker_id) REFERENCES Sneaker(sneaker_id)
                )
            ''')
            # Populate PreOrder table with exemplary data
            await connection.execute('''
                INSERT INTO PreOrder (customer_id, sneaker_id, order_date, status)
                VALUES 
                    (1, 1, '2022-05-01', 'Pending'),
                    (2, 3, '2022-05-03', 'Confirmed')
            ''')

# Pydantic models for JSON Payload
class SneakerIn(BaseModel):
    model: str
    brand: str
    color: str
    size: str
    price: float
    inventory_quantity: int

class CustomerIn(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone_number: str
    address: str

class PreOrderIn(BaseModel):
    customer_id: int
    sneaker_id: int
    order_date: str
    status: str

# API endpoints for handling pre-order requests, updating inventory, and managing order confirmations
@app.post("/sneaker/create/", response_model=SneakerIn)
async def create_sneaker(sneaker: SneakerIn):
    async with asyncpg.create_pool(DATABASE_URL) as pool:
        async with pool.acquire() as connection:
            await connection.execute('''
                INSERT INTO Sneaker (model, brand, color, size, price, inventory_quantity)
                VALUES ($1, $2, $3, $4, $5, $6)
            ''', sneaker.model, sneaker.brand, sneaker.color, sneaker.size, sneaker.price, sneaker.inventory_quantity)
    return sneaker

# Other API endpoints (to be implemented)

# Start the backend server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)