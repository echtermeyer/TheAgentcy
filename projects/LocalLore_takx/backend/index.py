import asyncpg
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

DATABASE_URL = "postgresql://user:admin@database:5432"

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Story(BaseModel):
    location: str
    theme: str
    content: str

async def connect_to_db():
    return await asyncpg.create_pool(DATABASE_URL)

async def close_db_connection():
    await pool.close()

async def create_tables():
    async with asyncpg.create_pool(DATABASE_URL) as pool:
        async with pool.acquire() as connection:
            await connection.execute(
                """
                CREATE TABLE IF NOT EXISTS stories (
                    story_id SERIAL PRIMARY KEY,
                    location VARCHAR(100),
                    theme VARCHAR(100),
                    content TEXT
                )
                """
            )
            await connection.execute("CREATE INDEX IF NOT EXISTS idx_location ON stories (location)")
            await connection.execute("CREATE INDEX IF NOT EXISTS idx_theme ON stories (theme)")

async def populate_tables():
    async with asyncpg.create_pool(DATABASE_URL) as pool:
        async with pool.acquire() as connection:
            await connection.execute(
                """
                INSERT INTO stories (location, theme, content) VALUES 
                ('New York', 'Adventure', 'A thrilling adventure in the heart of New York'),
                ('Paris', 'Romance', 'A romantic story set in the beautiful city of Paris'),
                ('Tokyo', 'Mystery', 'An intriguing mystery unfolding in the bustling streets of Tokyo')
                """
            )

@app.post("/stories/", response_model=Story)
async def create_story(story: Story):
    async with asyncpg.create_pool(DATABASE_URL) as pool:
        async with pool.acquire() as connection:
            query = "INSERT INTO stories (location, theme, content) VALUES ($1, $2, $3) RETURNING story_id"
            record = await connection.fetchrow(query, story.location, story.theme, story.content)
            return {**story.dict(), "story_id": record["story_id"]}

@app.get("/stories/{story_id}", response_model=Story)
async def read_story(story_id: int):
    async with asyncpg.create_pool(DATABASE_URL) as pool:
        async with pool.acquire() as connection:
            query = "SELECT location, theme, content FROM stories WHERE story_id = $1"
            record = await connection.fetchrow(query, story_id)
            if record is None:
                raise HTTPException(status_code=404, detail="Story not found")
            return Story(**record)

@app.put("/stories/{story_id}", response_model=Story)
async def update_story(story_id: int, story: Story):
    async with asyncpg.create_pool(DATABASE_URL) as pool:
        async with pool.acquire() as connection:
            query = "UPDATE stories SET location = $1, theme = $2, content = $3 WHERE story_id = $4 RETURNING story_id"
            record = await connection.fetchrow(query, story.location, story.theme, story.content, story_id)
            if record is None:
                raise HTTPException(status_code=404, detail="Story not found")
            return {**story.dict(), "story_id": record["story_id"]}

@app.delete("/stories/{story_id}")
async def delete_story(story_id: int):
    async with asyncpg.create_pool(DATABASE_URL) as pool:
        async with pool.acquire() as connection:
            query = "DELETE FROM stories WHERE story_id = $1"
            result = await connection.execute(query, story_id)
            if result == "DELETE 0":
                raise HTTPException(status_code=404, detail="Story not found")

@app.on_event("startup")
async def startup():
    app.state.pool = await connect_to_db()
    await create_tables()
    await populate_tables()

@app.on_event("shutdown")
async def shutdown():
    await close_db_connection()

# Start the backend server
uvicorn.run(app, host="0.0.0.0", port=8000)