import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Read DATABASE_URL env variable and create SQLAlchemy engine
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set.")

engine = create_engine(DATABASE_URL)

# Create a SessionLocal class using sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class using declarative_base()
Base = declarative_base()
