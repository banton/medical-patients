# Feature Backlog

This document tracks features that have been partially implemented or planned but need further specification and development.

## UI Features

### 1. Quick Start Templates
**Status**: UI hidden, backend functional  
**Location**: `static/new-ui/index.html` (commented out)  
**Description**: Quick Start button that shows pre-configured templates for common scenarios

**What exists**:
- Template modal with built-in templates (NATO Exercise, Training, Humanitarian, Large Scale)
- Template loading functionality
- Click handlers and UI styling

**What needs specification**:
- Better template preview with more details
- Template categories/filtering
- Template search functionality
- Recent/favorite templates
- Template sharing between users
- Template versioning

### 2. Job Results Viewer
**Status**: UI hidden, backend functional  
**Location**: `static/new-ui/js/modules/uiComponents.js` (commented out)  
**Description**: View button to preview generated patient data without downloading

**What exists**:
- View button in job cards
- Job completion with file paths
- Basic visualization dashboard at `/static/visualizations.html`

**What needs specification**:
- In-app patient data viewer
- Summary statistics display
- Patient search/filter capabilities
- Export selected patients
- Data visualization charts
- FHIR bundle viewer
- Integration with existing visualization dashboard

## Backend Features

### 3. Real-time Progress Updates
**Status**: Polling-based, WebSocket planned  
**Location**: `src/api/v1/routers/generation.py`, `static/new-ui/js/modules/jobManager.js`  
**Description**: Replace polling with WebSocket for real-time updates

**What exists**:
- Progress callback system
- Job status updates with progress details
- Adaptive polling (5s active, 30s idle)

**What needs specification**:
- WebSocket endpoint design
- Fallback mechanism for environments without WebSocket
- Progress event streaming
- Connection management
- Error recovery

### 4. Batch Operations
**Status**: Planned  
**Description**: Select and operate on multiple jobs at once

**What needs specification**:
- Multi-select UI for jobs
- Bulk download as single archive
- Bulk delete with confirmation
- Bulk cancel running jobs
- Job grouping/tagging

### 5. Configuration Validation API
**Status**: Basic validation exists  
**Location**: `src/api/v1/routers/configurations.py`  
**Description**: Enhanced validation with detailed feedback

**What exists**:
- Basic field validation
- Frontend ValidationManager

**What needs specification**:
- Semantic validation (e.g., facility capacity vs patient count)
- Warning vs error severity
- Validation rule customization
- Cross-field dependency validation

## System Features

### 6. Audit Logging
**Status**: Planned  
**Description**: Track all generation activities for compliance

**What needs specification**:
- What events to log
- Log retention policy
- Log format and storage
- User activity tracking
- Export capabilities

### 7. Performance Monitoring
**Status**: Planned  
**Description**: Track system performance and generation metrics

**What needs specification**:
- Metrics to collect
- Dashboard design
- Alert thresholds
- Historical trends
- Resource usage tracking

### 8. User Preferences
**Status**: Planned  
**Description**: Save user preferences and settings

**What needs specification**:
- What preferences to save
- Storage mechanism (local vs server)
- Default configurations per user
- UI theme preferences
- Notification preferences

## How to Use This Backlog

1. **Adding Items**: When hiding or deferring a feature, add it here with:
   - Current status
   - File locations
   - What already exists
   - What needs to be specified

2. **Converting to Tickets**: When ready to implement:
   - Create detailed specification
   - Break down into implementation tasks
   - Move to appropriate epic in `refactoring-epics-and-tickets.md`
   - Remove from this backlog

3. **Priority Guidelines**:
   - User-requested features: High
   - Performance improvements: Medium
   - Nice-to-have enhancements: Low