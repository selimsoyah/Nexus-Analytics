"""
Database Connection Module

Provides centralized database connection functionality for the Nexus Analytics platform.
This module handles PostgreSQL connections and provides a common interface for all API modules.

Author: Nexus Analytics Team
Date: October 2025
"""

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection
import os
import logging

logger = logging.getLogger(__name__)

# Database connection configuration
DB_URL = os.getenv("DATABASE_URL", "postgresql://nexus_user:nexus_pass@localhost:5432/nexus_db")

# Create engine instance
engine = create_engine(DB_URL)


def get_database_connection() -> Connection:
    """
    Get a database connection for executing queries.
    
    Returns:
        Connection: SQLAlchemy database connection
        
    Raises:
        Exception: If database connection fails
    """
    try:
        connection = engine.connect()
        logger.debug("Database connection established successfully")
        return connection
    except Exception as e:
        logger.error(f"Failed to establish database connection: {str(e)}")
        raise


def get_database_engine():
    """
    Get the database engine instance.
    
    Returns:
        Engine: SQLAlchemy database engine
    """
    return engine


def test_connection() -> bool:
    """
    Test the database connection.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        with get_database_connection() as conn:
            result = conn.execute(text("SELECT 1"))
            return result.fetchone()[0] == 1
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        return False


if __name__ == "__main__":
    # Test connection when run directly
    if test_connection():
        print("✅ Database connection successful")
    else:
        print("❌ Database connection failed")