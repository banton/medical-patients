# Test Failure Investigation Protocol

## Core Principle: NEVER SKIP OR CIRCUMVENT FAILED TESTS

**ALWAYS INVESTIGATE THOROUGHLY AND ASK WHEN UNCERTAIN**

## Protocol for Failed Tests

### 1. **Investigation First**
- **NEVER skip** a failing test without understanding why it fails
- **NEVER assume** a test is "legacy" or "irrelevant" 
- **ALWAYS investigate** what the test is actually testing
- **READ the test code** to understand the intended behavior
- **TRACE the execution** to find the root cause

### 2. **Understanding the Intent**
Before taking any action, answer these questions:
- What is this test trying to verify?
- What user workflow or business requirement does it represent?
- Is this testing a legitimate feature that should exist?
- Is the test expectation correct, or is the implementation incorrect?

### 3. **Resolution Approaches (In Order of Preference)**

#### **Option 1: Fix the Implementation (PREFERRED)**
- If the test represents legitimate functionality that should exist
- If the test expectation is correct but implementation is missing/wrong
- Implement the missing feature or fix the bug
- This is almost always the right choice

#### **Option 2: Fix the Test**
- Only if the test expectation is incorrect
- Only if the test doesn't match actual requirements
- Update test to match correct behavior
- Document why the change was made

#### **Option 3: Ask for Clarification**
- When unsure about requirements or expected behavior
- When test seems to contradict other requirements
- When implementation approach is unclear
- **ALWAYS ASK rather than assume**

#### **Option 4: Temporary Marking (LAST RESORT)**
- Only after investigation and asking
- Only when explicitly told to defer implementation
- Mark with detailed TODO explaining what needs to be done
- Track as technical debt with clear next steps

### 4. **What NEVER to Do**

❌ **Skip tests without investigation**
❌ **Assume tests are "legacy" or obsolete**
❌ **Comment out failing tests**
❌ **Mark tests as expected to fail without fixing**
❌ **Circumvent test requirements**
❌ **Make assumptions about requirements**

### 5. **Documentation Requirements**

When fixing failed tests, document:
- **Root cause** of the failure
- **What was implemented/fixed**
- **Why this approach was chosen**
- **Any dependencies or related changes**

## Example Investigation Process

```
1. Test fails: test_configuration_validation()
2. Read test code: Expects POST /api/v1/configurations/validate/
3. Check implementation: Endpoint doesn't exist
4. Analyze purpose: Client-side validation before saving
5. Question: Is this a legitimate requirement? YES
6. Action: Implement the validation endpoint
7. Document: Added validation endpoint for UX improvement
```

## Key Reminders

- **Failing tests indicate gaps** between requirements and implementation
- **Tests often represent user needs** that haven't been built yet
- **Investigation reveals missing features** that add real value
- **Asking questions prevents wrong assumptions** and wasted work
- **Proper implementation is always better** than workarounds

## Test Failure Motto

> "Every failing test is teaching us something important. Listen to what it's saying."

---

*This protocol ensures we build complete, robust systems that meet all requirements.*