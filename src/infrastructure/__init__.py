"""
Infrastructure layer for external services and resources.
Part of EPIC-003: Production Scalability Improvements
"""

from src.infrastructure.database_adapter import EnhancedDatabase, get_enhanced_database
from src.infrastructure.database_pool import EnhancedConnectionPool, close_pool, get_pool

__all__ = [
    "EnhancedConnectionPool",
    "EnhancedDatabase",
    "close_pool",
    "get_enhanced_database",
    "get_pool",
]
