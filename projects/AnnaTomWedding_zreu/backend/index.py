import asyncpg
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

# Database table creation and data insertion on startup
@app.on_event("startup")
async def startup():
    # Connect to the database
    conn = await asyncpg.connect(DATABASE_URL)
    
    # Create RSVP table
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS rsvp (
            id SERIAL PRIMARY KEY,
            guest_name VARCHAR(100) NOT NULL,
            meal_choice VARCHAR(50) NOT NULL
        )
    ''')
    
    # Insert example data
    await conn.execute('''
        INSERT INTO rsvp (guest_name, meal_choice) VALUES 
        ('John Doe', 'Vegetarian'),
        ('Jane Smith', 'Fish'),
        ('Bob Johnson', 'Chicken')
    ''')
    
    # Close the connection
    await conn.close()

# Pydantic model for JSON payload
class RSVP(BaseModel):
    guest_name: str
    meal_choice: str

# Endpoint to handle incoming RSVP form submissions
@app.post("/submit_rsvp")
async def submit_rsvp(rsvp: RSVP):
    try:
        # Connect to the database
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Insert the RSVP data into the database using parameterized query
        await conn.execute('''
            INSERT INTO rsvp (guest_name, meal_choice) VALUES ($1, $2)
        ''', rsvp.guest_name, rsvp.meal_choice)
        
        # Close the connection
        await conn.close()
        
        return {"message": "RSVP submitted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while processing the RSVP")

# Endpoint to retrieve RSVP information
@app.get("/get_rsvp/{rsvp_id}")
async def get_rsvp(rsvp_id: int):
    try:
        # Connect to the database
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Retrieve the RSVP information from the database using parameterized query
        rsvp_info = await conn.fetchrow('''
            SELECT * FROM rsvp WHERE id = $1
        ''', rsvp_id)
        
        # Close the connection
        await conn.close()
        
        if rsvp_info:
            return rsvp_info
        else:
            raise HTTPException(status_code=404, detail="RSVP not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while retrieving the RSVP information")

# Endpoint to delete RSVP information
@app.delete("/delete_rsvp/{rsvp_id}")
async def delete_rsvp(rsvp_id: int):
    try:
        # Connect to the database
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Delete the RSVP information from the database using parameterized query
        result = await conn.execute('''
            DELETE FROM rsvp WHERE id = $1
        ''', rsvp_id)
        
        # Close the connection
        await conn.close()
        
        if result == "DELETE 1":
            return {"message": "RSVP deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="RSVP not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while deleting the RSVP")