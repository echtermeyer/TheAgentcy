from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import asyncpg

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TimeSlotCreate(BaseModel):
    slot_date: str
    slot_time: str

class TimeSlotUpdate(BaseModel):
    slot_id: int
    customer_first_name: str
    customer_last_name: str

class TimeSlotDelete(BaseModel):
    slot_id: int

DATABASE_URL = 'postgresql://user:admin@database:5432'

async def create_tables():
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS TimeSlots (
            SlotID SERIAL PRIMARY KEY,
            SlotDate DATE NOT NULL,
            SlotTime TIME NOT NULL,
            CustomerFirstName VARCHAR(255),
            CustomerLastName VARCHAR(255),
            IsBooked BOOLEAN DEFAULT FALSE
        );
    ''')
    await conn.close()

@app.on_event("startup")
async def startup():
    await create_tables()
    # Populate the table with some example data
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute('''
        INSERT INTO TimeSlots (SlotDate, SlotTime) VALUES
        ('2023-01-01', '09:00'),
        ('2023-01-01', '10:00'),
        ('2023-01-01', '11:00');
    ''')
    await conn.close()

@app.post("/timeslots/", response_model=TimeSlotCreate)
async def create_timeslot(timeslot: TimeSlotCreate):
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute('''
        INSERT INTO TimeSlots (SlotDate, SlotTime) VALUES ($1, $2);
    ''', timeslot.slot_date, timeslot.slot_time)
    await conn.close()
    return {"status": "success"}

@app.get("/timeslots/")
async def read_available_timeslots():
    conn = await asyncpg.connect(DATABASE_URL)
    rows = await conn.fetch('''
        SELECT SlotID, SlotDate, SlotTime FROM TimeSlots WHERE IsBooked = FALSE;
    ''')
    await conn.close()
    return rows

@app.put("/timeslots/", response_model=TimeSlotUpdate)
async def update_timeslot(timeslot: TimeSlotUpdate):
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute('''
        UPDATE TimeSlots SET CustomerFirstName = $1, CustomerLastName = $2, IsBooked = TRUE WHERE SlotID = $3 AND IsBooked = FALSE;
    ''', timeslot.customer_first_name, timeslot.customer_last_name, timeslot.slot_id)
    await conn.close()
    return {"status": "success"}

@app.delete("/timeslots/", response_model=TimeSlotDelete)
async def delete_timeslot(timeslot: TimeSlotDelete):
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute('''
        DELETE FROM TimeSlots WHERE SlotID = $1;
    ''', timeslot.slot_id)
    await conn.close()
    return {"status": "success"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)