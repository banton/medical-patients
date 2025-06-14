# Git Workflow for Epic Implementation with Production Safety

## 🚨 Critical Context

**LIVE PRODUCTION RISK**: `main` branch is directly connected to production deployment
- **Auto-deployment**: Any push to `main` triggers automatic build/deploy
- **Zero downtime requirement**: Production must remain stable during development
- **Multi-week effort**: 6 epics over 9 weeks require careful coordination

## 🎯 Workflow Objectives

1. **Production Safety**: Never break live production on https://milmed.tech
2. **Epic Isolation**: Each epic developed in isolation with clear boundaries
3. **Incremental Integration**: Safe, tested integration of completed epics
4. **Rollback Capability**: Ability to quickly revert problematic changes
5. **Parallel Development**: Support multiple epics in development simultaneously

## 🌲 Branch Strategy

### Branch Hierarchy
```
main (PRODUCTION - AUTO-DEPLOY)
├── develop (INTEGRATION BRANCH)
│   ├── epic/cross-platform-dev-env (EPIC-001)
│   │   ├── feature/gitattributes-setup
│   │   ├── feature/task-runner-migration
│   │   └── feature/docker-optimization
│   ├── epic/api-key-management (EPIC-002)
│   │   ├── feature/database-models
│   │   ├── feature/cli-tool
│   │   └── feature/demo-key-system
│   ├── epic/production-scalability (EPIC-003)
│   │   ├── feature/connection-pooling
│   │   ├── feature/monitoring-setup
│   │   └── feature/resource-limits
│   └── epic/digitalocean-staging (EPIC-004)
│       ├── feature/staging-infrastructure
│       └── feature/deployment-pipeline
```

### Branch Naming Convention
```
main                           # Production branch (protected)
develop                        # Integration branch for epic coordination
epic/<epic-name>              # Epic feature branch
feature/<epic-name>/<task>    # Individual task implementation
hotfix/<issue-description>    # Emergency production fixes
release/<version>             # Release preparation
```

## 📋 Branch Protection Rules

### Main Branch Protection (CRITICAL)
```yaml
Branch: main
- Require pull request reviews: YES (minimum 2)
- Dismiss stale reviews: YES
- Require review from code owners: YES
- Restrict pushes to matching branches: YES
- Require status checks: YES
  - GitHub Actions CI (all tests pass)
  - Security scan (if applicable)
- Require up-to-date branches: YES
- Include administrators: NO (emergency override capability)
- Allow force pushes: NO
- Allow deletions: NO
```

### Develop Branch Protection
```yaml
Branch: develop
- Require pull request reviews: YES (minimum 1)
- Require status checks: YES
  - GitHub Actions CI
- Require up-to-date branches: YES
- Allow force pushes: NO
- Allow deletions: NO
```

### Epic Branch Protection
```yaml
Branches: epic/*
- Require pull request reviews: NO (development flexibility)
- Require status checks: YES
  - GitHub Actions CI
- Allow force pushes: YES (for rebasing)
- Allow deletions: YES (after completion)
```

## 🔄 Epic Implementation Workflow

### Phase 1: Epic Initialization

#### 1.1 Create Epic Branch
```bash
# Ensure main is up to date
git checkout main
git pull origin main

# Create and switch to epic branch
git checkout -b epic/cross-platform-dev-env
git push -u origin epic/cross-platform-dev-env

# Update epic status in memory
echo "Epic branch created: epic/cross-platform-dev-env" >> memory/epics/cross-platform-dev-environment.md
git add memory/epics/cross-platform-dev-environment.md
git commit -m "epic(dev-env): initialize epic branch

- Created epic/cross-platform-dev-env branch
- Updated epic status documentation
- Ready for feature branch development

Epic-ID: EPIC-001
Phase: Initialization"
```

#### 1.2 Epic Documentation Commit
```bash
# Commit complete epic documentation
git add memory/epics/cross-platform-dev-environment.md
git commit -m "docs(epic-001): comprehensive cross-platform dev environment plan

- Complete 4-phase implementation plan
- Success criteria and testing strategy defined
- Risk mitigation documented
- Ready for task implementation

Epic-ID: EPIC-001
Phase: Documentation"
```

