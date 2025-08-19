# Data Optimization Strategy

## Goal
Minimize data footprint while maintaining single-file portability and all metadata richness.

## Compression Approach: Single File + Gzip

### File Structure
```
patients.json.gz (single compressed file)
├── Uncompressed: 20MB (1000 patients)
└── Compressed: ~2MB (90% reduction)
```

### Browser Decompression
```javascript
// React viewer modification
async function loadPatientData(file) {
  if (file.name.endsWith('.gz')) {
    const arrayBuffer = await file.arrayBuffer();
    const decompressed = pako.inflate(new Uint8Array(arrayBuffer), { to: 'string' });
    return JSON.parse(decompressed);
  }
  // Regular JSON handling
  return JSON.parse(await file.text());
}
```

## Internal JSON Optimization (Before Compression)

### 1. Abbreviated Keys
```javascript
// BEFORE (verbose)
{
  "patient_id": "POL-2024-00142",
  "timestamp": "2024-03-15T06:42:00Z",
  "health_score": 55,
  "blood_volume_percent": 85,
  "triage_category": "T1"
}

// AFTER (abbreviated)
{
  "id": "POL-2024-00142",
  "ts": 1710486120,  // Unix timestamp
  "hs": 55,
  "bv": 85,
  "tr": 1  // Numeric code
}
```

### 2. Enumeration Mapping
```javascript
// Define at file level once
const ENUMS = {
  "triage": {"T1": 1, "T2": 2, "T3": 3},
  "injury": {"gsw": 1, "shrapnel": 2, "blast": 3},
  "facility": {"POI": 1, "Role1": 2, "Role2": 3},
  "treatment": {"tourniquet": 1, "iv_fluids": 2, "surgery": 3}
};

// Use numeric codes in data
"treatments": [1, 2]  // Instead of ["tourniquet", "iv_fluids"]
```

### 3. Timeline as Arrays
```javascript
// BEFORE (objects)
"timeline": [
  {"time": "06:42:00", "event": "injury", "health": 55},
  {"time": "06:47:00", "event": "tourniquet", "health": 52}
]

// AFTER (arrays)
"tl": [
  [402, 1, 55],  // [seconds_from_start, event_code, health]
  [702, 2, 52]
]
```

### 4. Delta Encoding for Health
```javascript
// BEFORE (absolute values)
"health_timeline": [100, 95, 88, 82, 75, 68, 60]

// AFTER (delta values)
"h_delta": [100, -5, -7, -6, -7, -7, -8]  // First value absolute, rest are changes
```

### 5. Omit Defaults and Nulls
```javascript
// BEFORE
{
  "surgery_required": false,
  "surgery_performed": null,
  "complications": [],
  "death_category": null,
  "transported_by_air": false
}

// AFTER (omit all defaults/nulls)
{
  // Only include if true or has value
}
```

## Size Reduction Analysis

### Per Patient Breakdown
```
Original verbose JSON:      20 KB
After key abbreviation:     14 KB (30% reduction)
After enumeration:          10 KB (50% reduction)
After array conversion:      8 KB (60% reduction)
After omitting defaults:     6 KB (70% reduction)
After gzip compression:      1.2 KB (94% reduction)
```

### For 1000 Patients
```
Original:                   20 MB
Optimized JSON:             6 MB
Gzipped:                    1.2 MB
```

## Metadata Dictionary

Include a compact dictionary at the start of the file:

```javascript
{
  "version": "3.0",
  "dictionary": {
    "keys": {
      "id": "patient_id",
      "ts": "timestamp",
      "hs": "health_score",
      "bv": "blood_volume",
      "tr": "triage"
    },
    "enums": {
      "triage": ["", "T1", "T2", "T3"],
      "injury": ["", "gsw", "shrapnel", "blast"],
      "facility": ["", "POI", "Role1", "Role2", "Role3"]
    }
  },
  "patients": [
    // Compressed patient data
  ]
}
```

## Implementation Steps

### 1. Generator Updates
```python
def optimize_patient_data(patient):
    """Convert verbose patient to optimized format"""
    return {
        "id": patient.id,
        "ts": int(patient.timestamp.timestamp()),
        "hs": patient.health_score,
        "bv": patient.blood_volume,
        "tr": TRIAGE_CODES[patient.triage],
        "tl": compress_timeline(patient.timeline)
    }

def save_compressed(patients, filename):
    """Save as gzipped JSON"""
    optimized = {
        "version": "3.0",
        "dictionary": DICTIONARY,
        "patients": [optimize_patient_data(p) for p in patients]
    }
    
    json_str = json.dumps(optimized, separators=(',', ':'))
    
    with gzip.open(f"{filename}.gz", 'wt', encoding='utf-8') as f:
        f.write(json_str)
```

### 2. React Viewer Updates
```javascript
// Add pako library for browser decompression
import pako from 'pako';

// Decode optimized format
function decodePatient(compressed, dictionary) {
  return {
    patient_id: compressed.id,
    timestamp: new Date(compressed.ts * 1000),
    health_score: compressed.hs,
    blood_volume: compressed.bv,
    triage: dictionary.enums.triage[compressed.tr],
    timeline: decodeTimeline(compressed.tl, dictionary)
  };
}
```

## Benefits

1. **90%+ size reduction** - 20MB → 2MB
2. **Single file maintained** - Easy portability
3. **Browser compatible** - Native gzip support
4. **Secure environment ready** - No external dependencies
5. **Fast loading** - 2MB loads quickly even on slow connections

## Trade-offs

1. **Slightly more complex parsing** - Need to decode
2. **Dictionary overhead** - Small fixed cost
3. **Less human-readable** - But who reads 1000 patients manually?

## Performance Targets

- Generate 1000 patients: < 30 seconds
- Compress to gzip: < 2 seconds
- Browser decompress: < 1 second
- Parse and render: < 3 seconds
- Total load time: < 5 seconds

This strategy maintains all our rich metadata while making files 10x smaller and keeping single-file portability intact.