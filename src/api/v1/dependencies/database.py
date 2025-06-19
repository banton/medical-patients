"""
Database dependencies for API endpoints.
"""

from src.infrastructure.database_adapter import get_enhanced_database


def get_database():
    """
    Get enhanced database instance.

    Returns:
        Enhanced database instance
    """
    return get_enhanced_database()
