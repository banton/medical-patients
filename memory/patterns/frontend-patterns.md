# Reusable Patterns - Medical Patients Generator

## API Communication Pattern

### Fetch Wrapper with Error Handling
```javascript
class ApiClient {
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl;
        this.headers = {
            'Content-Type': 'application/json',
            'X-API-Key': apiKey
        };
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    ...this.headers,
                    ...options.headers
                }
            });

            if (!response.ok) {
                const error = await response.json();
                throw new ApiError(
                    error.error?.message || 'API request failed',
                    response.status,
                    error.error?.code
                );
            }

            return await response.json();
        } catch (error) {
            if (error instanceof ApiError) {
                throw error;
            }
            throw new ApiError('Network error', 0, 'NETWORK_ERROR');
        }
    }

    get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
}

class ApiError extends Error {
    constructor(message, status, code) {
        super(message);
        this.status = status;
        this.code = code;
    }
}
```

## Component Base Pattern

### Reusable Component Class
```javascript
class Component {
    constructor(elementId) {
        this.element = document.getElementById(elementId);
        if (!this.element) {
            throw new Error(`Element with id '${elementId}' not found`);
        }
        this.state = {};
        this.listeners = {};
    }

    setState(newState) {
        this.state = { ...this.state, ...newState };
        this.render();
    }

    on(event, callback) {
        if (!this.listeners[event]) {
            this.listeners[event] = [];
        }
        this.listeners[event].push(callback);
    }

    emit(event, data) {
        if (this.listeners[event]) {
            this.listeners[event].forEach(callback => callback(data));
        }
    }

    render() {
        // Override in subclass
    }

    destroy() {
        this.listeners = {};
        this.element.innerHTML = '';
    }
}
```

## Testing Patterns

### Mock API for Testing
```javascript
class MockApiClient {
    constructor() {
        this.responses = {};
        this.calls = [];
    }

    setResponse(endpoint, response, error = null) {
        this.responses[endpoint] = { response, error };
    }

    async request(endpoint, options = {}) {
        this.calls.push({ endpoint, options });
        
        const mock = this.responses[endpoint];
        if (!mock) {
            throw new Error(`No mock response for ${endpoint}`);
        }

        if (mock.error) {
            throw mock.error;
        }

        return mock.response;
    }

    get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    post(endpoint, data) {
        return this.request(endpoint, { method: 'POST', body: data });
    }

    getCalls(endpoint = null) {
        if (endpoint) {
            return this.calls.filter(call => call.endpoint === endpoint);
        }
        return this.calls;
    }

    reset() {
        this.responses = {};
        this.calls = [];
    }
}
```

### Test Setup Helper
```javascript
function setupTestDOM() {
    document.body.innerHTML = `
        <div id="test-container">
            <div id="test-element"></div>
        </div>
    `;
}

function cleanupTestDOM() {
    document.body.innerHTML = '';
}

// Jest setup
beforeEach(() => {
    setupTestDOM();
});

afterEach(() => {
    cleanupTestDOM();
});
```

## JSON Editor Pattern

### Syntax Highlighting and Validation
```javascript
class JsonEditor {
    constructor(element) {
        this.element = element;
        this.textarea = this.createTextarea();
        this.errorDisplay = this.createErrorDisplay();
        this.isValid = true;
        
        this.init();
    }

    init() {
        this.element.appendChild(this.textarea);
        this.element.appendChild(this.errorDisplay);
        
        this.textarea.addEventListener('input', () => this.validate());
        this.textarea.addEventListener('blur', () => this.format());
    }

    createTextarea() {
        const textarea = document.createElement('textarea');
        textarea.className = 'json-editor-textarea';
        textarea.spellcheck = false;
        return textarea;
    }

    createErrorDisplay() {
        const div = document.createElement('div');
        div.className = 'json-editor-error';
        div.style.display = 'none';
        return div;
    }

    validate() {
        try {
            const value = this.textarea.value.trim();
            if (value) {
                JSON.parse(value);
            }
            this.setError(null);
            this.isValid = true;
        } catch (error) {
            this.setError(error.message);
            this.isValid = false;
        }
    }

    format() {
        if (this.isValid && this.textarea.value.trim()) {
            try {
                const parsed = JSON.parse(this.textarea.value);
                this.textarea.value = JSON.stringify(parsed, null, 2);
            } catch (e) {
                // Ignore formatting errors
            }
        }
    }

    setError(message) {
        if (message) {
            this.errorDisplay.textContent = message;
            this.errorDisplay.style.display = 'block';
            this.textarea.classList.add('error');
        } else {
            this.errorDisplay.style.display = 'none';
            this.textarea.classList.remove('error');
        }
    }

    getValue() {
        if (!this.isValid) {
            throw new Error('Invalid JSON');
        }
        return this.textarea.value ? JSON.parse(this.textarea.value) : null;
    }

    setValue(value) {
        this.textarea.value = JSON.stringify(value, null, 2);
        this.validate();
    }
}
```

