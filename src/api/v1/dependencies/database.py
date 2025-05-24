"""
Database dependencies for API endpoints.
"""
from typing import Generator

from patient_generator.database import Database


def get_database() -> Database:
    """
    Get database instance.
    
    Returns:
        Database instance
    """
    return Database()