import os
import logging
from sqlalchemy import Column, String, Float, DateTime, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.pool import NullPool
from datetime import datetime
import asyncio
import psycopg2 # Required by psycopg2 dialect for both synchronous DDL and runtime

from .config.settings import Settings

logger = logging.getLogger(__name__)

# --- Database Configuration ---
# Create settings instance for proper access
_settings = Settings()
DB_USER = _settings.DB_USER or os.getenv("DB_USER") or "priv_user"
DB_PASS = _settings.DB_PASS or os.getenv("DB_PASS") or "priv_password"
DB_NAME = _settings.DB_NAME or os.getenv("DB_NAME") or "priv_db"
INSTANCE_CONNECTION_NAME = _settings.CLOUD_SQL_INSTANCE_CONNECTION_NAME or os.getenv("CLOUD_SQL_INSTANCE_CONNECTION_NAME") # Crucial for Cloud SQL Auth Proxy
# PUBLIC_IP_ADDRESS is no longer used for connection when using proxy
# PUBLIC_IP_ADDRESS = settings.PUBLIC_IP_ADDRESS 

# --- SQLAlchemy Setup ---
Base = declarative_base()

class Agent(Base):
    """SQLAlchemy model for the 'agents' table."""
    __tablename__ = 'agents'
    agent_id = Column(String, primary_key=True, index=True, nullable=False)
    role = Column(String, nullable=False)
    reputation_score = Column(Float, default=0.5, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Agent(agent_id='{self.agent_id}', role='{self.role}', reputation_score={self.reputation_score:.2f})>"


class Vote(Base):
    """SQLAlchemy model for recorded arbitration votes."""
    __tablename__ = 'votes'
    vote_id = Column(String, primary_key=True, index=True, nullable=False)
    agent_id = Column(String, nullable=False, index=True)
    proposal_id = Column(String, nullable=False, index=True)
    vote = Column(String, nullable=False)  # BUY/SELL/HOLD/ABSTAIN
    confidence = Column(Float, default=0.0)
    reasoning = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Vote(vote_id='{self.vote_id}', agent_id='{self.agent_id}', proposal_id='{self.proposal_id}', vote={self.vote})>"

# --- SYNCHRONOUS ENGINE FOR BOTH APPLICATION RUNTIME AND DDL ---
def get_db_engine():
    """
    Initializes a synchronous connection pool for the database.

    Local/dev behavior: when running in DEMO_MODE or no Cloud SQL instance name is set,
    fall back to a local SQLite database (file-based) to avoid connection errors.
    Production behavior: when a Cloud SQL instance name is provided and DEMO_MODE is False,
    attempt to connect via Cloud SQL Auth Proxy using the Unix socket.
    """
    try:
        # If we're running in local demo mode or no Cloud SQL instance name is present, use SQLite
        if _settings.DEMO_MODE or not INSTANCE_CONNECTION_NAME:
            sqlite_path = os.getenv("PRIV_LOCAL_DB_PATH", "priv_demo.db")
            database_url = f"sqlite:///{sqlite_path}"
            engine = create_engine(
                database_url,
                connect_args={"check_same_thread": False},
                echo=False
            )
            logger.warning("Running in DEMO_MODE or missing Cloud SQL instance; falling back to local SQLite DB at %s", sqlite_path)
            return engine

        # Otherwise, attempt to connect to Cloud SQL via Unix socket
        database_url = (
            f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@/{DB_NAME}?"
            f"host=/cloudsql/{INSTANCE_CONNECTION_NAME}"
        )

        engine = create_engine(
            database_url,
            poolclass=NullPool, # Recommended for serverless environments and GKE
            echo=False # Set to True for verbose SQL logging
        )
        logger.info("Successfully created synchronous database connection pool (Cloud SQL Auth Proxy via Unix socket).")
        return engine
    except Exception as e:
        logger.critical(f"Failed to create database connection pool: {e}", exc_info=True)
        raise

# Create the single synchronous database engine
engine = get_db_engine()

# Create a configured "Session" class for synchronous operations
# This will be used by AgentReputationLedger and other parts of your app
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# MODIFIED: create_tables is now a synchronous function (already was)
def create_tables():
    """Creates all database tables defined in the Base metadata synchronously."""
    try:
        logger.info("Attempting to create database tables if they don't exist using synchronous engine...")
        Base.metadata.create_all(bind=engine) # Use the single 'engine'
        logger.info("Tables created successfully (or already exist).\n")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}", exc_info=True)
    finally:
        # No need to dispose engine here, as it's a global singleton for the app
        pass

# Dependency for FastAPI to get a synchronous database session
# This will be used with asyncio.to_thread in FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# This block allows you to run this file directly to create tables
if __name__ == "__main__":
    print("Attempting to create database tables...")
    # Call the synchronous table creation function directly
    create_tables()
    print("Database setup script finished.")

# Alias for get_db for compatibility
get_db_session = get_db
