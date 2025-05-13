# Common Issues and Solutions

## Troubleshooting Guide

This document provides solutions to common issues that might be encountered when using or developing with the Military Medical Exercise Patient Generator.

### Installation Issues

1. **ModuleNotFoundError when running the application**

   **Problem**: Python can't find a required module after installation.
   
   **Solution**:
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check that the virtual environment is activated
   - Install the package in development mode: `pip install -e .`
   - Verify Python path includes the project directory

2. **Version compatibility errors with dependencies**

   **Problem**: Conflicting dependency versions causing errors.
   
   **Solution**:
   - Create a fresh virtual environment
   - Install exact versions specified in requirements.txt
   - If using newer versions, check for breaking API changes
   - For FastAPI/Pydantic issues, note that Pydantic v2 requires updates to models

3. **Cryptography package installation failures**

   **Problem**: The cryptography package requires additional system dependencies.
   
   **Solution**:
   - Install required system packages:
     - Ubuntu/Debian: `apt-get install build-essential libssl-dev libffi-dev python3-dev`
     - RHEL/CentOS: `yum install gcc openssl-devel libffi-devel python-devel`
     - Windows: Ensure Visual C++ Build Tools are installed
   - Try installing a pre-built wheel: `pip install cryptography --only-binary=cryptography`

### Generation Issues

1. **Memory errors when generating large patient counts**

   **Problem**: Out of memory errors with large patient counts.
   
   **Solution**:
   - Reduce the number of patients generated in a single batch
   - Increase available memory (if possible)
   - Monitor memory usage during generation
   - Consider a more memory-efficient approach for very large datasets

2. **Percentage distribution validation failures**

   **Problem**: Front or injury distributions don't add up to 100%.
   
   **Solution**:
   - Ensure all percentages add up to exactly 100%
   - Check for rounding errors (use 33.3 instead of 33.333...)
   - In the UI, values are validated automatically
   - For API/programmatic use, verify totals before submission

3. **Unbalanced patient flow results**

   **Problem**: Generated flow doesn't match expected distributions.
   
   **Solution**:
   - Check configuration percentages for fronts and injury types
   - Verify that the random seed isn't fixed
   - Remember that small sample sizes will have more variance
   - For consistent results, set random seed manually
   - Statistical distributions are approximate and will vary randomly

4. **Missing demographics for certain nationalities**

   **Problem**: Some nationalities don't have complete demographic data.
   
   **Solution**:
   - System falls back to USA if nationality not found
   - Check for typos in nationality codes (must be POL, EST, FIN, etc.)
   - Extend `demographics.py` with additional nationality data if needed
   - Check console for any warnings about nationality fallbacks

### Web Interface Issues

1. **Web interface doesn't load**

   **Problem**: Unable to access the web interface.
   
   **Solution**:
   - Verify server is running with `python app.py`
   - Check if server is running on expected port (default: 8000)
   - Try accessing with http://localhost:8000 directly
   - Check console for startup errors
   - Verify no other service is using port 8000

2. **Generation job gets stuck at "running"**

   **Problem**: Job appears to be running but never completes.
   
   **Solution**:
   - Check server console for errors
   - Look for Python tracebacks indicating exceptions
   - Verify system has sufficient resources (memory, disk space)
   - Try a smaller patient count to test
   - Restart the server if it's in a bad state

3. **Download button doesn't appear after completion**

   **Problem**: Job completes but download button is missing.
   
   **Solution**:
   - Check if job status actually shows "completed"
   - Refresh the page and check job status again
   - Inspect browser console for JavaScript errors
   - Verify output files were created on the server
   - Try accessing the download URL directly: `/api/download/{job_id}`

4. **Charts not displaying correctly**

   **Problem**: Visualization charts are missing or broken.
   
   **Solution**:
   - Check browser console for JavaScript errors
   - Verify Chart.js loaded correctly
   - Ensure job summary data is available and properly formatted
   - Try a different browser
   - Update Chart.js version in the HTML file

### Output File Issues

1. **Empty or corrupted output files**

   **Problem**: Generated files are empty or cannot be opened.
   
   **Solution**:
   - Check server logs for file writing errors
   - Verify sufficient disk space
   - Ensure output directory is writable
   - Try generating with a smaller patient count
   - Disable compression and encryption to isolate the issue

2. **Can't decrypt encrypted files**

   **Problem**: Unable to decrypt encrypted output files.
   
   **Solution**:
   - Ensure you're using the correct password
   - For random keys, note that they are only stored in memory during the session
   - Verify the encryption option was enabled during generation
   - Check for any cryptography errors in the logs
   - Try regenerating with a simpler password

3. **XML output not well-formed**

   **Problem**: XML output files fail validation or parsing.
   
   **Solution**:
   - Check for error messages during XML formatting
   - Try generating JSON format instead
   - Examine the XML file for specific formatting issues
   - Look for invalid characters or encoding problems
   - Consider adjusting the XML formatting options in `formatter.py`

4. **NDEF files not compatible with NFC tags**

   **Problem**: Generated NDEF files cannot be written to NFC tags.
   
   **Solution**:
   - Verify the NFC tag supports the data size
   - Check that the MIME type is supported
   - Try using the compressed version for larger datasets
   - Ensure the NFC writer software supports custom MIME types
   - Verify the NDEF format is compliant with specification

### FHIR Compliance Issues

1. **FHIR validation errors**

   **Problem**: Generated FHIR bundles fail validation.
   
   **Solution**:
   - Identify the specific validation errors
   - Check the implementation in `fhir_generator.py`
   - Update resource structure to match FHIR R4 specifications
   - Ensure required fields are present in all resources
   - Verify reference formats are correct

