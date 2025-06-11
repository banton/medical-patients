# API Error Mapping Implementation Plan

## Overview
Plan to capture API validation errors from patient generation requests and map them back to specific JSON editors for better user experience and debugging.

## Current Situation Analysis

**What we have:**
- Two JSON editors: Battle Fronts & Injury Distribution  
- Client-side validation (basic format checking)
- API generation endpoint that can return detailed validation errors
- Generic error display in status section

**What we need:**
- Map API errors back to specific JSON editors
- Show validation errors directly in the accordion sections
- Maintain existing client-side validation as first-line defense

## Proposed Implementation Strategy

### Phase 1: Error Capture & Classification

```javascript
class ApiErrorMapper {
    constructor(app) {
        this.app = app;
        this.errorMappings = {
            // Map API error patterns to accordion sections
            'front_configs': 0,        // Battle Fronts editor
            'injury_distribution': 1,  // Injury Distribution editor
            'total_patients': 1,       // Also Injury Distribution
            'casualty_rate': 0,        // Battle Fronts
            'nationality_distribution': 0  // Battle Fronts
        };
    }
    
    processApiErrors(apiErrorResponse) {
        // Parse API error response and map to editors
        const editorErrors = { 0: [], 1: [] };
        
        // Extract errors from API response
        if (apiErrorResponse.detail) {
            this.mapErrorsToEditors(apiErrorResponse.detail, editorErrors);
        }
        
        return editorErrors;
    }
}
```

### Phase 2: Enhanced Error Display in Accordions

```javascript
// Extend accordion validation to show API errors
updateValidationUI(index, result, apiErrors = []) {
    const item = this.items[index];
    
    // Show client-side validation first
    if (!result.valid) {
        this.showValidationError(item, result.message, 'client');
        return;
    }
    
    // Show API errors if any
    if (apiErrors.length > 0) {
        this.showValidationError(item, apiErrors.join('; '), 'api');
        return;
    }
    
    // Show success state
    this.showValidationSuccess(item, result.message);
}

showValidationError(item, message, source) {
    item.status.className = 'accordion__status accordion__status--invalid';
    item.status.textContent = '✗';
    item.editor.classList.add('accordion__editor--invalid');
    
    // Enhanced error display with source indicator
    item.validation.className = 'accordion__validation accordion__validation--error';
    item.validation.innerHTML = `
        <div class="error-source">${source === 'api' ? '🌐 API Error' : '📝 Format Error'}</div>
        <div class="error-message">${message}</div>
    `;
}
```

### Phase 3: Generation Flow Enhancement

```javascript
// Modified handleGenerate method
async handleGenerate() {
    // ... existing code ...
    
    try {
        const response = await this.apiClient.generatePatients({
            configuration,
            output_formats: ['json', 'csv']
        });
        
        // Success path continues as normal
        this.currentJobId = response.job_id;
        // ...
        
    } catch (error) {
        console.error('Generation failed:', error);
        
        // NEW: Map API errors back to JSON editors
        if (error.status === 422) { // Validation error
            const editorErrors = this.errorMapper.processApiErrors(error);
            this.showApiValidationErrors(editorErrors);
        } else {
            // Generic error handling for other issues
            this.showError(`Generation failed: ${error.message}`);
        }
        
        this.resetUI();
    }
}

showApiValidationErrors(editorErrors) {
    // Clear any success states first
    this.accordion.clearAllValidation();
    
    // Apply API errors to specific editors
    Object.keys(editorErrors).forEach(editorIndex => {
        const errors = editorErrors[editorIndex];
        if (errors.length > 0) {
            this.accordion.showApiErrors(parseInt(editorIndex), errors);
        }
    });
    
    // Show summary in status
    this.showError('Configuration validation failed. Please check the highlighted sections.');
}
```

### Phase 4: Error Pattern Mapping