### Phase 2: Feature Development

#### 2.1 Create Feature Branch
```bash
# From epic branch, create feature branch
git checkout epic/cross-platform-dev-env
git checkout -b feature/cross-platform-dev-env/gitattributes-setup

# Implement the feature
# ... development work ...

# Commit with epic context
git add .gitattributes
git commit -m "feat(dev-env): implement cross-platform gitattributes

- Add comprehensive .gitattributes for line ending consistency
- Ensure LF endings for shell scripts and Docker files  
- Prevent Windows CRLF issues
- Support all project file types

Epic-ID: EPIC-001
Task: 1.1 - Line Ending Configuration
Closes: EPIC-001-T1.1"
```

#### 2.2 Feature Integration to Epic
```bash
# Push feature branch
git push -u origin feature/cross-platform-dev-env/gitattributes-setup

# Create PR: feature → epic (NOT main)
gh pr create \
  --base epic/cross-platform-dev-env \
  --head feature/cross-platform-dev-env/gitattributes-setup \
  --title "feat(dev-env): cross-platform gitattributes configuration" \
  --body "$(cat <<'EOF'
## Epic Context
- **Epic ID**: EPIC-001
- **Task**: 1.1 - Line Ending Configuration  
- **Phase**: Foundation Setup (Week 1)

## Implementation
- ✅ Comprehensive .gitattributes for all file types
- ✅ LF enforcement for shell scripts and configs
- ✅ Binary file identification
- ✅ Cross-platform consistency ensured

## Testing
- [ ] Tested on Windows (CRLF → LF conversion)
- [ ] Tested on macOS (consistency maintained)  
- [ ] Tested on Linux (baseline validation)

## Next Steps
After merge, team should re-clone repository to apply new line ending rules.

Part of epic/cross-platform-dev-env implementation.
EOF
)"

# Merge after review (epic branch, safe to merge)
git checkout epic/cross-platform-dev-env
git merge feature/cross-platform-dev-env/gitattributes-setup
git push origin epic/cross-platform-dev-env

# Clean up feature branch
git branch -d feature/cross-platform-dev-env/gitattributes-setup
git push origin --delete feature/cross-platform-dev-env/gitattributes-setup
```

### Phase 3: Epic Completion & Integration

#### 3.1 Epic to Develop Integration
```bash
# Epic complete, integrate to develop
git checkout develop
git pull origin develop

# Create integration PR: epic → develop
gh pr create \
  --base develop \
  --head epic/cross-platform-dev-env \
  --title "epic(dev-env): complete cross-platform development environment" \
  --body "$(cat <<'EOF'
## Epic Summary
**Epic ID**: EPIC-001 - Cross-Platform Development Environment
**Duration**: 3 weeks
**Status**: COMPLETED ✅

## Deliverables Completed
- ✅ Cross-platform .gitattributes configuration
- ✅ Task runner installation and setup
- ✅ Complete Taskfile.yml modular structure  
- ✅ Platform-specific setup scripts (Windows, macOS, Linux)
- ✅ Docker cross-platform optimization
- ✅ VS Code dev container configuration
- ✅ Documentation and migration guides
- ✅ CI/CD cross-platform testing

## Success Criteria Met
- ✅ Setup time reduced to <5 minutes on all platforms
- ✅ All developers can run `task setup && task dev`
- ✅ CI passes on Linux, macOS, Windows
- ✅ Zero platform-specific issues during testing
- ✅ Team successfully migrated from Makefile

## Testing Validation
- ✅ Integration tests pass on all platforms
- ✅ Performance benchmarks met
- ✅ User acceptance testing completed
- ✅ Migration documentation validated

## Impact
- 🚀 Developer productivity improved (5min vs 30min setup)
- 🌍 Windows developers can now contribute effectively
- 🔧 Foundation established for all future epics
- 📚 Comprehensive documentation for onboarding

## Next Steps
Ready for production integration after develop branch validation.

Enables: EPIC-002 (API Key Management), EPIC-003 (Production Scalability)
EOF
)"
```

