from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Define FastAPI app
app = FastAPI()

# SQLAlchemy database configuration
DATABASE_URL = "mysql://username:password@localhost/NewsletterDB"  # Replace with your database URL
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define Subscriber model
class Subscriber(Base):
    __tablename__ = "Subscribers"

    SubscriberID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    FirstName = Column(String(255))
    LastName = Column(String(255))
    Email = Column(String(255), unique=True, index=True)
    SignupDate = Column(TIMESTAMP, default=datetime.utcnow)

# Create database tables
Base.metadata.create_all(bind=engine)

# Pydantic model for incoming data
class SubscriberCreate(BaseModel):
    FirstName: str
    LastName: str
    Email: str

# API endpoint for user sign-up
@app.post("/api/signup")
async def signup(subscriber: SubscriberCreate):
    db = SessionLocal()
    db_subscriber = Subscriber(**subscriber.dict())

    # Server-side validation
    if not is_valid_email(db_subscriber.Email):
        raise HTTPException(status_code=400, detail="Invalid email format")

    db.add(db_subscriber)
    db.commit()
    db.refresh(db_subscriber)
    db.close()
    return {"message": "Signup successful"}

# Function to validate email format
def is_valid_email(email: str) -> bool:
    # Add your email validation logic here, e.g., using regex
    # For simplicity, we assume all emails are valid in this example
    return True
