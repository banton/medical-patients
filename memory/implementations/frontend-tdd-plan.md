# Frontend Development Plan - TDD Approach

## Overview
Create a simple, functional frontend using Vanilla JavaScript with Test-Driven Development.

## Requirements Summary
1. Single page application
2. Edit 3 JSON configuration files
3. Generate patients with button
4. Show progress during generation
5. Display results and download links
6. No framework complexity

## Architecture Design

### File Structure
```
static/
├── index.html          # Main HTML file
├── css/
│   └── app.css        # Simple styling
├── js/
│   ├── app.js         # Main application
│   ├── components/
│   │   ├── api-banner.js     # API promotion banner
│   │   ├── accordion.js      # Accordion container
│   │   ├── json-editor.js    # JSON editor component
│   │   ├── generator.js      # Generation control
│   │   ├── progress.js       # Progress display
│   │   ├── history-modal.js  # Previous generations
│   │   └── error-modal.js    # Error reporting
│   ├── services/
│   │   ├── api.js           # API communication
│   │   └── validator.js     # JSON & nationality validation
│   └── utils/
│       └── messages.js      # Fun progress messages
└── tests/
    ├── unit/          # Component tests
    └── e2e/           # End-to-end tests
```

## Component Specifications

### 1. JSON Editor Component
```javascript
// Responsibilities:
// - Load JSON from file
// - Validate JSON syntax
// - Highlight syntax errors
// - Save changes to memory
// - Reset to defaults

class JsonEditor {
    constructor(elementId, configType) {
        this.element = document.getElementById(elementId);
        this.configType = configType; // 'demographics' | 'fronts' | 'injuries'
        this.originalData = null;
        this.currentData = null;
    }
    
    async load() { /* Load from API */ }
    validate() { /* Validate JSON */ }
    save() { /* Save to memory */ }
    reset() { /* Reset to original */ }
    getChanges() { /* Get current data */ }
}
```

### 2. Generator Component
```javascript
// Responsibilities:
// - Collect configuration from editors
// - Start generation job
// - Poll for status
// - Handle errors

class Generator {
    constructor(editors, progressComponent) {
        this.editors = editors;
        this.progress = progressComponent;
        this.jobId = null;
    }
    
    async generate() { /* Start generation */ }
    async pollStatus() { /* Check job status */ }
    handleError(error) { /* Display errors */ }
}
```

### 3. Progress Component
```javascript
// Responsibilities:
// - Show/hide progress
// - Update progress bar
// - Display status messages
// - Show phase information

class Progress {
    constructor(elementId) {
        this.element = document.getElementById(elementId);
        this.progressBar = null;
        this.statusText = null;
    }
    
    show() { /* Show progress */ }
    hide() { /* Hide progress */ }
    update(percent, message) { /* Update display */ }
}
```

### 4. API Service
```javascript
// Responsibilities:
// - Handle all API calls
// - Add authentication
// - Parse responses
// - Handle errors

class ApiService {
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl;
        this.apiKey = apiKey;
    }
    
    async getConfiguration(type) { /* GET config */ }
    async generatePatients(config) { /* POST generate */ }
    async getJobStatus(jobId) { /* GET job status */ }
    async downloadResults(jobId) { /* GET download */ }
}
```

## TDD Test Plan

### Phase 1: Unit Tests (Create First)

#### JSON Editor Tests
```javascript
describe('JsonEditor', () => {
    test('should initialize with element and type', () => {});
    test('should load JSON data from API', () => {});
    test('should validate correct JSON', () => {});
    test('should detect invalid JSON', () => {});
    test('should highlight syntax errors', () => {});
    test('should save changes to memory', () => {});
    test('should reset to original data', () => {});
    test('should track changes', () => {});
});
```

#### Generator Tests
```javascript
describe('Generator', () => {
    test('should collect data from all editors', () => {});
    test('should start generation job', () => {});
    test('should poll for job status', () => {});
    test('should update progress during generation', () => {});
    test('should handle successful completion', () => {});
    test('should handle generation errors', () => {});
});
```

#### API Service Tests
```javascript
describe('ApiService', () => {
    test('should add API key to requests', () => {});
    test('should handle successful responses', () => {});
    test('should handle error responses', () => {});
    test('should parse JSON responses', () => {});
    test('should handle network errors', () => {});
});
```

### Phase 2: Integration Tests

```javascript
describe('Frontend Integration', () => {
    test('should load all configurations on startup', () => {});
    test('should enable generate button when valid', () => {});
    test('should disable UI during generation', () => {});
    test('should show progress updates', () => {});
    test('should display download links on completion', () => {});
});
```

### Phase 3: E2E Tests

```javascript
describe('E2E Patient Generation', () => {
    test('user can edit configuration and generate patients', async () => {
        // 1. Load page
        // 2. Edit demographics.json
        // 3. Click generate
        // 4. Wait for completion
        // 5. Verify download link
    });
    
    test('user sees errors for invalid JSON', async () => {
        // 1. Load page
        // 2. Enter invalid JSON
        // 3. Try to generate
        // 4. Verify error message
    });
});
```

## Implementation Steps