#### 3.2 Develop Branch Validation
```bash
# After epic integration to develop
git checkout develop
git pull origin develop

# Run comprehensive testing
task test:all
task test:cross-platform
task test:integration

# Validate epic doesn't break existing functionality
task dev  # Should start successfully
task clean  # Should clean properly

# Create validation commit
git add .
git commit -m "test(epic-001): validate cross-platform dev environment integration

- All tests pass on develop branch
- Epic integration successful
- No breaking changes detected
- Ready for production consideration

Epic-ID: EPIC-001
Status: VALIDATED"
```

### Phase 4: Production Release (HIGH CAUTION)

#### 4.1 Pre-Production Validation
```bash
# Extensive testing before production
git checkout develop

# Run full test suite
task test:all
task test:performance
task test:security
task lint:all

# Create release branch for additional safety
git checkout -b release/v2.1.0-cross-platform
git push -u origin release/v2.1.0-cross-platform

# Final validation on release branch
# ... additional testing ...
```

#### 4.2 Production Integration (PROTECTED)
```bash
# Create production PR with maximum caution
gh pr create \
  --base main \
  --head release/v2.1.0-cross-platform \
  --title "release: v2.1.0 - Cross-Platform Development Environment" \
  --body "$(cat <<'EOF'
## 🚨 PRODUCTION RELEASE

**Version**: v2.1.0
**Epic**: EPIC-001 - Cross-Platform Development Environment
**Risk Level**: MEDIUM (infrastructure changes, backward compatible)

## 🔒 Safety Validations
- ✅ All CI tests pass (Linux, macOS, Windows)
- ✅ Integration testing on develop branch (2 weeks)
- ✅ Backward compatibility maintained
- ✅ Rollback plan documented
- ✅ Team training completed

## 📦 Changes Included
- Cross-platform development environment (Task runner)
- Platform-specific setup automation
- Enhanced Docker configuration
- Comprehensive documentation updates

## 🔄 Deployment Plan
1. Merge triggers automatic deployment
2. Monitor deployment logs and health checks
3. Validate application functionality
4. Monitor for 24 hours post-deployment

## 🆘 Rollback Plan
If issues detected:
1. Immediate revert: `git revert <merge-commit>`
2. Alternative: Manual rollback to previous deployment
3. DigitalOcean rollback available as backup

## 👥 Review Requirements
- [ ] Technical lead approval
- [ ] DevOps review
- [ ] Final functionality check

**Auto-deployment will trigger on merge. Proceed with caution.**
EOF
)"
```

## 🔥 Emergency Procedures

### Hotfix Workflow (Production Issues)
```bash
# Critical production issue
git checkout main
git pull origin main
git checkout -b hotfix/critical-production-fix

# Make minimal fix
# ... fix implementation ...

git add .
git commit -m "hotfix: critical production issue fix

- Description of urgent fix
- Minimal change to resolve immediate issue
- Full testing in next development cycle

Priority: CRITICAL
Deployment: IMMEDIATE"

# Direct to main (emergency only)
gh pr create \
  --base main \
  --head hotfix/critical-production-fix \
  --title "🚨 HOTFIX: Critical Production Issue" \
  --body "Emergency fix for production issue. Minimal change, immediate deployment required."

# After merge and deployment, backport to develop
git checkout develop
git cherry-pick <hotfix-commit>
git push origin develop
```

### Epic Rollback (Epic Causes Issues)
```bash
# If epic integration causes issues
git checkout develop
git revert <epic-merge-commit>
git push origin develop

# Create epic rollback PR
gh pr create \
  --base main \
  --head develop \
  --title "revert: rollback epic implementation due to issues" \
  --body "Reverting epic changes due to discovered issues. Investigation in progress."
```

## 📊 Commit Message Standards

### Format
```
<type>(<scope>): <description>

[optional body]

Epic-ID: <epic-id>
Task: <task-id>
[Closes: <issue-id>]
```

