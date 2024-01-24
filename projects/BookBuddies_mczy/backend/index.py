import asyncpg
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Create connection pool
async def create_pool():
    DATABASE_URL = "postgresql://user:admin@database:5432"
    return await asyncpg.create_pool(DATABASE_URL)

# Create tables on startup
async def on_startup():
    app.state.pool = await create_pool()
    async with app.state.pool.acquire() as connection:
        await connection.execute('''
            CREATE TABLE IF NOT EXISTS members (
                member_id SERIAL PRIMARY KEY,
                username VARCHAR(50) NOT NULL,
                email VARCHAR(100) NOT NULL,
                password VARCHAR(100) NOT NULL,
                join_date DATE NOT NULL
            )
        ''')
        await connection.execute('''
            CREATE TABLE IF NOT EXISTS book_suggestions (
                suggestion_id SERIAL PRIMARY KEY,
                member_id INT REFERENCES members(member_id),
                book_title VARCHAR(100) NOT NULL,
                author VARCHAR(100) NOT NULL,
                suggested_date DATE NOT NULL
            )
        ''')
        await connection.execute('''
            CREATE TABLE IF NOT EXISTS monthly_picks (
                pick_id SERIAL PRIMARY KEY,
                book_title VARCHAR(100) NOT NULL,
                author VARCHAR(100) NOT NULL,
                pick_date DATE NOT NULL,
                votes INT DEFAULT 0
            )
        ''')

app.add_event_handler("startup", on_startup)

# API endpoints
@app.post("/register")
async def register_member(username: str, email: str, password: str, join_date: str):
    async with app.state.pool.acquire() as connection:
        await connection.execute(
            "INSERT INTO members (username, email, password, join_date) VALUES ($1, $2, $3, $4)",
            username, email, password, join_date
        )

@app.post("/suggest-book")
async def suggest_book(member_id: int, book_title: str, author: str, suggested_date: str):
    async with app.state.pool.acquire() as connection:
        await connection.execute(
            "INSERT INTO book_suggestions (member_id, book_title, author, suggested_date) VALUES ($1, $2, $3, $4)",
            member_id, book_title, author, suggested_date
        )

@app.post("/vote-monthly-pick")
async def vote_monthly_pick(pick_id: int):
    async with app.state.pool.acquire() as connection:
        await connection.execute(
            "UPDATE monthly_picks SET votes = votes + 1 WHERE pick_id = $1",
            pick_id
        )

@app.get("/get-monthly-picks")
async def get_monthly_picks():
    async with app.state.pool.acquire() as connection:
        monthly_picks = await connection.fetch("SELECT * FROM monthly_picks")
        return monthly_picks