2. **Missing or incorrect SNOMED CT codes**

   **Problem**: SNOMED CT codes are missing or incorrect.
   
   **Solution**:
   - Check medical condition lists in `medical.py`
   - Verify codes against official SNOMED CT browser
   - Update codes to use current versions
   - Add more specific codes if needed
   - Ensure correct system URLs are used in coding blocks

3. **DateTime format issues**

   **Problem**: Date or time formats are invalid.
   
   **Solution**:
   - Ensure all dates use ISO8601 format (YYYY-MM-DD)
   - Check datetime handling in `fhir_generator.py`
   - Verify timezone handling if present
   - Ensure birthdate format is correct for patient resources
   - Check for any manual date string formatting

### Development and Extension Issues

1. **Adding a new nationality isn't working**

   **Problem**: New nationality data isn't being used in generation.
   
   **Solution**:
   - Verify nationality code is added to all required dictionaries
   - Add first and last name lists for the nationality
   - Implement ID format generation function
   - Update nationality distribution configurations
   - Check for typos in nationality codes

2. **Custom medical conditions not appearing**

   **Problem**: Added medical conditions aren't being used.
   
   **Solution**:
   - Check that conditions are added to the correct list in `medical.py`
   - Verify SNOMED CT codes are valid and unique
   - Ensure probability distribution allows selection
   - Check for any filtering based on injury type or triage category
   - Verify class extension if using inheritance

3. **Unit tests failing after changes**

   **Problem**: Unit tests fail after code modifications.
   
   **Solution**:
   - Identify specific failing tests in the error output
   - Check if the test expectations match your changes
   - Update tests to match new behavior if intentional
   - Verify that required test fixtures are updated
   - Run specific failing tests to isolate issues: `python -m unittest tests.TestClassName.test_method_name`

4. **API endpoints return unexpected errors**

   **Problem**: API calls fail with HTTP errors.
   
   **Solution**:
   - Check the server logs for detailed error traces
   - Verify request format matches expected input models
   - Check for changes in FastAPI or Pydantic versions
   - Test endpoint with minimal valid input
   - Use tools like Postman to debug API requests

### Performance Issues

1. **Slow generation for large patient counts**

   **Problem**: Generation takes too long for large numbers of patients.
   
   **Solution**:
   - Profile the code to identify bottlenecks
   - Consider implementing batch processing
   - Optimize the heaviest operations
   - Add parallel processing for independent operations
   - Reduce complexity of generation if possible

2. **High memory usage during generation**

   **Problem**: Memory usage grows too large during generation.
   
   **Solution**:
   - Add incremental processing for large datasets
   - Release references to large objects when no longer needed
   - Consider streaming output rather than in-memory processing
   - Profile memory usage to identify leaks
   - Optimize data structures for memory efficiency

3. **Web interface becomes unresponsive**

   **Problem**: Browser slows down or freezes when displaying results.
   
   **Solution**:
   - Implement pagination for large result sets
   - Optimize JavaScript code in the UI
   - Reduce the size of data transferred to the browser
   - Consider using web workers for heavy client-side processing
   - Implement progressive loading of visualizations

### Deployment Issues

1. **Application won't start in production environment**

   **Problem**: Application starts locally but fails in production.
   
   **Solution**:
   - Check for environment-specific configuration issues
   - Verify all dependencies are installed in production
   - Check for path or permission issues
   - Look for environment variables that might differ
   - Verify Python version compatibility

2. **Output directory permission errors**

   **Problem**: Cannot write to output directory.
   
   **Solution**:
   - Check filesystem permissions
   - Verify the application has write access to the directory
   - Use a configurable output path that can be set at runtime
   - Create directories with appropriate permissions if they don't exist
   - Log the exact path being used to verify location

3. **Server timeouts for large generations**

   **Problem**: Web server times out during large generation jobs.
   
   **Solution**:
   - Increase server timeout settings
   - Implement background processing (already done with FastAPI)
   - Add proper status updates to track progress
   - Consider chunking large jobs into smaller batches
   - Optimize generation process for speed

### Common CLI Issues

1. **Command-line demo fails with arguments**

   **Problem**: The demo script fails when passing arguments.
   
   **Solution**:
   - Check argument parsing in `demo.py`
   - Verify argument format and types
   - Run with `--help` to see expected arguments
   - Check for changes in argparse implementation
   - Try running without arguments first to isolate issues

2. **Cannot find output from CLI generation**

   **Problem**: Output files from command-line generation are missing.
   
   **Solution**:
   - Check the configured output directory
   - Verify write permissions for the directory
   - Look for error messages in console output
   - Ensure generation completed successfully
   - Check default output location if none specified

### Data Quality Issues

1. **Unrealistic vital signs in observations**

   **Problem**: Generated vital signs are outside normal ranges.
   
   **Solution**:
   - Check distribution parameters in `flow_simulator.py`
   - Adjust random distribution parameters
   - Add range checks for generated values
   - Consider condition-appropriate vital sign ranges
   - Implement more sophisticated physiological models if needed

2. **Incorrect relationships between conditions and treatments**

   **Problem**: Treatments don't match conditions appropriately.
   
   **Solution**:
   - Review condition-treatment mappings in `medical.py`
   - Enhance the logic for treatment selection
   - Add more specific treatments for conditions
   - Implement severity-appropriate treatment selection
   - Consider adding a formal medical ontology