### Types
- `feat`: New feature implementation
- `fix`: Bug fix
- `docs`: Documentation only changes
- `test`: Adding or updating tests
- `refactor`: Code change that neither fixes bug nor adds feature
- `epic`: Epic-level changes or documentation
- `release`: Release preparation
- `hotfix`: Emergency production fix
- `revert`: Reverting previous changes

### Examples
```bash
# Feature implementation
feat(api-keys): implement demo key auto-creation

- Add DEMO_MILMED_2025_500_PATIENTS auto-creation
- Implement usage tracking and limits
- Add database persistence

Epic-ID: EPIC-002
Task: 2.3 - Demo Key Implementation
Closes: EPIC-002-T2.3

# Epic completion
epic(dev-env): complete cross-platform development environment

- All 4 phases completed successfully
- Migration from Makefile to Task runner
- Platform support for Windows, macOS, Linux
- Comprehensive testing and documentation

Epic-ID: EPIC-001
Status: COMPLETED

# Production release
release: v2.2.0 - Multi-tenant API key management

- Epic EPIC-002 implementation complete
- Public demo key available
- CLI management tools included
- Full backward compatibility maintained

Epic-ID: EPIC-002
Risk: LOW
```

## 🔒 Branch Management Rules

### Branch Lifecycle
1. **Creation**: From `main` for epic, from epic for features
2. **Development**: Regular commits with epic context
3. **Integration**: Feature → Epic → Develop → Main
4. **Cleanup**: Delete after successful integration

### Branch Naming Standards
```bash
# Epic branches
epic/cross-platform-dev-env
epic/api-key-management
epic/production-scalability

# Feature branches
feature/cross-platform-dev-env/gitattributes-setup
feature/api-key-management/database-models
feature/production-scalability/connection-pooling

# Release branches
release/v2.1.0-cross-platform
release/v2.2.0-api-keys

# Hotfix branches
hotfix/critical-memory-leak
hotfix/security-vulnerability
```

## 📈 Success Metrics & Monitoring

### Git Workflow Metrics
- **Time to Integration**: Feature → Epic → Develop (target: <3 days)
- **Epic Completion Rate**: % of epics successfully integrated (target: 100%)
- **Production Incidents**: Issues caused by epic integration (target: 0)
- **Rollback Rate**: % of releases requiring rollback (target: <5%)

### Code Quality Gates
- All CI tests must pass before any branch integration
- Epic branches must maintain test coverage >80%
- Production releases require 2+ approvals
- Hotfixes require post-deployment review

## 🔄 Epic Coordination

### Multiple Epics in Development
```bash
# Epic dependencies management
epic/cross-platform-dev-env     # EPIC-001 (foundation - must complete first)
epic/api-key-management         # EPIC-002 (depends on EPIC-001)
epic/production-scalability     # EPIC-003 (parallel with EPIC-002)
epic/digitalocean-staging       # EPIC-004 (depends on EPIC-001, EPIC-003)
```

### Integration Order
1. **EPIC-001**: Cross-platform dev environment (blocks all others)
2. **EPIC-002 & EPIC-003**: Can develop in parallel
3. **EPIC-004**: Requires foundation from EPIC-001 and scalability from EPIC-003
4. **EPIC-005 & EPIC-006**: Can proceed after infrastructure is stable

## 📚 Documentation Integration

### Memory Updates
```bash
# Update progress after each epic completion
git add memory/epics/<epic-name>.md
git commit -m "docs(epic): update completion status and lessons learned

- Epic marked as completed
- Success criteria validation documented
- Lessons learned captured
- Next epic dependencies updated

Epic-ID: <epic-id>
Status: COMPLETED"
```

### CLAUDE.md Updates
```bash
# Update main documentation after significant milestones
git add CLAUDE.md memory/current-session.md
git commit -m "docs(project): update project status after epic completion

- CLAUDE.md updated with new capabilities
- Current session status updated
- Roadmap progress reflected
- Next session priorities defined

Milestone: <epic-name> Completion"
```

---

**This git workflow ensures production safety while enabling efficient epic development and integration. The key is isolation, testing, and gradual integration with multiple safety nets.**