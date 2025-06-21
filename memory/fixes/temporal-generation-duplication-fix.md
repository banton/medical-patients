# Temporal Generation Duplication Bug

## Issue
When generating patients with temporal configuration (e.g., "5 days of fighting"), the chunked generation logic causes massive duplication:
- Requested: 2,500 patients
- Generated: 11,250 patients (4.5x)
- Many patient IDs appear 2-3 times

## Root Cause
The `_generate_patient_chunk` method in `patient_generation_service.py` has a critical bug:

1. For large patient counts (>1000), it uses chunked generation
2. Each chunk calls `flow_simulator.generate_casualty_flow()`
3. Temporal generation creates ALL patients based on the timeline, ignoring chunk size
4. Each chunk gets the full patient set, then re-IDs them to the chunk range

Example for 2500 patients:
- Chunk 1 (0-999): Generates all 2500, assigns IDs 0-999
- Chunk 2 (1000-1999): Generates all 2500 again, assigns IDs 1000-1999  
- Chunk 3 (2000-2499): Generates all 2500 again, assigns IDs 2000-2499

Result: Same patients generated multiple times with different IDs.

## Fix Required
The temporal generation should either:
1. Generate all patients at once (no chunking for temporal)
2. Or modify temporal generator to support partial generation

Quick fix: Disable chunking for temporal generation:
```python
# In _generate_base_patients
if total_patients > chunk_size and not context.temporal_config:
    # Use chunking only for non-temporal generation
```

## Impact
- This affects all temporal generations over 1000 patients
- Timeline viewer shows inflated patient counts
- Duplicate patient data with different IDs
- Performance impact from generating 4.5x more data than needed