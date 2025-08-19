# How to Use These Review Prompts

## Overview
I've created four prompts for a critical review of the hemorrhage modeling implementation. Each has a different focus and approach. Use them with a fresh Claude instance to get an unbiased, critical review.

## The Prompts (in order of recommended use)

### 1. `MASTER_REVIEW_PROMPT.md` - Start Here
**Purpose**: Complete critical review with clear success criteria  
**Time**: 2 hours  
**Focus**: Simplify by 75%, maintain clinical validity  
**Best for**: Getting a comprehensive review and simplified solution

### 2. `CLAUDE_SIMPLE_REVIEW.md` - Quick Simplification
**Purpose**: Rapid simplification focused on deletion  
**Time**: 30-60 minutes  
**Focus**: Get to <150 lines of code  
**Best for**: When you need a quick win and minimal implementation

### 3. `CLAUDE_SS_INTEGRATION.md` - Integration Focus
**Purpose**: How hemorrhage fits into the broader SimedisScore system  
**Time**: 1 hour  
**Focus**: Minimal integration with existing patient model  
**Best for**: Understanding the big picture and avoiding over-engineering

### 4. `CLAUDE_REVIEW_PROMPT.md` - Detailed Analysis
**Purpose**: Comprehensive architectural review  
**Time**: 3-4 hours  
**Focus**: Deep dive into problems and alternatives  
**Best for**: When you need thorough documentation of issues

## How to Use with Claude

### Option 1: Single Comprehensive Review
```
1. Start a new Claude conversation
2. Paste the entire MASTER_REVIEW_PROMPT.md
3. Add: "The implementation is in /Users/banton/Sites/medical-patients/patient_generator/hemorrhage/"
4. Let Claude analyze and provide simplified solution
```

### Option 2: Iterative Refinement
```
1. Start with CLAUDE_SIMPLE_REVIEW.md for quick wins
2. Then use CLAUDE_SS_INTEGRATION.md to ensure it fits the bigger picture
3. Finally, use MASTER_REVIEW_PROMPT.md for final validation
```

### Option 3: Team Review
```
Give different prompts to different reviewers:
- Developer: CLAUDE_SIMPLE_REVIEW.md (focus on code)
- Architect: CLAUDE_SS_INTEGRATION.md (focus on system design)
- Lead: MASTER_REVIEW_PROMPT.md (focus on business value)
```

## Key Instructions to Add

When using any prompt, also tell Claude:

```
Additional context:
- We have ~1000-5000 patients to simulate
- Performance matters but not critical (seconds, not milliseconds)
- This is for training/simulation, not real-time clinical use
- We can iterate - MVP first, enhance later
- Integration with existing code is more important than perfection
```

## Expected Outcomes

### From a Good Review:
1. **Simplified hemorrhage.py** (<150 lines total)
2. **Clear integration points** with existing Patient class
3. **Deletion list** of unnecessary code
4. **Proof of equivalence** showing simple = complex for our use case
5. **2-minute explanation** that anyone can understand

### Red Flags in Review:
- Suggests adding MORE abstraction
- Can't explain simply
- Focuses on edge cases we don't have
- Proposes new frameworks or patterns
- Can't show clear benefit/complexity tradeoff

## The Ultimate Test

After the review, you should be able to:
1. Implement hemorrhage in 1 hour (not 1 week)
2. Explain it in 2 minutes (not 20)
3. Test it with 10 lines (not 100)
4. Maintain it with confidence

## Sample Conversation Starter

```
I need you to critically review a hemorrhage modeling system and simplify it dramatically. 

The current implementation is 500+ lines across multiple files. I need it to be <150 lines in a single file while maintaining 90% of the clinical validity.

[Paste MASTER_REVIEW_PROMPT.md here]

The code is located at: /Users/banton/Sites/medical-patients/patient_generator/hemorrhage/

Be ruthless about removing complexity. Every line of code is a liability. Start by trying to delete 75% of the code and see what breaks.
```

## Remember

The goal is NOT to create the perfect hemorrhage model. The goal is to create the SIMPLEST hemorrhage model that makes our SimedisScore system useful for training simulations.

Complexity can always be added later. It can rarely be removed.
