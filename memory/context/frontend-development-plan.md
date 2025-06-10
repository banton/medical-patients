# Frontend Development Plan - v1 API Integration

## Feature Branch: `feature/frontend/v1-api-integration`

**Created**: Current session  
**Base**: develop branch (post API standardization success)  
**Goal**: Implement modern frontend with v1 API integration

## Current State Analysis

### Existing Frontend
- **File**: `static/index.html` - Basic HTML page with simple styling
- **JavaScript**: `static/js/simple-app.js` - Contains default configuration and basic functionality
- **API Integration**: Uses old endpoints, needs v1 API migration
- **UI**: Static layout, no interactive JSON editors

### Target Architecture (From UI Specification)
- **Single Page Application**: Vanilla JS (no framework complexity)
- **API Banner**: Always visible promotion for programmatic usage
- **Vertical Accordion**: JSON editors (one visible at a time)
- **Load Previous**: Database-backed configuration history
- **Progress UI**: Fun messages with minimum 2-second display
- **Error Handling**: Developer-friendly reporting with retry logic
- **Download**: Generated file access

## Implementation Strategy (TDD Approach)

### Phase 1: Foundation & API Banner ⏳
1. **Test**: API banner visibility and linking
2. **Implement**: Static banner component with proper styling
3. **Test**: Banner integration with existing layout
4. **Implement**: Update CSS with design system colors

### Phase 2: Accordion Structure 📋
1. **Test**: Accordion component behavior (expand/collapse)
2. **Implement**: JavaScript accordion with state management
3. **Test**: Only one section expanded at a time
4. **Implement**: Section validation status indicators

### Phase 3: JSON Editors 📝
1. **Test**: JSON editor initialization and validation
2. **Implement**: Textarea-based editors with syntax highlighting
3. **Test**: Real-time validation and error display
4. **Implement**: Nationality code validation against API

### Phase 4: API Integration 🔌
1. **Test**: v1 API endpoint calls with proper authentication
2. **Implement**: Update all API calls to v1 endpoints
3. **Test**: Error handling for API failures
4. **Implement**: Response model parsing

### Phase 5: Load Previous Feature 💾
1. **Test**: Configuration history retrieval
2. **Implement**: Modal UI for previous generations
3. **Test**: Configuration loading and editor population
4. **Implement**: Database integration

### Phase 6: Progress & UX Polish ✨
1. **Test**: Progress animation and message rotation
2. **Implement**: Enhanced progress UI with fun messages
3. **Test**: Download functionality
4. **Implement**: Final UX polish and responsive design

## Technical Requirements

### API Endpoints (v1)
- `GET /api/v1/configurations/` - List configurations
- `POST /api/v1/generation/` - Generate patients
- `GET /api/v1/jobs/{job_id}` - Check job status
- `GET /api/v1/downloads/{job_id}` - Download results
- `GET /api/v1/configurations/reference/nationalities/` - Valid nationality codes

### JavaScript Modules
```
static/js/
├── app.js              # Main application controller
├── components/
│   ├── api-banner.js   # API promotion banner
│   ├── accordion.js    # Configuration accordion
│   ├── json-editor.js  # JSON editing with validation
│   ├── progress.js     # Progress display and messaging
│   └── modal.js        # Load previous modal
├── services/
│   ├── api.js          # v1 API client
│   ├── validator.js    # JSON and nationality validation
│   └── storage.js      # Local storage utilities
└── utils/
    ├── dom.js          # DOM utilities
    └── events.js       # Event handling helpers
```

### CSS Architecture
```
static/css/
├── variables.css       # Design system colors and spacing
├── components/
│   ├── banner.css      # API banner styling
│   ├── accordion.css   # Accordion component
│   ├── editor.css      # JSON editor styling
│   ├── progress.css    # Progress animation
│   └── modal.css       # Modal dialogs
└── layout.css          # Main layout and responsive design
```

### Testing Strategy
1. **Unit Tests**: Individual component functionality
2. **Integration Tests**: API communication and data flow
3. **E2E Tests**: Complete user workflows
4. **Visual Tests**: UI component rendering

## Development Checklist

### Phase 1 Tasks ⏳
- [ ] Create CSS design system with color variables
- [ ] Implement API banner component (static)
- [ ] Write tests for banner visibility and linking
- [ ] Update HTML structure for new layout

### Future Phases 📅
- [ ] Accordion implementation with state management
- [ ] JSON editor with real-time validation
- [ ] v1 API integration and authentication
- [ ] Load previous configurations feature
- [ ] Progress animation and fun messaging
- [ ] Error handling and retry logic
- [ ] Download functionality
- [ ] Responsive design and polish
- [ ] Comprehensive test coverage

## Success Metrics

### Functional Requirements ✅
- All v1 API endpoints properly integrated
- Real-time JSON validation working
- Load previous configurations functional
- Progress display minimum 2 seconds
- Error retry with developer-friendly reporting

### Performance Targets 🎯
- Page load < 1 second
- Instant JSON validation feedback
- Smooth accordion animations
- Responsive design down to mobile

### User Experience Goals 🎨
- Intuitive configuration management
- Clear validation feedback
- Professional military tool appearance
- API promotion without being intrusive

---

**Next Action**: Begin Phase 1 with TDD approach - API banner component implementation and testing