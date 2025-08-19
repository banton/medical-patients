# MASTER REVIEW PROMPT: Hemorrhage Model Critical Analysis

## Your Role
You are a **skeptical senior architect** reviewing a hemorrhage modeling system. Your mandate is to **ruthlessly simplify** while maintaining clinical validity. Be critical. Question everything. Accept nothing by default.

## Quick Context
- **Goal**: Implement SimedisScore (SS) system for patient deterioration (0-20 scale)
- **Current**: Someone built a 500+ line hemorrhage module with 10 body regions
- **Research**: Table 1 shows 5 bleeding categories with rates (α₀) and progression factors (k)
- **Reality**: We need the simplest thing that provides value

## Three-Part Review Process

### Part 1: Demolition (30 min)
Read `/patient_generator/hemorrhage/` and identify everything that can be deleted:
```bash
wc -l hemorrhage/*.py  # Current line count
# Your goal: Reduce by 80%
```

**Questions to ask:**
- Why 10 body regions when we only care about tourniquetable vs not?
- Why track vessel types when we only use bleeding rate?
- Why separate module when it could be 3 fields in Patient class?
- Why complex inheritance when a dictionary lookup would work?

### Part 2: Reconstruction (45 min)
Build the minimal viable hemorrhage system:

```python
# Target: Complete implementation in <100 lines
# hemorrhage_minimal.py

# Just what we need from Table 1
BLEEDING_RATES = {
    'minor': (0.2, 0.02),      # (α₀, k)
    'moderate': (1.5, 0.05),   
    'severe': (5.0, 0.15),
    'massive': (10.0, 0.3)
}

def classify_hemorrhage(injury_code: str, triage: str) -> tuple[float, float]:
    """Return (bleeding_rate, progression_factor) or (0, 0)"""
    # Your logic here - aim for <20 lines
    pass

def affects_limb(injury_code: str) -> bool:
    """Can a tourniquet help?"""
    # Literally just: is it an arm or leg injury?
    pass

# That's it. No classes. No inheritance. No separate files.
```

### Part 3: Integration Proof (45 min)
Show EXACTLY how this connects to the SS system:

```python
# In existing patient.py
class Patient:
    def __init__(self):
        # ... existing code ...
        self.bleeding_rate_hr = 0  # α₀ from Table 1
        self.bleeding_k = 0         # k factor
        
    def update_blood_volume(self, hours_elapsed):
        """Simple exponential decay with progression"""
        if self.bleeding_rate_hr > 0:
            alpha = self.bleeding_rate_hr + (self.bleeding_k * hours_elapsed)
            self.blood_volume *= math.exp(-alpha * hours_elapsed)
            
    def calculate_ss(self):
        """SimedisScore affected by blood loss"""
        # Modify vital signs based on blood volume
        # Calculate SS
        # Return score 0-20
```

## Deliverables

### 1. Deletion List (Be Ruthless)
```markdown
Files to delete:
- [ ] body_regions.py - Overcomplicated, just need binary tourniquetable flag
- [ ] integration.py - Nice-to-have features, not MVP
- [ ] ...

Code to remove:
- [ ] VesselType enum - No value for SS calculation
- [ ] BodyLocation class - Overengineered
- [ ] ...
```

### 2. Minimal Implementation (<100 lines)
```python
# Your complete, working, simplified hemorrhage system
# Must handle:
# 1. Map injury -> bleeding rate
# 2. Track blood volume over time  
# 3. Identify tourniquetable injuries
# That's ALL.
```

### 3. Proof of Equivalence
Run both systems on test cases:
```python
# Show that simple system gives similar results
test_injuries = [
    ("262574004", "T1"),  # Bullet wound
    ("284551006", "T1"),  # Amputation
    ("125689001", "T2"),  # Shrapnel
]

for injury_code, triage in test_injuries:
    complex_result = complex_system.calculate(...)
    simple_result = simple_system.calculate(...)
    assert abs(complex_result - simple_result) < 0.1  # Close enough
```

### 4. Integration Plan (5 steps max)
1. Add 2 fields to Patient
2. Add 1 method for blood volume update
3. Modify SS calculation to check blood volume
4. Done
5. (There is no step 5)

## Evaluation Criteria

### You WIN if:
- ✅ Reduce code by >75%
- ✅ Maintain clinical validity
- ✅ Integration adds <50 lines to existing code
- ✅ Can explain in 2 minutes
- ✅ No new dependencies

### You FAIL if:
- ❌ Add new classes when dictionary would work
- ❌ Create abstractions for single use cases
- ❌ Prioritize "correctness" over simplicity
- ❌ Can't show clear benefit vs complexity

## The Nuclear Option

If you can't simplify by 75%, consider:
```python
# The absolute minimum - just modify triage
def add_hemorrhage_effect(patient):
    if patient.triage_category == "T1":
        patient.ss_modifier = -5  # Severe bleeding effect
    elif patient.triage_category == "T2":
        patient.ss_modifier = -2  # Moderate bleeding
    # That's it. 4 lines. Done.
```

**Is this good enough?** If yes, delete everything else.

## Final Thoughts

Remember:
- **Every line of code will need to be maintained**
- **Complex systems fail in complex ways**
- **We can always add complexity later**
- **We can't always remove it**

Start with the simplest thing. Only add complexity when you have proof it's needed.

## Begin Here

1. Count lines in current implementation
2. Set target: 25% of current
3. Start deleting
4. Build minimal replacement
5. Prove it works
6. Ship it

**Your north star**: What's the simplest hemorrhage model that would make the SS system clinically useful?

---

*Note: The research is in `/modeling-research/`. Table 1 is the only required reference. Everything else is optional complexity.*
