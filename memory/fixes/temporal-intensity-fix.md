# Temporal Generation Intensity Fix

## Issue
The temporal generation system was multiplying the total patient count by intensity modifiers:
- Low intensity: 0.5x patients
- Medium intensity: 1.0x patients  
- High intensity: 1.5x patients
- Extreme intensity: 2.0x patients

This was conceptually wrong. Intensity should affect HOW casualties arrive (clustering, timing), not HOW MANY total casualties there are. The number of combatants doesn't magically increase with combat intensity.

## Example
- Requested: 2,500 patients with high intensity
- Generated: 3,750 patients (1.5x multiplier applied)
- Expected: 2,500 patients arriving in more clustered/intense patterns

## Root Cause
In `temporal_generator.py`, line 62 was multiplying total patients:
```python
adjusted_total = int(total_patients * intensity_mod["patient_multiplier"])
```

## Fix
Changed to use exact requested amount:
```python
# FIXED: Intensity should NOT change total patient count - it affects clustering/timing only
# Total patients represents actual combatants who can be injured
adjusted_total = total_patients  # Use exact requested amount
```

## Correct Intensity Behavior
Intensity now properly affects:
1. **Mass casualty probability** - Higher intensity = more mass casualty events
2. **Event clustering** - Casualties arrive in larger groups
3. **Time compression** - Casualties arrive in shorter bursts
4. **Peak surge intensity** - Higher spikes during combat peaks

## Verification
- Before: 2,000 patients with high intensity → 3,000 generated
- After: 2,000 patients with high intensity → 2,000 generated ✅

The total patient count now represents the actual number of combatants who can potentially be injured, regardless of combat intensity.