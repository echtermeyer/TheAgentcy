from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncpg
from pydantic import BaseModel
import pandas as pd
import numpy as np

app = FastAPI()

# Database Connection
DATABASE_URL = "postgresql://user:admin@database:5432"

@app.on_event("startup")
async def startup():
    app.db_pool = await asyncpg.create_pool(DATABASE_URL)

    # Create tables
    async with app.db_pool.acquire() as connection:
        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS category (
                id SERIAL PRIMARY KEY,
                name VARCHAR NOT NULL
            )
            """
        )
        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS suggestion (
                id SERIAL PRIMARY KEY,
                title VARCHAR NOT NULL,
                description TEXT NOT NULL,
                category_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """
        )

        # Populate tables
        await populate_tables()

@app.on_event("shutdown")
async def shutdown():
    await app.db_pool.close()

# Pydantic Models
class Suggestion(BaseModel):
    title: str
    description: str
    category_id: int

class Category(BaseModel):
    name: str

class UpdateSuggestion(BaseModel):
    new_title: str

# API Endpoints
@app.post("/submit_suggestion/")
async def submit_suggestion(suggestion: Suggestion):
    async with app.db_pool.acquire() as connection:
        await connection.execute(
            "INSERT INTO suggestion (title, description, category_id) VALUES ($1, $2, $3)",
            suggestion.title, suggestion.description, suggestion.category_id
        )
    return {"message": "Suggestion submitted successfully"}

@app.get("/get_suggestions/")
async def get_suggestions():
    async with app.db_pool.acquire() as connection:
        rows = await connection.fetch("SELECT * FROM suggestion")
        suggestions = [dict(row) for row in rows]
    return {"suggestions": suggestions}

@app.put("/update_suggestion/{suggestion_id}")
async def update_suggestion(suggestion_id: int, updated_suggestion: UpdateSuggestion):
    async with app.db_pool.acquire() as connection:
        result = await connection.execute(
            "UPDATE suggestion SET title = $1 WHERE id = $2",
            updated_suggestion.new_title, suggestion_id
        )
        if result == "UPDATE 0":
            raise HTTPException(status_code=404, detail="Suggestion not found")
    return {"message": "Suggestion updated successfully"}

# Populate Tables with Example Data
async def populate_tables():
    async with app.db_pool.acquire() as connection:
        # Populate category table
        await connection.execute("INSERT INTO category (name) VALUES ($1)", "Feature")
        await connection.execute("INSERT INTO category (name) VALUES ($1)", "Bug")
        await connection.execute("INSERT INTO category (name) VALUES ($1)", "Improvement")

        # Populate suggestion table
        await connection.execute(
            "INSERT INTO suggestion (title, description, category_id) VALUES ($1, $2, $3)",
            "New Feature", "Add a new feature to improve user experience", 1
        )
        await connection.execute(
            "INSERT INTO suggestion (title, description, category_id) VALUES ($1, $2, $3)",
            "Bug Fix", "Fix the login bug", 2
        )
        await connection.execute(
            "INSERT INTO suggestion (title, description, category_id) VALUES ($1, $2, $3)",
            "Performance Improvement", "Optimize database queries for faster response", 3
        )

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Start the backend server
uvicorn.run(app, host="0.0.0.0", port=8000)