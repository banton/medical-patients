"""
Database-backed implementation of job repository.
"""

from dataclasses import asdict
from datetime import datetime
import json
from typing import Any, Dict, List

import psycopg2
from psycopg2.extras import RealDictCursor

from src.core.exceptions import JobNotFoundError
from src.domain.models.job import Job, JobProgressDetails, JobStatus
from src.domain.repositories.job_repository import JobRepositoryInterface
from src.infrastructure.database_pool import EnhancedConnectionPool


class DatabaseJobRepository(JobRepositoryInterface):
    """Database-backed implementation of job repository."""

    def __init__(self, db_pool: EnhancedConnectionPool):
        self.db_pool = db_pool

    async def create(self, config: Dict[str, Any]) -> Job:
        """Create a new job in the database."""
        job = Job(
            status=JobStatus.PENDING,
            created_at=datetime.utcnow(),
            config=config,
            job_id=None,  # Will be auto-generated in __post_init__
            progress=0,
        )

        query = """
            INSERT INTO jobs (
                job_id, status, config, created_at, progress
            ) VALUES (
                %s, %s, %s, %s, %s
            )
        """

        params = (job.job_id, job.status.value, json.dumps(config), job.created_at, job.progress)

        try:
            with self.db_pool.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                conn.commit()
        except psycopg2.IntegrityError as e:
            # Job ID already exists
            error_msg = f"Job with ID {job.job_id} already exists"
            raise ValueError(error_msg) from e

        return job

    async def get(self, job_id: str) -> Job:
        """Get a job by ID from the database."""
        query = """
            SELECT job_id, status, config, created_at, completed_at,
                   summary, progress, progress_details, error, output_files
            FROM jobs
            WHERE job_id = %s
        """

        with self.db_pool.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (job_id,))
                result = cursor.fetchone()

            if not result:
                error_msg = f"Job {job_id} not found"
                raise JobNotFoundError(error_msg)

            # Convert row to Job object
            job = Job(
                job_id=result["job_id"],
                status=JobStatus(result["status"]),
                created_at=result["created_at"],
                config=result["config"] if isinstance(result["config"], dict) else json.loads(result["config"]),
                progress=result["progress"] or 0,
            )

            # Set optional fields
            if result["completed_at"]:
                job.completed_at = result["completed_at"]
            if result["error"]:
                job.error = result["error"]
            if result["summary"]:
                job.summary = (
                    result["summary"] if isinstance(result["summary"], dict) else json.loads(result["summary"])
                )
            if result["progress_details"]:
                details = (
                    result["progress_details"]
                    if isinstance(result["progress_details"], dict)
                    else json.loads(result["progress_details"])
                )
                job.progress_details = JobProgressDetails(**details)
            if result["output_files"]:
                files_data = (
                    result["output_files"]
                    if isinstance(result["output_files"], list)
                    else json.loads(result["output_files"])
                )
                job.output_files = files_data
                job.result_files = files_data  # Set both for compatibility

            return job

    async def update(self, job: Job) -> None:
        """Update a job in the database."""
        query = """
            UPDATE jobs
            SET status = %s,
                progress = %s,
                progress_details = %s,
                error = %s,
                completed_at = %s,
                summary = %s,
                output_files = %s
            WHERE job_id = %s
        """

        # Handle both output_files and result_files for backwards compatibility
        output_files_data = job.output_files or job.result_files or []

        params = (
            job.status.value,
            job.progress,
            json.dumps(asdict(job.progress_details)) if job.progress_details else None,
            job.error,
            job.completed_at,
            json.dumps(job.summary) if job.summary else None,
            json.dumps(output_files_data) if output_files_data else None,
            job.job_id,
        )

        with self.db_pool.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                if cursor.rowcount == 0:
                    error_msg = f"Job {job.job_id} not found"
                    raise JobNotFoundError(error_msg)
            conn.commit()

    async def list_all(self) -> List[Job]:
        """List all jobs from the database."""
        query = """
            SELECT job_id, status, config, created_at, completed_at,
                   summary, progress, progress_details, error, output_files
            FROM jobs
            ORDER BY created_at DESC
            LIMIT 100
        """

        jobs = []
        with self.db_pool.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query)
                results = cursor.fetchall()

            for result in results:
                job = Job(
                    job_id=result["job_id"],
                    status=JobStatus(result["status"]),
                    created_at=result["created_at"],
                    config=result["config"] if isinstance(result["config"], dict) else json.loads(result["config"]),
                    progress=result["progress"] or 0,
                )

                # Set optional fields
                if result["completed_at"]:
                    job.completed_at = result["completed_at"]
                if result["error"]:
                    job.error = result["error"]
                if result["summary"]:
                    job.summary = (
                        result["summary"] if isinstance(result["summary"], dict) else json.loads(result["summary"])
                    )
                if result["progress_details"]:
                    details = (
                        result["progress_details"]
                        if isinstance(result["progress_details"], dict)
                        else json.loads(result["progress_details"])
                    )
                    job.progress_details = JobProgressDetails(**details)
                if result["output_files"]:
                    files_data = (
                        result["output_files"]
                        if isinstance(result["output_files"], list)
                        else json.loads(result["output_files"])
                    )
                    job.output_files = files_data
                    job.result_files = files_data  # Set both for compatibility

                jobs.append(job)

        return jobs

    async def delete(self, job_id: str) -> None:
        """Delete a job from the database."""
        query = "DELETE FROM jobs WHERE job_id = %s"

        with self.db_pool.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (job_id,))
                if cursor.rowcount == 0:
                    error_msg = f"Job {job_id} not found"
                    raise JobNotFoundError(error_msg)
            conn.commit()

    async def cleanup_old_jobs(self, days: int = 7) -> int:
        """Clean up jobs older than specified days."""
        query = """
            DELETE FROM jobs
            WHERE created_at < NOW() - INTERVAL '%s days'
            AND status IN ('completed', 'failed', 'cancelled')
        """

        with self.db_pool.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (days,))
                deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count