```javascript
mapErrorsToEditors(errorDetail, editorErrors) {
    // Handle different API error response formats
    
    if (Array.isArray(errorDetail)) {
        // Pydantic validation errors array
        errorDetail.forEach(error => {
            const field = error.loc ? error.loc.join('.') : '';
            const editorIndex = this.getEditorForField(field);
            if (editorIndex !== -1) {
                editorErrors[editorIndex].push(error.msg);
            }
        });
    } else if (typeof errorDetail === 'string') {
        // Simple string error - try to parse
        const editorIndex = this.detectEditorFromMessage(errorDetail);
        editorErrors[editorIndex].push(errorDetail);
    } else if (errorDetail.errors) {
        // Nested error structure
        this.mapErrorsToEditors(errorDetail.errors, editorErrors);
    }
}

getEditorForField(fieldPath) {
    // Map API field paths to editor indices
    for (const [pattern, editorIndex] of Object.entries(this.errorMappings)) {
        if (fieldPath.includes(pattern)) {
            return editorIndex;
        }
    }
    return 0; // Default to Battle Fronts if unclear
}
```

## UI/UX Enhancements

### Enhanced CSS for API Errors

```css
.accordion__validation--api-error {
    background: linear-gradient(90deg, rgba(239, 68, 68, 0.1) 0%, rgba(239, 68, 68, 0.05) 100%);
    border-left: 4px solid var(--error);
    padding: 0.75rem;
    border-radius: 0.375rem;
}

.error-source {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--error);
    margin-bottom: 0.25rem;
    text-transform: uppercase;
    letter-spacing: 0.025em;
}

.error-message {
    font-size: 0.875rem;
    line-height: 1.4;
    color: var(--error);
}

.accordion__editor--api-invalid {
    border-color: var(--error);
    background: rgba(239, 68, 68, 0.03);
    box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
}
```

## Integration Points

### 1. API Client Enhancement
```javascript
// Enhanced error handling in api.js
async generatePatients(configuration) {
    try {
        return await this.post('/generation/', configuration);
    } catch (error) {
        // Enhanced error object with structured details
        if (error.status === 422) {
            error.validationErrors = this.parseValidationErrors(error.detail);
        }
        throw error;
    }
}
```

### 2. Accordion Method Addition
```javascript
// New method in accordion.js
showApiErrors(editorIndex, errors) {
    const item = this.items[editorIndex];
    if (!item) return;
    
    // Mark as invalid with API error styling
    item.status.className = 'accordion__status accordion__status--invalid';
    item.status.textContent = '⚠';
    item.editor.classList.add('accordion__editor--api-invalid');
    
    // Show combined error message
    item.validation.className = 'accordion__validation accordion__validation--api-error';
    item.validation.innerHTML = `
        <div class="error-source">🌐 Server Validation Error</div>
        <div class="error-message">${errors.join('<br>')}</div>
    `;
    
    // Expand this section so user sees the error
    this.expand(editorIndex);
}
```

## Implementation Priority

1. **High Priority** - Basic error mapping and display
2. **Medium Priority** - Enhanced UI styling and error categorization  
3. **Low Priority** - Smart error field highlighting within JSON

## Benefits

- **Immediate Feedback**: Users see errors exactly where they occurred
- **Better Debugging**: Clear distinction between client and server validation
- **Improved UX**: No need to guess which JSON section has the problem  
- **Professional Feel**: Sophisticated error handling like modern web applications

## Technical Considerations

- **Error Response Parsing**: Need to handle various API error formats (Pydantic, FastAPI, custom)
- **Field Mapping**: Maintain mapping between API field paths and UI editor indices
- **State Management**: Clear previous errors when new validation runs
- **Performance**: Minimal impact on existing validation flow
- **Accessibility**: Ensure error messages are screen-reader friendly

This approach provides immediate, actionable feedback by showing API validation errors directly in the relevant JSON editor sections, making it much easier for users to identify and fix configuration issues.