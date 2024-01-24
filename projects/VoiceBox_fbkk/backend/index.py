import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncpg
from pydantic import BaseModel
import pandas as pd
import numpy as np

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

# Database table creation and data population
@app.on_event("startup")
async def startup():
    # Connect to the database
    conn = await asyncpg.connect(DATABASE_URL)

    # Create table: users
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id SERIAL PRIMARY KEY,
            username VARCHAR(50) NOT NULL,
            email VARCHAR(100) NOT NULL,
            password VARCHAR(100) NOT NULL,
            role VARCHAR(10) NOT NULL
        )
    ''')

    # Create table: suggestion_categories
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS suggestion_categories (
            category_id SERIAL PRIMARY KEY,
            category_name VARCHAR(50) NOT NULL
        )
    ''')

    # Create table: suggestion_submissions
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS suggestion_submissions (
            suggestion_id SERIAL PRIMARY KEY,
            user_id INT NOT NULL,
            category_id INT NOT NULL,
            suggestion_text TEXT NOT NULL,
            submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_anonymous BOOLEAN NOT NULL
        )
    ''')

    # Populate table: users
    await conn.execute('''
        INSERT INTO users (username, email, password, role) VALUES 
        ('john_doe', 'john@example.com', 'password123', 'employee'),
        ('jane_smith', 'jane@example.com', 'pass456', 'manager')
    ''')

    # Populate table: suggestion_categories
    await conn.execute('''
        INSERT INTO suggestion_categories (category_name) VALUES 
        ('Improvement'),
        ('Cost Saving'),
        ('Employee Engagement')
    ''')

    # Populate table: suggestion_submissions
    await conn.execute('''
        INSERT INTO suggestion_submissions (user_id, category_id, suggestion_text, is_anonymous) VALUES 
        (1, 1, 'Improve office lighting for better productivity', FALSE),
        (2, 2, 'Implement paperless billing to reduce costs', FALSE),
        (1, 3, 'Organize team building activities for better engagement', TRUE)
    ''')

    # Close the connection
    await conn.close()

# Pydantic models for JSON payloads
class User(BaseModel):
    username: str
    email: str
    password: str
    role: str

class Category(BaseModel):
    category_name: str

class SuggestionSubmission(BaseModel):
    user_id: int
    category_id: int
    suggestion_text: str
    is_anonymous: bool

# API endpoints
@app.post("/users/")
async def create_user(user: User):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute(
            "INSERT INTO users (username, email, password, role) VALUES ($1, $2, $3, $4)",
            user.username, user.email, user.password, user.role
        )
        return {"message": "User created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        await conn.close()

@app.post("/categories/")
async def create_category(category: Category):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute(
            "INSERT INTO suggestion_categories (category_name) VALUES ($1)",
            category.category_name
        )
        return {"message": "Category created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        await conn.close()

@app.post("/suggestions/")
async def submit_suggestion(suggestion: SuggestionSubmission):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute(
            "INSERT INTO suggestion_submissions (user_id, category_id, suggestion_text, is_anonymous) VALUES ($1, $2, $3, $4)",
            suggestion.user_id, suggestion.category_id, suggestion.suggestion_text, suggestion.is_anonymous
        )
        return {"message": "Suggestion submitted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        await conn.close()

@app.get("/suggestions/")
async def get_suggestions():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        result = await conn.fetch("SELECT * FROM suggestion_submissions")
        suggestions = [dict(row) for row in result]
        return {"suggestions": suggestions}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        await conn.close()

# Start the backend server
uvicorn.run(app, host="0.0.0.0", port=8000)