## Progress Tracking Pattern

### Polling with Exponential Backoff
```javascript
class JobPoller {
    constructor(apiClient, options = {}) {
        this.apiClient = apiClient;
        this.options = {
            initialDelay: 1000,
            maxDelay: 10000,
            backoffFactor: 1.5,
            maxAttempts: 100,
            ...options
        };
    }

    async poll(jobId, onProgress, onComplete, onError) {
        let delay = this.options.initialDelay;
        let attempts = 0;

        while (attempts < this.options.maxAttempts) {
            try {
                const status = await this.apiClient.get(`/api/jobs/${jobId}`);
                
                if (status.status === 'completed') {
                    onComplete(status);
                    return;
                } else if (status.status === 'failed') {
                    onError(new Error(status.error || 'Job failed'));
                    return;
                } else {
                    onProgress(status);
                }

                await this.sleep(delay);
                delay = Math.min(delay * this.options.backoffFactor, this.options.maxDelay);
                attempts++;
                
            } catch (error) {
                onError(error);
                return;
            }
        }

        onError(new Error('Polling timeout'));
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}
```

## State Management Pattern

### Simple State Store
```javascript
class StateStore {
    constructor(initialState = {}) {
        this.state = initialState;
        this.listeners = [];
    }

    getState() {
        return { ...this.state };
    }

    setState(updates) {
        const prevState = this.state;
        this.state = { ...this.state, ...updates };
        this.notify(prevState, this.state);
    }

    subscribe(listener) {
        this.listeners.push(listener);
        
        // Return unsubscribe function
        return () => {
            this.listeners = this.listeners.filter(l => l !== listener);
        };
    }

    notify(prevState, nextState) {
        this.listeners.forEach(listener => {
            listener(nextState, prevState);
        });
    }
}

// Usage Example
const appState = new StateStore({
    isGenerating: false,
    jobId: null,
    progress: 0,
    configurations: {
        demographics: null,
        fronts: null,
        injuries: null
    }
});

// Subscribe to changes
appState.subscribe((state, prevState) => {
    if (state.isGenerating !== prevState.isGenerating) {
        updateUI(state.isGenerating);
    }
});
```

## Error Handling Pattern

### User-Friendly Error Display
```javascript
class ErrorHandler {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.createErrorDisplay();
    }

    createErrorDisplay() {
        this.errorEl = document.createElement('div');
        this.errorEl.className = 'error-message';
        this.errorEl.style.display = 'none';
        
        const closeBtn = document.createElement('button');
        closeBtn.className = 'error-close';
        closeBtn.textContent = '×';
        closeBtn.onclick = () => this.hide();
        
        this.messageEl = document.createElement('p');
        
        this.errorEl.appendChild(closeBtn);
        this.errorEl.appendChild(this.messageEl);
        this.container.appendChild(this.errorEl);
    }

    show(error) {
        let message = 'An unexpected error occurred';
        
        if (error instanceof ApiError) {
            switch (error.code) {
                case 'VALIDATION_ERROR':
                    message = `Invalid input: ${error.message}`;
                    break;
                case 'GENERATION_ERROR':
                    message = `Generation failed: ${error.message}`;
                    break;
                case 'NETWORK_ERROR':
                    message = 'Network error. Please check your connection.';
                    break;
                default:
                    message = error.message;
            }
        } else if (error.message) {
            message = error.message;
        }

        this.messageEl.textContent = message;
        this.errorEl.style.display = 'block';
        
        // Auto-hide after 10 seconds
        setTimeout(() => this.hide(), 10000);
    }

    hide() {
        this.errorEl.style.display = 'none';
    }
}
```

---

*Created: Current Session*
*Purpose: Reusable patterns for consistent implementation*
