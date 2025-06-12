# Comprehensive CI Checklist - Medical Patients Generator

## 🎯 Purpose
This checklist prevents repetitive CI failures by ensuring ALL validation steps are performed locally before pushing to GitHub. Based on actual failure patterns from pull requests.

## 📋 Pre-Push CI Validation Checklist

### ✅ **Step 1: Python Linting and Type Checking**
```bash
# Run EXACTLY what CI runs
ruff check src/ patient_generator/
mypy src/ patient_generator/ --ignore-missing-imports
```

**Common Failures to Fix:**
- ❌ `E722`: Bare except clauses → Change `except:` to `except Exception:`
- ❌ `F821`: Undefined variables → Check variable names and imports
- ❌ `EM101`: Exception string literals → Move strings to variables first
- ❌ `RET504`: Unnecessary return assignments → Simplify return statements
- ❌ `C400`: Generators → Convert to list comprehensions where appropriate
- ❌ `SIM102`: Nested if statements → Combine with `and` operator

**Quick Fixes:**
```bash
ruff check --fix src/ patient_generator/  # Auto-fix what's possible
```

### ✅ **Step 2: JavaScript/Frontend Linting**
```bash
# Run EXACTLY what CI runs
npm run lint:check
npm run format:check
```

**Common Failures to Fix:**
- ❌ `prettier/prettier`: Formatting issues → Run `npm run format`
- ❌ `no-trailing-spaces`: Remove trailing whitespace
- ❌ `no-else-return`: Remove unnecessary else after return
- ❌ `indent`: Fix indentation (usually prettier fixes this)

**Quick Fixes:**
```bash
npm run format  # Auto-fix formatting
npm run lint:check  # Verify all issues resolved
```

### ✅ **Step 3: All Tests Pass**
```bash
# Run ALL tests locally
python3 -m pytest tests/ -v --tb=short

# Check specific test counts match CI expectations
# Expected: 124 total tests (43 unit + 21 integration + 60 other)
```

**Test Debugging:**
- If tests fail, check database connections
- Verify all imports work correctly
- Check for random test data causing inconsistencies
- Ensure async functions are properly awaited

### ✅ **Step 4: Type Safety Verification**
```bash
# Ensure no mypy errors
python3 -m mypy src/ patient_generator/ --ignore-missing-imports
```

**Common Type Errors:**
- ❌ Async generator return types
- ❌ Dict/Collection type inference issues  
- ❌ Missing type annotations on functions
- ❌ Incompatible tuple/single value returns

### ✅ **Step 5: Timeline Viewer Build**
```bash
cd patient-timeline-viewer
npm run build
cd ..
```

**React/Vite Build Issues:**
- ❌ TypeScript errors in React components
- ❌ Missing dependencies in package.json
- ❌ Import path issues
- ❌ CSS/Tailwind configuration problems

### ✅ **Step 6: Security Scan Preparation**
```bash
# Check for accidentally committed secrets
grep -r "sk-\|pk_\|AIza\|AKIA\|password.*=.*['\"]" . --exclude-dir=.git --exclude-dir=.venv --exclude-dir=node_modules --exclude="*.md"

# Check for real secret patterns (not just test names)
grep -r "api_key.*=.*['\"]" . --exclude-dir=.git --exclude-dir=.venv --exclude="test*" --exclude="*.md"
```

### ✅ **Step 7: Docker Build Test**
```bash
# Test Docker build locally (optional but recommended for complex changes)
docker build -t medical-patients-test .
```

## 🔄 **Complete Pre-Push Workflow**

```bash
#!/bin/bash
# Save this as check-ci.sh and run before every push

echo "🔍 Running complete CI validation locally..."

echo "1. Python linting..."
ruff check src/ patient_generator/ || exit 1

echo "2. Type checking..."
mypy src/ patient_generator/ --ignore-missing-imports || exit 1

echo "3. JavaScript linting..."
npm run lint:check || exit 1

echo "4. JavaScript formatting..."
npm run format:check || exit 1

echo "5. Running all tests..."
python3 -m pytest tests/ -q || exit 1

echo "6. Building timeline viewer..."
cd patient-timeline-viewer && npm run build && cd .. || exit 1

echo "7. Security check..."
if grep -r "sk-\|pk_\|password.*=.*['\"]" . --exclude-dir=.git --exclude-dir=.venv --exclude-dir=node_modules --exclude="*.md" | grep -v "test\|example"; then
    echo "❌ Potential secrets found!"
    exit 1
fi

echo "✅ All CI checks passed locally! Safe to push."
```

## 🎯 **Failure Pattern Learning**

### **JavaScript Linting Issues (Most Common)**
1. **Always run `npm run format` after editing JS files**
2. **Check for `no-else-return` errors** - remove unnecessary else blocks
3. **Watch for indentation issues** - usually auto-fixed by prettier
4. **Trailing spaces** - configure your editor to remove them

### **Python Type Issues (Second Most Common)**  
1. **Async generator return types** - ensure tuples match expected signatures
2. **Dict type inference** - add explicit type annotations when mypy confused
3. **Import errors** - verify all imports work in isolation

### **Test Failures (Third Most Common)**
1. **Configuration CRUD tests** - make robust to database state
2. **Random data in tests** - use fixed test data only
3. **Database cleanup** - ensure tests don't interfere with each other

## 📝 **Key Memory Points**

### **For Future PRs:**
1. **ALWAYS run the complete validation locally first**
2. **Never assume "small changes" won't break linting**
3. **JavaScript formatting is STRICT** - always run prettier
4. **Test both unit AND integration tests**
5. **Type checking catches production bugs early**

### **Emergency CI Fix Workflow:**
1. Pull latest changes
2. Run `npm run format` + `ruff check --fix`
3. Run full test suite
4. Commit with "fix(ci): resolve linting and formatting issues"
5. Push immediately

## 🚀 **Success Metrics**
- **Goal**: Zero CI failures after following this checklist
- **Time Saved**: ~15 minutes per failed CI round
- **Reliability**: 99%+ CI pass rate when checklist completed

---

**Last Updated**: Based on comprehensive CI failure analysis
**Applies To**: All future PRs and development cycles
**Status**: Use this checklist for EVERY push to avoid repetitive CI failures