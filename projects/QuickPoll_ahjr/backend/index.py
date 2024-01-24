import asyncpg
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import date

# Database connection string
DATABASE_URL = "postgresql://user:admin@database:5432"

# FastAPI app
app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database table creation and data population on startup
@app.on_event("startup")
async def startup():
    # Connect to the database
    async with asyncpg.create_pool(DATABASE_URL) as pool:
        async with pool.acquire() as connection:
            # Create employees table
            await connection.execute('''
                CREATE TABLE IF NOT EXISTS employees (
                    employee_id SERIAL PRIMARY KEY,
                    first_name VARCHAR(50) NOT NULL,
                    last_name VARCHAR(50) NOT NULL,
                    department VARCHAR(50) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL
                )
            ''')
            # Populate employees table with exemplary data
            await connection.execute('''
                INSERT INTO employees (first_name, last_name, department, email)
                VALUES ('John', 'Doe', 'Engineering', 'john.doe@example.com'),
                       ('Jane', 'Smith', 'Marketing', 'jane.smith@example.com')
            ''')

            # Create poll_questions table
            await connection.execute('''
                CREATE TABLE IF NOT EXISTS poll_questions (
                    question_id SERIAL PRIMARY KEY,
                    question_text TEXT NOT NULL,
                    week_start_date DATE NOT NULL
                )
            ''')
            # Populate poll_questions table with exemplary data
            await connection.execute('''
                INSERT INTO poll_questions (question_text, week_start_date)
                VALUES ('How satisfied are you with the new project management tool?', '2023-10-02'),
                       ('Would you recommend our company to a friend?', '2023-10-09')
            ''')

            # Create poll_responses table
            await connection.execute('''
                CREATE TABLE IF NOT EXISTS poll_responses (
                    response_id SERIAL PRIMARY KEY,
                    employee_id INT REFERENCES employees(employee_id),
                    question_id INT REFERENCES poll_questions(question_id),
                    response_value VARCHAR(20) NOT NULL,
                    response_date DATE NOT NULL
                )
            ''')
            # Populate poll_responses table with exemplary data
            await connection.execute('''
                INSERT INTO poll_responses (employee_id, question_id, response_value, response_date)
                VALUES (1, 1, 'Satisfied', '2023-10-02'),
                       (2, 1, 'Neutral', '2023-10-02'),
                       (1, 2, 'Yes', '2023-10-09'),
                       (2, 2, 'Yes', '2023-10-09')
            ''')

# Pydantic models for JSON payloads
class Employee(BaseModel):
    first_name: str
    last_name: str
    department: str
    email: str

class PollQuestion(BaseModel):
    question_text: str
    week_start_date: date

class PollResponse(BaseModel):
    employee_id: int
    question_id: int
    response_value: str
    response_date: date

# API endpoints
@app.post("/employees/create")
async def create_employee(employee: Employee):
    async with asyncpg.create_pool(DATABASE_URL) as pool:
        async with pool.acquire() as connection:
            await connection.execute('''
                INSERT INTO employees (first_name, last_name, department, email)
                VALUES ($1, $2, $3, $4)
            ''', employee.first_name, employee.last_name, employee.department, employee.email)
    return {"message": "Employee created successfully"}

@app.get("/employees/{employee_id}")
async def get_employee(employee_id: int):
    async with asyncpg.create_pool(DATABASE_URL) as pool:
        async with pool.acquire() as connection:
            employee = await connection.fetchrow('''
                SELECT * FROM employees WHERE employee_id = $1
            ''', employee_id)
            if employee is None:
                raise HTTPException(status_code=404, detail="Employee not found")
            return employee

@app.post("/poll/questions/create")
async def create_poll_question(poll_question: PollQuestion):
    async with asyncpg.create_pool(DATABASE_URL) as pool:
        async with pool.acquire() as connection:
            await connection.execute('''
                INSERT INTO poll_questions (question_text, week_start_date)
                VALUES ($1, $2)
            ''', poll_question.question_text, poll_question.week_start_date)
    return {"message": "Poll question created successfully"}

@app.get("/poll/questions/{question_id}")
async def get_poll_question(question_id: int):
    async with asyncpg.create_pool(DATABASE_URL) as pool:
        async with pool.acquire() as connection:
            question = await connection.fetchrow('''
                SELECT * FROM poll_questions WHERE question_id = $1
            ''', question_id)
            if question is None:
                raise HTTPException(status_code=404, detail="Poll question not found")
            return question

@app.post("/poll/responses/create")
async def create_poll_response(poll_response: PollResponse):
    async with asyncpg.create_pool(DATABASE_URL) as pool:
        async with pool.acquire() as connection:
            await connection.execute('''
                INSERT INTO poll_responses (employee_id, question_id, response_value, response_date)
                VALUES ($1, $2, $3, $4)
            ''', poll_response.employee_id, poll_response.question_id, poll_response.response_value, poll_response.response_date)
    return {"message": "Poll response created successfully"}

@app.get("/poll/responses/{response_id}")
async def get_poll_response(response_id: int):
    async with asyncpg.create_pool(DATABASE_URL) as pool:
        async with pool.acquire() as connection:
            response = await connection.fetchrow('''
                SELECT * FROM poll_responses WHERE response_id = $1
            ''', response_id)
            if response is None:
                raise HTTPException(status_code=404, detail="Poll response not found")
            return response

# Start the backend server
uvicorn.run(app, host="0.0.0.0", port=8000)