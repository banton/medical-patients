"""
Database adapter to integrate enhanced connection pool with existing code.
Part of EPIC-003: Production Scalability Improvements
"""

import threading
from typing import Any, Dict, List, Literal, Optional, Union, overload

import psycopg2
import psycopg2.extras

from patient_generator.database import Database as LegacyDatabase
from src.infrastructure.database_pool import get_pool


class EnhancedDatabase(LegacyDatabase):
    """
    Enhanced database class that uses the new connection pool.

    This adapter maintains backward compatibility with existing code
    while using the enhanced connection pool for better scalability.
    """

    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls):
        """Singleton pattern to ensure only one database instance."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = EnhancedDatabase()
            return cls._instance

    def __init__(self):
        """Initialize with enhanced connection pool."""
        # Skip parent __init__ to avoid creating the old pool
        self._pool: Any = get_pool()

    def get_connection(self) -> Optional[psycopg2.extensions.connection]:
        """
        Get connection from enhanced pool.

        Note: This returns a context manager, not a raw connection.
        The calling code should be updated to use it properly.
        """
        # This is a compatibility shim - the enhanced pool uses context managers
        # We'll need to update calling code to use the new pattern
        return self._pool.get_connection()

    def release_connection(self, conn: Optional[psycopg2.extensions.connection]):
        """
        Release connection back to pool.

        Note: With the enhanced pool, connections are automatically
        released when the context manager exits.
        """
        # No-op for compatibility - enhanced pool handles this automatically

    @overload
    def _execute_query(
        self,
        query: str,
        params: Optional[Union[tuple, Dict[str, Any]]] = None,
        *,
        fetch_one: Literal[True],
        fetch_all: Literal[False] = False,
        commit: bool = False,
    ) -> Optional[psycopg2.extras.DictRow]: ...

    @overload
    def _execute_query(
        self,
        query: str,
        params: Optional[Union[tuple, Dict[str, Any]]] = None,
        *,
        fetch_one: Literal[False] = False,
        fetch_all: Literal[True],
        commit: bool = False,
    ) -> List[psycopg2.extras.DictRow]: ...

    @overload
    def _execute_query(
        self,
        query: str,
        params: Optional[Union[tuple, Dict[str, Any]]] = None,
        *,
        fetch_one: Literal[False] = False,
        fetch_all: Literal[False] = False,
        commit: bool = False,
    ) -> None: ...

    def _execute_query(
        self,
        query: str,
        params: Optional[Union[tuple, Dict[str, Any]]] = None,
        *,
        fetch_one: bool = False,
        fetch_all: bool = False,
        commit: bool = False,
    ):
        """Execute query using enhanced connection pool."""
        try:
            with self._pool.get_connection() as conn, conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                if params is not None:
                    cur.execute(query, params)
                else:
                    cur.execute(query)

                if commit:
                    conn.commit()

                if fetch_one:
                    return cur.fetchone()
                if fetch_all:
                    return cur.fetchall()
                return None

        except Exception as error:
            print(f"Database Error: {error}")
            raise

    def close_pool(self):
        """Close the enhanced connection pool."""
        # Enhanced pool is managed globally, don't close it here

    def get_pool_status(self) -> Dict[str, Any]:
        """Get connection pool status and metrics."""
        return self._pool.get_pool_status()


def get_enhanced_database() -> EnhancedDatabase:
    """Get enhanced database instance for dependency injection."""
    return EnhancedDatabase.get_instance()
