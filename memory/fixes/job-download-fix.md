# Job Download Fix - Output Files Not Found

## Issue
When trying to download completed jobs, users got error:
```
Download failed: Storage error: Output directory not found for job {job_id}
```

Even though jobs showed as completed with 100% progress, the output_files were empty in the database.

## Root Causes
1. **Field name mismatch**: Job model had both `result_files` and `output_files` fields
   - Job service was setting `result_files`
   - Database repository was expecting `output_files`
   - Result: output files were never persisted to database

2. **Missing output_directory**: The jobs table doesn't have an output_directory column
   - Job service expected this field for downloads
   - Directory path was never stored in database

## Solutions Implemented

### 1. Fixed Field Mismatch
Updated `DatabaseJobRepository` to handle both fields:
```python
# In update method
output_files_data = job.output_files or job.result_files or []

# In get/list methods
job.output_files = files_data
job.result_files = files_data  # Set both for compatibility
```

### 2. Reconstruct Output Directory
Updated `JobService.create_download_archive` to reconstruct path:
```python
if not job.output_directory:
    import tempfile
    job.output_directory = os.path.join(tempfile.gettempdir(), "medical_patients", f"job_{job_id}")
```

## Verification
- Generated new jobs with multiple output formats (json, csv)
- Output files properly stored in database
- Downloads work correctly
- ZIP archives contain all generated files

## Technical Details
- Output files stored as JSONB array in PostgreSQL
- Directory pattern: `/tmp/medical_patients/job_{job_id}/`
- Files named: `patients.json`, `patients.csv`, etc.
- Compression adds `.gz` extension if enabled

## Future Considerations
1. Consider adding output_directory column to jobs table
2. Standardize on single field name (output_files) 
3. Add cleanup job for old temp directories
4. Store files in persistent storage for production