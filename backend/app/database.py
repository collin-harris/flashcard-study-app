import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Read DATABASE_URL env variable and create SQLAlchemy engine
database_url = os.environ.get("DATABASE_URL")

if not database_url:
    raise ValueError("DATABASE_URL environment variable is not set.")

engine = create_engine(database_url)

# Create a SessionLocal class using sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class using declarative_base()
Base = declarative_base()