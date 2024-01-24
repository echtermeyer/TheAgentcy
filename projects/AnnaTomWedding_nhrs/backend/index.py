import uvicorn
import asyncpg
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime

app = FastAPI()

# Database Connection
DATABASE_URL = "postgresql://user:admin@database:5432"

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Table Creation and Population
@app.on_event("startup")
async def startup():
    connection = await asyncpg.connect(DATABASE_URL)
    await connection.execute('''
        CREATE TABLE IF NOT EXISTS RSVP (
            id SERIAL PRIMARY KEY,
            guest_name VARCHAR(100) NOT NULL,
            meal_choice VARCHAR(100) NOT NULL,
            submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    await connection.execute('''
        CREATE TABLE IF NOT EXISTS RSVP_Log (
            id SERIAL PRIMARY KEY,
            event_type VARCHAR(100) NOT NULL,
            event_description TEXT,
            event_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    await connection.execute('''
        CREATE OR REPLACE FUNCTION process_rsvp(p_guest_name VARCHAR(100), p_meal_choice VARCHAR(100)) RETURNS VOID AS $$
        BEGIN
            IF p_guest_name = '' OR p_meal_choice = '' THEN
                RAISE EXCEPTION 'Guest name and meal choice cannot be empty';
            END IF;
            INSERT INTO RSVP (guest_name, meal_choice) VALUES (p_guest_name, p_meal_choice);
        END;
        $$ LANGUAGE plpgsql;
    ''')
    await connection.execute('''
        CREATE OR REPLACE FUNCTION rsvp_submission_trigger_function() RETURNS TRIGGER AS $$
        BEGIN
            INSERT INTO RSVP_Log (event_type, event_description) VALUES ('RSVP Submission', 'New RSVP submitted');
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    ''')
    await connection.execute('''
        CREATE TRIGGER rsvp_submission_trigger
        AFTER INSERT ON RSVP
        FOR EACH ROW
        EXECUTE FUNCTION rsvp_submission_trigger_function();
    ''')
    await connection.close()

# Pydantic Models
class RSVP(BaseModel):
    guest_name: str
    meal_choice: str

# API Endpoints
@app.post("/submit_rsvp/")
async def submit_rsvp(rsvp: RSVP):
    try:
        connection = await asyncpg.connect(DATABASE_URL)
        await connection.execute('SELECT process_rsvp($1, $2)', rsvp.guest_name, rsvp.meal_choice)
        await connection.close()
        return {"message": "RSVP submitted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_rsvps/")
async def get_rsvps():
    try:
        connection = await asyncpg.connect(DATABASE_URL)
        rsvps = await connection.fetch('SELECT * FROM RSVP')
        await connection.close()
        return rsvps
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_rsvp_log/")
async def get_rsvp_log():
    try:
        connection = await asyncpg.connect(DATABASE_URL)
        log = await connection.fetch('SELECT * FROM RSVP_Log')
        await connection.close()
        return log
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Start the backend server
uvicorn.run(app, host="0.0.0.0", port=8000)