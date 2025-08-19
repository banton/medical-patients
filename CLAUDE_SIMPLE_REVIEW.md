# Quick Start Prompt for Critical Review

## One-Line Summary
Review and drastically simplify the hemorrhage modeling system in `/patient_generator/hemorrhage/` - be ruthless about removing complexity.

## The Situation
- We have battlefield medical research showing bleeding rates for injuries
- Someone implemented a complex system with 10 body regions, vessel types, and multiple classes
- We need the SIMPLEST thing that works, not the most comprehensive

## Your Job in 3 Steps

### Step 1: Audit (30 minutes)
```python
# Read these files and identify what can be deleted
/patient_generator/hemorrhage/body_regions.py  # 200+ lines - probably needs 20
/patient_generator/hemorrhage/hemorrhage_model.py  # 400+ lines - could be 100
/patient_generator/hemorrhage/integration.py  # Nice-to-have, not essential
```

### Step 2: Simplify (1 hour)
Create ONE file that does everything essential:
```python
# hemorrhage_simple.py - Target: <150 lines total

BLEEDING_RATES = {
    "minor": 0.2,      # Small wounds
    "moderate": 1.5,   # Limb arteries  
    "severe": 5.0      # Major vessels
}

def get_bleeding_rate(injury_code: str, severity: str) -> float:
    # 10 lines max
    pass

def is_tourniquetable(injury_code: str) -> bool:
    # Extremity injuries only
    pass
```

### Step 3: Integrate (30 minutes)
Show exactly how to add this to the existing `Patient` class:
```python
# In patient.py
self.bleeding_rate = get_bleeding_rate(condition['code'], condition['severity'])
self.needs_tourniquet = is_tourniquetable(condition['code'])
```

## Critical Questions

1. **Why not just use triage category?**
   - T1 = severe bleeding (5.0)
   - T2 = moderate bleeding (1.5)
   - T3 = minor/no bleeding (0.2)
   - Done. Why is it more complex?

2. **Why track body regions?**
   - We only care: Can you put a tourniquet on it? (Yes/No)
   - Arms/Legs = Yes
   - Everything else = No
   - Why do we need 10 regions?

3. **Why model lethal triad progression?**
   - For MVP, constant bleeding rate is fine
   - Add complexity later IF needed
   - What's the actual impact on outcomes?

4. **Why separate hemorrhage from conditions?**
   - Just add `bleeding_rate` to existing conditions
   - No new classes needed
   - Use what's already there

## Output Format

### 1. What to Delete (Be Brutal)
- [ ] File X - entire file unnecessary
- [ ] Class Y - overcomplicated
- [ ] Method Z - no clear value

### 2. Minimal Implementation
```python
# Your complete simplified solution
# Goal: <150 lines that does 90% of what we need
```

### 3. Integration Steps
1. Add field to Patient class
2. Modify one method in medical.py
3. Done

## Remember
- **Every line of code is a liability**
- **Features are expensive, simplicity is valuable**
- **Working code > Perfect abstraction**
- **Ship in 1 day, not 1 week**

## The Test
Can you explain the entire hemorrhage system to a new developer in 2 minutes? If not, it's too complex.
