
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncpg
from pydantic import BaseModel

app = FastAPI()

# Database connection string
DB_CONNECTION_STRING = "postgresql://user:admin@database:5432"

# Add CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


class Item(BaseModel):
    name: str


async def get_db_connection():
    return await asyncpg.connect(DB_CONNECTION_STRING)

@app.on_event("startup")
async def startup():
    # Create database table on startup
    conn = await get_db_connection()
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL
        )
    ''')

    # Insert sample data
    sample_items = ['Item 1', 'Item 2', 'Item 3']
    for item in sample_items:
        await conn.execute('''
            INSERT INTO items (name) VALUES ($1)
        ''', item)

    await conn.close()

@app.post("/add_item/")
async def add_item(item: Item):
    conn = await get_db_connection()
    result = await conn.execute('''
        INSERT INTO items(name) VALUES($1) RETURNING id
    ''', item.name)
    await conn.close()
    return {"id": result}

@app.get("/get_items/")
async def get_items():
    conn = await get_db_connection()
    items = await conn.fetch('SELECT * FROM items')
    await conn.close()
    return {"items": items}

@app.delete("/delete_item/{item_id}")
async def delete_item(item_id: int):
    conn = await get_db_connection()
    await conn.execute('''
        DELETE FROM items WHERE id = $1
    ''', item_id)
    await conn.close()
    return {"message": "Item deleted"}

@app.get("/test")
async def read_root():
    await delete_item(1)
    return {"message": "Backend running!"}

# Start the web server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
