"""
Database dependencies for API endpoints.
"""

from patient_generator.database import Database


def get_database() -> Database:
    """
    Get database instance.

    Returns:
        Database instance
    """
    return Database()
