# patient_generator/database.py
import sqlite3
import json
import os
import datetime
import threading

class Database:
    """SQLite database for storing job information"""
    
    _instance = None
    _lock = threading.Lock()
    
    @classmethod
    def get_instance(cls, db_path=None):
        """Singleton pattern to ensure only one database connection"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = Database(db_path)
            return cls._instance
    
    def __init__(self, db_path=None):
        """Initialize the database connection"""
        self.db_path = db_path or os.path.join(os.getcwd(), "patient_generator.db")
        self.conn = None
        self.init_db()
    
    def init_db(self):
        """Initialize the database schema if it doesn't exist"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        # Enable JSON serialization/deserialization
        self.conn.row_factory = sqlite3.Row
        
        # Create jobs table if it doesn't exist
        cursor = self.conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            config TEXT NOT NULL,
            created_at TEXT NOT NULL,
            completed_at TEXT,
            summary TEXT,
            progress INTEGER DEFAULT 0,
            progress_details TEXT,
            error TEXT,
            output_files TEXT,
            file_types TEXT,
            total_size INTEGER DEFAULT 0,
            total_size_formatted TEXT
        )
        ''')
        self.conn.commit()
    
    def save_job(self, job_data):
        """Save job data to the database"""
        cursor = self.conn.cursor()
        
        # Convert dictionary values to JSON strings
        config = json.dumps(job_data.get('config', {}))
        summary = json.dumps(job_data.get('summary', {}))
        progress_details = json.dumps(job_data.get('progress_details', {}))
        output_files = json.dumps(job_data.get('output_files', []))
        file_types = json.dumps(job_data.get('file_types', {}))
        
        # Check if job already exists to decide between INSERT and UPDATE
        cursor.execute('SELECT job_id FROM jobs WHERE job_id = ?', (job_data['job_id'],))
        exists = cursor.fetchone() is not None
        
        if exists:
            # Update existing job
            cursor.execute('''
            UPDATE jobs SET
                status = ?,
                config = ?,
                created_at = ?,
                completed_at = ?,
                summary = ?,
                progress = ?,
                progress_details = ?,
                error = ?,
                output_files = ?,
                file_types = ?,
                total_size = ?,
                total_size_formatted = ?
            WHERE job_id = ?
            ''', (
                job_data.get('status'),
                config,
                job_data.get('created_at'),
                job_data.get('completed_at'),
                summary,
                job_data.get('progress', 0),
                progress_details,
                job_data.get('error'),
                output_files,
                file_types,
                job_data.get('total_size', 0),
                job_data.get('total_size_formatted'),
                job_data['job_id']
            ))
        else:
            # Insert new job
            cursor.execute('''
            INSERT INTO jobs (
                job_id, status, config, created_at, completed_at, summary, 
                progress, progress_details, error, output_files, file_types,
                total_size, total_size_formatted
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job_data['job_id'],
                job_data.get('status'),
                config,
                job_data.get('created_at'),
                job_data.get('completed_at'),
                summary,
                job_data.get('progress', 0),
                progress_details,
                job_data.get('error'),
                output_files,
                file_types,
                job_data.get('total_size', 0),
                job_data.get('total_size_formatted')
            ))
        
        self.conn.commit()
    
    def get_job(self, job_id):
        """Get job data from the database"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM jobs WHERE job_id = ?', (job_id,))
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        # Convert row to dictionary
        job_data = dict(row)
        
        # Convert JSON strings back to dictionaries/lists
        job_data['config'] = json.loads(job_data['config'])
        job_data['summary'] = json.loads(job_data['summary'])
        job_data['progress_details'] = json.loads(job_data['progress_details'])
        job_data['output_files'] = json.loads(job_data['output_files'])
        job_data['file_types'] = json.loads(job_data['file_types'])
        
        return job_data
    
    def get_all_jobs(self, limit=50, status=None):
        """Get all jobs from the database with optional filtering"""
        cursor = self.conn.cursor()
        
        if status:
            cursor.execute('SELECT * FROM jobs WHERE status = ? ORDER BY created_at DESC LIMIT ?', (status, limit))
        else:
            cursor.execute('SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?', (limit,))
        
        rows = cursor.fetchall()
        
        # Convert rows to list of dictionaries
        jobs = []
        for row in rows:
            job_data = dict(row)
            
            # Convert JSON strings back to dictionaries/lists
            job_data['config'] = json.loads(job_data['config'])
            job_data['summary'] = json.loads(job_data['summary'])
            job_data['progress_details'] = json.loads(job_data['progress_details'])
            job_data['output_files'] = json.loads(job_data['output_files'])
            job_data['file_types'] = json.loads(job_data['file_types'])
            
            jobs.append(job_data)
        
        return jobs
    
    def delete_job(self, job_id):
        """Delete a job from the database"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM jobs WHERE job_id = ?', (job_id,))
        self.conn.commit()
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
