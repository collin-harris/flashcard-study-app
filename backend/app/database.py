import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Read DATABASE_URL env variable and create SQLAlchemy engine
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set.")

# pool_pre_ping checks a pooled connection is still alive before handing it
# out, transparently reconnecting if Neon has suspended the database since
# the connection was opened. pool_recycle proactively retires connections
# older than 300 seconds, shrinking the window where one could go stale.
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)

# Create a SessionLocal class using sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class using declarative_base()
Base = declarative_base()
