# DigitalOcean Deployment Information

## App Details
- **App ID**: `e2b6df5c-3cb9-48d9-811f-9330754bb642`
- **App Name**: `medical-patients-generator-redis`
- **Region**: `nyc`
- **Platform**: DigitalOcean App Platform

## Deployment History
- **Target Rollback Deployment**: `1041e031-2f0a-47ab-9729-30f7d239c6c6`
- **Status**: SUPERSEDED (Created: 2025-06-14 09:05:12Z)
- **Reason**: Rolling back from ERROR deployment to last stable version

## Rollback Information - EXECUTED
- **Rollback Initiated**: ✅ SUCCESSFUL
- **New Deployment ID**: `3a6b998c-41d2-4cdf-adcb-b0c77ee7bee1`
- **Rollback Target**: `1041e031-2f0a-47ab-9729-30f7d239c6c6`
- **Status**: PENDING_BUILD (deployment in progress)
- **Initiated At**: 2025-06-14T09:49:23Z
- **Commit Hash**: `a9527646c0fcf2f4439f2e1e1f46a9253cae778c`

### Rollback Details
- **From**: ERROR deployment `ab9e7e7a-5524-4ec8-9e72-ad2d8e4503e1`
- **To**: SUPERSEDED deployment `1041e031-2f0a-47ab-9729-30f7d239c6c6`
- **Components Being Restored**:
  - API service (Python FastAPI)
  - Redis service (7-alpine)
  - Frontend static site
  - PostgreSQL database (unchanged)

### Next Steps
- Monitor deployment progress
- Once deployment completes, commit rollback with `commit_app_rollback`
- Test application functionality at https://milmed.tech

## MCP Tools Available
- `mcp__digitalocean-mcp-local__list_deployments` - List deployment history
- `mcp__digitalocean-mcp-local__validate_app_rollback` - Validate rollback safety
- `mcp__digitalocean-mcp-local__rollback_app` - Execute rollback
- `mcp__digitalocean-mcp-local__commit_app_rollback` - Make rollback permanent
- `mcp__digitalocean-mcp-local__revert_app_rollback` - Undo rollback

## Notes
- Always validate rollback before executing
- Rollbacks pin the app until committed or reverted
- Document all rollback operations for future reference

---
*Last Updated: Documented app ID and target deployment for rollback operations*