### Step 1: Setup Testing Environment
1. Configure Jest for browser testing
2. Setup test HTML fixtures
3. Create mock API responses
4. Write first failing test

### Step 2: Create HTML Structure
```html
<!DOCTYPE html>
<html>
<head>
    <title>Military Patient Generator</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="/static/css/app.css">
</head>
<body>
    <!-- API Banner -->
    <div id="api-banner" class="api-banner">
        <span class="api-banner-text">
            🔧 API Available! This tool can also be used programmatically. 
            Integrate patient generation into your systems via our REST API.
        </span>
        <a href="/docs" class="api-banner-link">View API Documentation →</a>
    </div>

    <div class="container">
        <header>
            <h1>Military Patient Generator</h1>
            <div class="controls">
                <button id="load-previous-btn" class="secondary-button">
                    Load Previous
                </button>
                <button id="generate-btn" class="primary-button">
                    Generate Patients
                </button>
                <button id="reset-btn" class="secondary-button">
                    Reset All
                </button>
            </div>
        </header>
        
        <!-- Configuration Accordion -->
        <div id="config-accordion" class="accordion">
            <div class="accordion-item" data-config="demographics">
                <div class="accordion-header">
                    <span class="accordion-arrow">▼</span>
                    <span>Demographics Configuration</span>
                    <span class="validation-status" id="demographics-status">✓</span>
                </div>
                <div class="accordion-content">
                    <div id="demographics-editor" class="json-editor"></div>
                </div>
            </div>
            
            <div class="accordion-item" data-config="fronts">
                <div class="accordion-header">
                    <span class="accordion-arrow">▶</span>
                    <span>Battle Fronts Configuration</span>
                    <span class="validation-status" id="fronts-status">✓</span>
                </div>
                <div class="accordion-content" style="display: none;">
                    <div id="fronts-editor" class="json-editor"></div>
                </div>
            </div>
            
            <div class="accordion-item" data-config="injuries">
                <div class="accordion-header">
                    <span class="accordion-arrow">▶</span>
                    <span>Injury Distribution</span>
                    <span class="validation-status" id="injuries-status">✓</span>
                </div>
                <div class="accordion-content" style="display: none;">
                    <div id="injuries-editor" class="json-editor"></div>
                </div>
            </div>
        </div>
        
        <!-- Progress Section -->
        <div id="progress-section" class="progress-section" style="display: none;">
            <h3>Generation Progress</h3>
            <div class="progress-bar">
                <div id="progress-fill" class="progress-fill"></div>
            </div>
            <p id="progress-message"></p>
            <p id="progress-detail"></p>
        </div>
        
        <!-- Results Section -->
        <div id="results-section" class="results-section" style="display: none;">
            <h3>Generation Complete</h3>
            <div id="results-summary"></div>
            <div id="download-links"></div>
        </div>
    </div>
    
    <!-- Modals -->
    <div id="history-modal" class="modal" style="display: none;"></div>
    <div id="error-modal" class="modal" style="display: none;"></div>
    
    <script src="/static/js/app.js" type="module"></script>
</body>
</html>
```

### Step 3: Implement Components (TDD)
1. Write test for component
2. Create minimal component to pass test
3. Refactor and improve
4. Repeat for next feature

### Step 4: CSS Styling (Minimal)
```css
/* Keep it simple and functional */
.container { max-width: 1200px; margin: 0 auto; }
.json-editor { 
    font-family: monospace; 
    border: 1px solid #ddd;
    min-height: 300px;
}
.progress-bar { 
    background: #f0f0f0; 
    height: 20px; 
    border-radius: 4px; 
}
.progress-fill { 
    background: #4CAF50; 
    height: 100%; 
    transition: width 0.3s; 
}
```

## Testing Tools

### Jest Configuration
```javascript
// jest.config.js
module.exports = {
    testEnvironment: 'jsdom',
    setupFilesAfterEnv: ['<rootDir>/setupTests.js'],
    testMatch: ['**/tests/**/*.test.js'],
    collectCoverageFrom: [
        'static/js/**/*.js',
        '!static/js/vendor/**'
    ]
};
```

### Test Utilities
```javascript
// tests/utils/test-helpers.js
export function createMockApi() {
    return {
        getConfiguration: jest.fn(),
        generatePatients: jest.fn(),
        getJobStatus: jest.fn(),
        downloadResults: jest.fn()
    };
}

export function waitForElement(selector, timeout = 1000) {
    // Helper to wait for elements in E2E tests
}
```

## Success Criteria

1. **All tests pass** - 100% of test suite
2. **Test coverage** - Minimum 80% code coverage
3. **No console errors** - Clean browser console
4. **Accessible** - Keyboard navigation works
5. **Responsive** - Works on different screen sizes
6. **Fast** - Page loads in < 1 second
7. **Intuitive** - No user manual needed

## Development Workflow

1. **Start with test** - Write failing test first
2. **Implement minimum** - Just enough to pass
3. **Refactor** - Improve without breaking tests
4. **Document** - Add JSDoc comments
5. **Commit** - Small, focused commits

---

*Created: Current Session*
*Status: Ready for TDD Implementation*
