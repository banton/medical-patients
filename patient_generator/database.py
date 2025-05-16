# patient_generator/database.py
import psycopg2
import psycopg2.pool
import psycopg2.extras # For DictCursor
import json
import os
import datetime
import threading
from typing import Optional, List, Dict, Any, Union

class Database:
    """PostgreSQL database for storing job information and configurations"""

    _instance = None
    _lock = threading.Lock()
    _pool: Optional[psycopg2.pool.SimpleConnectionPool] = None

    @classmethod
    def get_instance(cls):
        """Singleton pattern to ensure only one database connection pool"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = Database()
            return cls._instance

    def __init__(self):
        """Initialize the database connection pool"""
        if Database._pool is not None:
            # This can happen if __init__ is called directly after get_instance created it
            return

        try:
            db_url = os.environ.get("DATABASE_URL")
            if not db_url:
                raise ValueError("DATABASE_URL environment variable not set.")
            
            # minconn=1, maxconn=10 (adjust as needed)
            Database._pool = psycopg2.pool.SimpleConnectionPool(1, 20, dsn=db_url)
            # Test connection
            conn = self.get_connection()
            if conn:
                print("Database connection pool initialized successfully.")
                self.release_connection(conn)
            else:
                print("Failed to initialize database connection pool.")
                Database._pool = None # Ensure pool is None if connection failed
        except (Exception, psycopg2.Error) as error:
            print(f"Error while connecting to PostgreSQL or initializing pool: {error}")
            Database._pool = None # Ensure pool is None if connection failed
            # Depending on application requirements, you might want to raise this error
            # or handle it in a way that allows the app to run in a degraded mode or exit.

    def get_connection(self) -> Optional[psycopg2.extensions.connection]:
        """Get a connection from the pool"""
        if not self._pool:
            print("Connection pool is not initialized.")
            # Attempt to re-initialize, could be a transient issue or first-time setup
            # self.__init__() # Be careful with re-entrancy if called from constructor
            # if not self._pool: # Check again
            return None
        try:
            return self._pool.getconn()
        except Exception as e:
            print(f"Error getting connection from pool: {e}")
            return None

    def release_connection(self, conn: Optional[psycopg2.extensions.connection]):
        """Release a connection back to the pool"""
        if self._pool and conn:
            try:
                self._pool.putconn(conn)
            except Exception as e:
                print(f"Error releasing connection to pool: {e}")

    # init_db is removed as schema is managed by Alembic.
    # The jobs table (and others) will be created by running Alembic migrations.

    def _execute_query(self, query: str, params: Union[tuple, Dict[str, Any]] = None, fetch_one: bool = False, fetch_all: bool = False, commit: bool = False):
        """Helper function to execute queries"""
        conn = None
        try:
            conn = self.get_connection()
            if not conn:
                raise ConnectionError("Failed to get database connection.")
            
            # Use DictCursor to get results as dictionaries
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(query, params)
                
                if commit:
                    conn.commit()
                
                if fetch_one:
                    return cur.fetchone()
                if fetch_all:
                    return cur.fetchall()
                return None # For INSERT/UPDATE/DELETE without returning rows
        except (Exception, psycopg2.Error) as error:
            # In a real app, you'd want more sophisticated logging/error handling
            print(f"Database Error: {error}")
            # Rollback in case of error during a transaction that was meant to be committed
            if conn and commit:
                try:
                    conn.rollback()
                except Exception as rb_error:
                    print(f"Rollback failed: {rb_error}")
            # Re-raise or handle as appropriate for your application
            raise
        finally:
            if conn:
                self.release_connection(conn)

    def save_job(self, job_data: Dict[str, Any]):
        """Save job data to the database (INSERT or UPDATE)"""
        # Convert dictionary/list values to JSON strings for storage
        # This matches the previous SQLite structure. For new tables/PostgreSQL JSONB,
        # psycopg2 can handle dicts directly.
        config_json = json.dumps(job_data.get('config', {}))
        summary_json = json.dumps(job_data.get('summary', {}))
        progress_details_json = json.dumps(job_data.get('progress_details', {}))
        output_files_json = json.dumps(job_data.get('output_files', []))
        file_types_json = json.dumps(job_data.get('file_types', {}))

        job_id = job_data['job_id']
        
        # Check if job exists
        # Note: For PostgreSQL, column names are case-sensitive if quoted during creation,
        # but typically lowercased if not. Assuming standard SQL lowercasing.
        check_query = "SELECT job_id FROM jobs WHERE job_id = %s"
        existing_job = self._execute_query(check_query, (job_id,), fetch_one=True)

        if existing_job:
            # Update existing job
            update_query = """
            UPDATE jobs SET
                status = %s, config = %s, created_at = %s, completed_at = %s,
                summary = %s, progress = %s, progress_details = %s, error = %s,
                output_files = %s, file_types = %s, total_size = %s, total_size_formatted = %s
            WHERE job_id = %s
            """
            params = (
                job_data.get('status'), config_json, job_data.get('created_at'),
                job_data.get('completed_at'), summary_json, job_data.get('progress', 0),
                progress_details_json, job_data.get('error'), output_files_json,
                file_types_json, job_data.get('total_size', 0),
                job_data.get('total_size_formatted'), job_id
            )
            self._execute_query(update_query, params, commit=True)
        else:
            # Insert new job
            insert_query = """
            INSERT INTO jobs (
                job_id, status, config, created_at, completed_at, summary,
                progress, progress_details, error, output_files, file_types,
                total_size, total_size_formatted
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (
                job_id, job_data.get('status'), config_json, job_data.get('created_at'),
                job_data.get('completed_at'), summary_json, job_data.get('progress', 0),
                progress_details_json, job_data.get('error'), output_files_json,
                file_types_json, job_data.get('total_size', 0),
                job_data.get('total_size_formatted')
            )
            self._execute_query(insert_query, params, commit=True)

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job data from the database"""
        query = "SELECT * FROM jobs WHERE job_id = %s"
        row = self._execute_query(query, (job_id,), fetch_one=True)

        if row is None:
            return None

        job_data = dict(row) # Convert DictRow to dict
        
        # Convert JSON strings back to Python objects
        job_data['config'] = json.loads(job_data['config']) if job_data.get('config') else {}
        job_data['summary'] = json.loads(job_data['summary']) if job_data.get('summary') else {}
        job_data['progress_details'] = json.loads(job_data['progress_details']) if job_data.get('progress_details') else {}
        job_data['output_files'] = json.loads(job_data['output_files']) if job_data.get('output_files') else []
        job_data['file_types'] = json.loads(job_data['file_types']) if job_data.get('file_types') else {}
        
        return job_data

    def get_all_jobs(self, limit: Optional[int] = 50, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all jobs from the database with optional filtering and limit"""
        query_parts = ["SELECT * FROM jobs"]
        params = []
        
        conditions = []
        if status:
            conditions.append("status = %s")
            params.append(status)
        
        if conditions:
            query_parts.append("WHERE " + " AND ".join(conditions))
            
        query_parts.append("ORDER BY created_at DESC")
        
        if limit is not None and limit > 0:
            query_parts.append("LIMIT %s")
            params.append(limit)
            
        final_query = " ".join(query_parts)
        rows = self._execute_query(final_query, tuple(params), fetch_all=True)
        
        jobs = []
        if rows:
            for row in rows:
                job_data = dict(row) # Convert DictRow to dict
                job_data['config'] = json.loads(job_data['config']) if job_data.get('config') else {}
                job_data['summary'] = json.loads(job_data['summary']) if job_data.get('summary') else {}
                job_data['progress_details'] = json.loads(job_data['progress_details']) if job_data.get('progress_details') else {}
                job_data['output_files'] = json.loads(job_data['output_files']) if job_data.get('output_files') else []
                job_data['file_types'] = json.loads(job_data['file_types']) if job_data.get('file_types') else {}
                jobs.append(job_data)
        
        return jobs

    def delete_job(self, job_id: str):
        """Delete a job from the database"""
        query = "DELETE FROM jobs WHERE job_id = %s"
        self._execute_query(query, (job_id,), commit=True)

    def close_pool(self):
        """Close all connections in the pool"""
        if self._pool:
            try:
                self._pool.closeall()
                print("Database connection pool closed.")
            except Exception as e:
                print(f"Error closing connection pool: {e}")
            Database._pool = None
            Database._instance = None # Reset instance so it can be re-created

# Example of how to get the database instance:
# db_instance = Database.get_instance()
# At application shutdown, you might want to call:
# db_instance.close_pool()
