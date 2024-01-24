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

# Database table creation and data population on startup
async def startup():
    # Connect to the database
    conn = await asyncpg.connect(DATABASE_URL)
    
    # Create EmployeeSuggestions table
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS EmployeeSuggestions (
            suggestion_id SERIAL PRIMARY KEY,
            suggestion_content TEXT,
            category VARCHAR(50),
            timestamp TIMESTAMP,
            anonymous_submission BOOLEAN
        )
    ''')
    
    # Create indexes
    await conn.execute('''
        CREATE INDEX IF NOT EXISTS idx_category ON EmployeeSuggestions (category)
    ''')
    await conn.execute('''
        CREATE INDEX IF NOT EXISTS idx_timestamp ON EmployeeSuggestions (timestamp)
    ''')
    
    # Insert example data
    await conn.execute('''
        INSERT INTO EmployeeSuggestions (suggestion_content, category, timestamp, anonymous_submission)
        VALUES 
            ($1, $2, $3, $4),
            ($5, $6, $7, $8)
    ''', 
    'Improve office recycling program', 'Environment', datetime.strptime('2022-01-15 10:00:00', '%Y-%m-%d %H:%M:%S'), False,
    'Implement flexible work hours', 'Workplace', datetime.strptime('2022-01-16 11:30:00', '%Y-%m-%d %H:%M:%S'), True)
    
    # Close the connection
    await conn.close()

# Add startup event handler
app.add_event_handler("startup", startup)

# Pydantic model for suggestion submission
class SuggestionSubmission(BaseModel):
    suggestion_content: str
    category: str
    anonymous_submission: bool

# API endpoint for submitting a suggestion
@app.post("/submit_suggestion")
async def submit_suggestion(suggestion: SuggestionSubmission):
    conn = await asyncpg.connect(DATABASE_URL)
    timestamp = datetime.now()
    await conn.execute('''
        INSERT INTO EmployeeSuggestions (suggestion_content, category, timestamp, anonymous_submission)
        VALUES ($1, $2, $3, $4)
    ''', suggestion.suggestion_content, suggestion.category, timestamp, suggestion.anonymous_submission)
    await conn.close()
    return {"message": "Suggestion submitted successfully"}

# API endpoint for retrieving categorized suggestions
@app.get("/get_categorized_suggestions/{category}")
async def get_categorized_suggestions(category: str):
    conn = await asyncpg.connect(DATABASE_URL)
    suggestions = await conn.fetch('''
        SELECT * FROM EmployeeSuggestions
        WHERE category = $1
    ''', category)
    await conn.close()
    return suggestions

# API endpoint for searching specific suggestions
@app.get("/search_suggestions/{keyword}")
async def search_suggestions(keyword: str):
    conn = await asyncpg.connect(DATABASE_URL)
    suggestions = await conn.fetch('''
        SELECT * FROM EmployeeSuggestions
        WHERE suggestion_content ILIKE $1
    ''', f'%{keyword}%')
    await conn.close()
    return suggestions

# Start the backend server
uvicorn.run(app, host="0.0.0.0", port=8000)