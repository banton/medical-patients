# CRITICAL: Development Workflow Requirements

## 🚨 **MANDATORY: ALWAYS USE MAKEFILE**

**USER REQUIREMENT**: Use the Makefile for ALL development operations. This has been stated multiple times.

### Required Commands:
- `make dev` - Start development server
- `make test` - Run tests
- `make lint` - Run linting
- `make format` - Format code
- `make build` - Build application
- `make clean` - Clean up

### **NEVER** use direct commands like:
- ❌ `python3 -m uvicorn src.main:app --reload --port 8000`
- ❌ `python3 -m pytest`
- ❌ Manual server startup

### **ALWAYS** use Makefile commands:
- ✅ `make dev`
- ✅ `make test`
- ✅ `make lint`

## Important Notes:
- User has emphasized this requirement multiple times
- Ignoring Makefile usage shows lack of attention to user preferences
- The Makefile contains the proper development workflow
- Using direct commands bypasses project-specific configurations

**REMEMBER: When user says to use Makefile, they mean it!**