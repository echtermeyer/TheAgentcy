import asyncpg
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime

# Database connection string
DATABASE_URL = "postgresql://user:admin@database:5432"

# FastAPI app
app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database models
class Employee(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str

class PollQuestion(BaseModel):
    question_text: str

class PollResponse(BaseModel):
    employee_id: int
    question_id: int
    response_text: str

# Database setup on startup
@app.on_event("startup")
async def startup():
    # Connect to the database
    app.state.pool = await asyncpg.create_pool(DATABASE_URL)

    # Create tables
    async with app.state.pool.acquire() as connection:
        await connection.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                employee_id SERIAL PRIMARY KEY,
                first_name VARCHAR(50),
                last_name VARCHAR(50),
                email VARCHAR(100) UNIQUE,
                password VARCHAR(100) NOT NULL
            )
        ''')
        await connection.execute('''
            CREATE TABLE IF NOT EXISTS poll_questions (
                question_id SERIAL PRIMARY KEY,
                question_text VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await connection.execute('''
            CREATE TABLE IF NOT EXISTS poll_responses (
                response_id SERIAL PRIMARY KEY,
                employee_id INT REFERENCES employees(employee_id),
                question_id INT REFERENCES poll_questions(question_id),
                response_text VARCHAR(255) NOT NULL,
                response_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

# API endpoints
@app.post("/employees/")
async def create_employee(employee: Employee):
    async with app.state.pool.acquire() as connection:
        await connection.execute(
            "INSERT INTO employees (first_name, last_name, email, password) VALUES ($1, $2, $3, $4)",
            employee.first_name, employee.last_name, employee.email, employee.password
        )

@app.post("/polls/")
async def create_poll_question(poll_question: PollQuestion):
    async with app.state.pool.acquire() as connection:
        await connection.execute(
            "INSERT INTO poll_questions (question_text) VALUES ($1)",
            poll_question.question_text
        )

@app.post("/polls/responses/")
async def create_poll_response(poll_response: PollResponse):
    async with app.state.pool.acquire() as connection:
        await connection.execute(
            "INSERT INTO poll_responses (employee_id, question_id, response_text) VALUES ($1, $2, $3)",
            poll_response.employee_id, poll_response.question_id, poll_response.response_text
        )

@app.get("/polls/responses/{question_id}")
async def get_poll_responses(question_id: int):
    async with app.state.pool.acquire() as connection:
        rows = await connection.fetch(
            "SELECT * FROM poll_responses WHERE question_id = $1",
            question_id
        )
        return rows

# Start the backend server
uvicorn.run(app, host="0.0.0.0", port=8000)