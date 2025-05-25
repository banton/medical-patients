# patient_generator/database.py
import datetime
import json
import os
import threading
from typing import Any, Dict, List, Literal, Optional, Union, overload
import uuid  # For generating IDs

import psycopg2
import psycopg2.extras  # For DictCursor
import psycopg2.pool

# Import Pydantic models for configuration
from .schemas_config import ConfigurationTemplateCreate, ConfigurationTemplateDB


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
            return

        try:
            db_url = os.environ.get("DATABASE_URL")
            if not db_url:
                # Fallback for local development if DATABASE_URL is not set
                # Ensure these match your local setup if not using Docker env vars for local dev
                print("DATABASE_URL not set, attempting fallback to default local connection string.")
                db_url = "postgresql://medgen_user:medgen_password@localhost:5432/medgen_db"

            Database._pool = psycopg2.pool.SimpleConnectionPool(1, 20, dsn=db_url)
            conn = self.get_connection()
            if conn:
                print("Database connection pool initialized successfully.")
                self.release_connection(conn)
            else:
                print("Failed to initialize database connection pool.")
                Database._pool = None  # Ensure pool is None if init fails
        except (Exception, psycopg2.Error) as error:
            print(f"Error while connecting to PostgreSQL or initializing pool: {error}")
            Database._pool = None  # Ensure pool is None if init fails

    def get_connection(self) -> Optional[psycopg2.extensions.connection]:
        if self._pool is None:  # More direct check
            print("Connection pool is not initialized. Attempting to re-initialize.")
            # Try to re-initialize.
            self.__init__()
            if self._pool is None:  # Check again after attempt
                print("Re-initialization of connection pool failed.")
                return None
        try:
            return self._pool.getconn()
        except Exception as e:
            print(f"Error getting connection from pool: {e}")
            return None

    def release_connection(self, conn: Optional[psycopg2.extensions.connection]):
        if self._pool and conn:
            try:
                self._pool.putconn(conn)
            except Exception as e:
                print(f"Error releasing connection to pool: {e}")

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
        conn = None
        try:
            conn = self.get_connection()
            if not conn:  # conn could be None if get_connection fails
                msg = "Failed to get database connection."
                raise ConnectionError(msg)

            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
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
        except (Exception, psycopg2.Error) as error:
            print(f"Database Error: {error}")
            if conn and commit:  # Check if conn is not None before trying to rollback
                try:
                    conn.rollback()
                except Exception as rb_error:
                    print(f"Rollback failed: {rb_error}")
            raise
        finally:
            if conn:
                self.release_connection(conn)

    # --- Job Methods ---
    def save_job(self, job_data: Dict[str, Any]):
        config_json = json.dumps(job_data.get("config", {}))
        summary_json = json.dumps(job_data.get("summary", {}))
        progress_details_json = json.dumps(job_data.get("progress_details", {}))
        output_files_json = json.dumps(job_data.get("output_files", []))
        file_types_json = json.dumps(job_data.get("file_types", {}))
        job_id = job_data["job_id"]

        check_query = "SELECT job_id FROM jobs WHERE job_id = %s"
        existing_job = self._execute_query(check_query, (job_id,), fetch_one=True)

        if existing_job:
            update_query = """
            UPDATE jobs SET
                status = %s, config = %s, created_at = %s, completed_at = %s,
                summary = %s, progress = %s, progress_details = %s, error = %s,
                output_files = %s, file_types = %s, total_size = %s, total_size_formatted = %s
            WHERE job_id = %s
            """
            params = (
                job_data.get("status"),
                config_json,
                job_data.get("created_at"),
                job_data.get("completed_at"),
                summary_json,
                job_data.get("progress", 0),
                progress_details_json,
                job_data.get("error"),
                output_files_json,
                file_types_json,
                job_data.get("total_size", 0),
                job_data.get("total_size_formatted"),
                job_id,
            )
            self._execute_query(update_query, params, commit=True)
        else:
            insert_query = """
            INSERT INTO jobs (
                job_id, status, config, created_at, completed_at, summary,
                progress, progress_details, error, output_files, file_types,
                total_size, total_size_formatted
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (
                job_id,
                job_data.get("status"),
                config_json,
                job_data.get("created_at"),
                job_data.get("completed_at"),
                summary_json,
                job_data.get("progress", 0),
                progress_details_json,
                job_data.get("error"),
                output_files_json,
                file_types_json,
                job_data.get("total_size", 0),
                job_data.get("total_size_formatted"),
            )
            self._execute_query(insert_query, params, commit=True)

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM jobs WHERE job_id = %s"
        row = self._execute_query(query, (job_id,), fetch_one=True)
        if row is None:
            return None
        job_data = dict(row)
        for field_name, default_value in [
            ("config", {}),
            ("summary", {}),
            ("progress_details", {}),
            ("output_files", []),
            ("file_types", {}),
        ]:
            if job_data.get(field_name) and isinstance(job_data[field_name], str):
                try:
                    job_data[field_name] = json.loads(job_data[field_name])
                except json.JSONDecodeError:
                    job_data[field_name] = default_value
            elif not job_data.get(field_name):  # Handles None or empty string if not already dict/list
                job_data[field_name] = default_value
        return job_data

    def get_all_jobs(self, limit: Optional[int] = 50, status: Optional[str] = None) -> List[Dict[str, Any]]:
        query_parts = ["SELECT * FROM jobs"]
        params_list: List[Any] = []
        conditions = []
        if status:
            conditions.append("status = %s")
            params_list.append(status)
        if conditions:
            query_parts.append("WHERE " + " AND ".join(conditions))
        query_parts.append("ORDER BY created_at DESC")
        if limit is not None and limit > 0:  # Ensure limit is positive
            query_parts.append("LIMIT %s")
            params_list.append(limit)

        final_query = " ".join(query_parts)
        rows = self._execute_query(final_query, tuple(params_list), fetch_all=True)
        jobs = []
        if rows:
            for row_item in rows:  # Changed 'row' to 'row_item' to avoid conflict with outer scope 'row' in get_job
                job_data = dict(row_item)
                for field_name, default_value in [
                    ("config", {}),
                    ("summary", {}),
                    ("progress_details", {}),
                    ("output_files", []),
                    ("file_types", {}),
                ]:
                    if job_data.get(field_name) and isinstance(job_data[field_name], str):
                        try:
                            job_data[field_name] = json.loads(job_data[field_name])
                        except json.JSONDecodeError:
                            job_data[field_name] = default_value
                    elif not job_data.get(field_name):  # Handles None or empty string if not already dict/list
                        job_data[field_name] = default_value
                jobs.append(job_data)
        return jobs

    def delete_job(self, job_id: str):
        query = "DELETE FROM jobs WHERE job_id = %s"
        self._execute_query(query, (job_id,), commit=True)

    def close_pool(self):
        if self._pool:
            try:
                self._pool.closeall()
                print("Database connection pool closed.")
            except Exception as e:
                print(f"Error closing connection pool: {e}")
            Database._pool = None
            Database._instance = None


class ConfigurationRepository:
    """Repository for managing ConfigurationTemplates in PostgreSQL"""

    def __init__(self, db: Database):
        self.db = db

    def _row_to_pydantic(self, row: Optional[psycopg2.extras.DictRow]) -> Optional[ConfigurationTemplateDB]:
        if row is None:
            return None
        # Pydantic model expects Python dicts for JSONB fields after json.loads
        # The DB stores them as JSONB, psycopg2 DictRow might return them as strings or already parsed
        # depending on typecasters. Assuming they need json.loads if they are strings.
        data: Dict[str, Any] = dict(row)  # Ensure data is a mutable dict
        for field in ["front_configs", "facility_configs", "injury_distribution"]:
            if field in data:
                if isinstance(data[field], str):  # Only load if it's a string
                    try:
                        data[field] = json.loads(data[field])
                    except json.JSONDecodeError:
                        # Handle cases where string is not valid JSON, or field is not JSONB in DB
                        print(f"Warning: Could not decode JSON for field {field} in config ID {data.get('id')}")
                        # Assign default based on Pydantic model or expected structure
                        data[field] = [] if field in ["front_configs", "facility_configs"] else {}
                elif data[field] is None:  # Handle if JSONB field is NULL
                    data[field] = [] if field in ["front_configs", "facility_configs"] else {}
            else:  # Field might not be present in row if columns were not selected
                data[field] = [] if field in ["front_configs", "facility_configs"] else {}

        # Ensure datetime objects are timezone-aware if not already (PostgreSQL stores them as UTC)
        # Pydantic V2 with from_attributes=True should handle this if types match.
        # Ensure all required fields for ConfigurationTemplateDB are present in `data`
        # or provide defaults if Pydantic model doesn't have them.
        return ConfigurationTemplateDB(**data)

    def create_configuration(self, config_create: ConfigurationTemplateCreate) -> ConfigurationTemplateDB:
        """Creates a new configuration template."""
        config_id = str(uuid.uuid4())
        now = datetime.datetime.utcnow()

        query = """
        INSERT INTO configuration_templates
            (id, name, description, front_configs, facility_configs, injury_distribution, total_patients, created_at, updated_at, version, parent_config_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING *;
        """
        params = (
            config_id,
            config_create.name,
            config_create.description,
            json.dumps([fc.model_dump() for fc in config_create.front_configs]),
            json.dumps([fc.model_dump() for fc in config_create.facility_configs]),
            json.dumps(config_create.injury_distribution),
            config_create.total_patients,
            now,
            now,
            config_create.version,
            config_create.parent_config_id,  # Corrected attribute name
        )
        # _execute_query with fetch_one=True returns Optional[DictRow]
        db_row = self.db._execute_query(query, params, fetch_one=True, commit=True)

        if db_row is None:
            msg = "Failed to create configuration template, no data returned from DB."
            raise Exception(msg)

        pydantic_obj = self._row_to_pydantic(db_row)
        if pydantic_obj is None:  # Should not happen if db_row is not None and _row_to_pydantic is robust
            msg = "Failed to convert DB row to Pydantic model after creation."
            raise Exception(msg)
        return pydantic_obj

    def get_configuration(self, config_id: str) -> Optional[ConfigurationTemplateDB]:
        """Retrieves a configuration template by its ID."""
        query = "SELECT * FROM configuration_templates WHERE id = %s;"
        # _execute_query with fetch_one=True returns Optional[DictRow]
        db_row = self.db._execute_query(query, (config_id,), fetch_one=True)
        if db_row is None:
            return None
        return self._row_to_pydantic(db_row)

    def list_configurations(self, skip: int = 0, limit: int = 100) -> List[ConfigurationTemplateDB]:
        """Lists all configuration templates with pagination."""
        query = "SELECT * FROM configuration_templates ORDER BY name OFFSET %s LIMIT %s;"
        # _execute_query with fetch_all=True returns List[DictRow]
        db_rows: List[psycopg2.extras.DictRow] = self.db._execute_query(query, (skip, limit), fetch_all=True)

        configurations: List[ConfigurationTemplateDB] = []
        if db_rows:  # db_rows is a list, could be empty
            for db_row_item in db_rows:
                pydantic_obj = self._row_to_pydantic(db_row_item)
                if pydantic_obj is not None:
                    configurations.append(pydantic_obj)
        return configurations

    def update_configuration(
        self, config_id: str, config_update: ConfigurationTemplateCreate
    ) -> Optional[ConfigurationTemplateDB]:
        """Updates an existing configuration template."""
        now = datetime.datetime.utcnow()
        # Assuming version and parent_id might also be updatable or handled by model
        query = """
        UPDATE configuration_templates SET
            name = %s,
            description = %s,
            front_configs = %s,
            facility_configs = %s,
            injury_distribution = %s,
            total_patients = %s,
            updated_at = %s,
            version = %s,
            parent_config_id = %s
        WHERE id = %s
        RETURNING *;
        """
        params = (
            config_update.name,
            config_update.description,
            json.dumps([fc.model_dump() for fc in config_update.front_configs]),
            json.dumps([fc.model_dump() for fc in config_update.facility_configs]),
            json.dumps(config_update.injury_distribution),
            config_update.total_patients,
            now,
            config_update.version,
            config_update.parent_config_id,  # Corrected attribute name
            config_id,
        )
        # _execute_query with fetch_one=True returns Optional[DictRow]
        db_row = self.db._execute_query(query, params, fetch_one=True, commit=True)
        if db_row is None:
            return None
        return self._row_to_pydantic(db_row)

    def delete_configuration(self, config_id: str) -> bool:
        """Deletes a configuration template by its ID. Returns True if deleted."""
        query = "DELETE FROM configuration_templates WHERE id = %s RETURNING id;"
        deleted_row = self.db._execute_query(query, (config_id,), fetch_one=True, commit=True)
        return deleted_row is not None


# Example of how to get the database instance and repository:
# db_instance = Database.get_instance()
# config_repo = ConfigurationRepository(db_instance)
# At application shutdown, you might want to call:
# db_instance.close_pool()
