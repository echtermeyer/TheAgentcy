import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncpg
from pydantic import BaseModel
import datetime

app = FastAPI()

# Database connection pool
DATABASE_URL = "postgresql://user:admin@database:5432"
pool = None

class Member(BaseModel):
    name: str
    email: str
    password: str

class BookSuggestion(BaseModel):
    suggested_by: int
    title: str
    author: str
    suggested_on: datetime.date

class MonthlyPick(BaseModel):
    book_id: int
    picked_on: datetime.date

@app.on_event("startup")
async def startup():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL)

    async with pool.acquire() as connection:
        # Create tables
        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS members (
                member_id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(100) NOT NULL
            )
            """
        )
        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS book_suggestions (
                suggestion_id SERIAL PRIMARY KEY,
                suggested_by INT REFERENCES members(member_id),
                title VARCHAR(200) NOT NULL,
                author VARCHAR(100) NOT NULL,
                suggested_on DATE
            )
            """
        )
        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS monthly_picks (
                pick_id SERIAL PRIMARY KEY,
                book_id INT REFERENCES book_suggestions(suggestion_id),
                picked_on DATE
            )
            """
        )

        # Populate tables with data
        await connection.execute(
            """
            INSERT INTO members (name, email, password) VALUES 
            ('John Doe', 'john@example.com', 'password123'),
            ('Jane Smith', 'jane@example.com', 'password456')
            """
        )
        await connection.execute(
            """
            INSERT INTO book_suggestions (suggested_by, title, author, suggested_on) VALUES 
            (1, 'The Great Gatsby', 'F. Scott Fitzgerald', '2022-01-15'),
            (2, 'To Kill a Mockingbird', 'Harper Lee', '2022-01-20')
            """
        )
        await connection.execute(
            """
            INSERT INTO monthly_picks (book_id, picked_on) VALUES 
            (1, '2022-02-01'),
            (2, '2022-02-01')
            """
        )

@app.post("/members")
async def create_member(member: Member):
    async with pool.acquire() as connection:
        await connection.execute(
            "INSERT INTO members (name, email, password) VALUES ($1, $2, $3)",
            member.name, member.email, member.password
        )
    return {"message": "Member created successfully"}

@app.post("/book_suggestions")
async def suggest_book(book_suggestion: BookSuggestion):
    async with pool.acquire() as connection:
        await connection.execute(
            "INSERT INTO book_suggestions (suggested_by, title, author, suggested_on) VALUES ($1, $2, $3, $4)",
            book_suggestion.suggested_by, book_suggestion.title, book_suggestion.author, book_suggestion.suggested_on
        )
    return {"message": "Book suggestion added successfully"}

@app.post("/monthly_picks")
async def pick_monthly_book(monthly_pick: MonthlyPick):
    async with pool.acquire() as connection:
        await connection.execute(
            "INSERT INTO monthly_picks (book_id, picked_on) VALUES ($1, $2)",
            monthly_pick.book_id, monthly_pick.picked_on
        )
    return {"message": "Monthly pick added successfully"}

@app.get("/book_suggestions")
async def get_book_suggestions():
    async with pool.acquire() as connection:
        rows = await connection.fetch("SELECT * FROM book_suggestions")
    return rows

@app.get("/monthly_picks")
async def get_monthly_picks():
    async with pool.acquire() as connection:
        rows = await connection.fetch("SELECT * FROM monthly_picks")
    return rows

@app.delete("/book_suggestions/{suggestion_id}")
async def delete_book_suggestion(suggestion_id: int):
    async with pool.acquire() as connection:
        await connection.execute("DELETE FROM book_suggestions WHERE suggestion_id = $1", suggestion_id)
    return {"message": "Book suggestion deleted successfully"}

@app.delete("/monthly_picks/{pick_id}")
async def delete_monthly_pick(pick_id: int):
    async with pool.acquire() as connection:
        await connection.execute("DELETE FROM monthly_picks WHERE pick_id = $1", pick_id)
    return {"message": "Monthly pick deleted successfully"}

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