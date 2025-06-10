/**
 * API Client Tests
 * Testing the v1 API client service integration
 */

// Import test framework
const { TestFramework, assert } = window.TestFramework || {};

if (!TestFramework) {
    console.error('Test framework not loaded. Please include banner.test.js first.');
}

// Mock fetch for testing
let originalFetch;
let mockFetch;

function setupMockFetch() {
    originalFetch = window.fetch;
    mockFetch = {
        calls: [],
        responses: [],
        
        setup(responses) {
            this.responses = responses;
            this.calls = [];
        },
        
        mock: async function(url, options) {
            mockFetch.calls.push({ url, options });
            
            const response = mockFetch.responses.shift() || {
                ok: true,
                status: 200,
                json: async () => ({ success: true })
            };
            
            return {
                ok: response.ok,
                status: response.status,
                json: async () => response.json || {},
                text: async () => response.text || '',
                blob: async () => response.blob || new Blob()
            };
        }
    };
    
    window.fetch = mockFetch.mock;
}

function teardownMockFetch() {
    window.fetch = originalFetch;
}

// API Client Tests
TestFramework.test('ApiClient should initialize with correct defaults', () => {
    const client = new ApiClient();
    
    assert(client.baseUrl === '', 'Base URL should default to empty string');
    assert(client.apiKey === 'your_secret_api_key_here', 'API key should have default value');
    assert(client.defaultHeaders['Content-Type'] === 'application/json', 'Should have JSON content type');
    assert(client.defaultHeaders['X-API-Key'] === client.apiKey, 'Should include API key in headers');
});

TestFramework.test('ApiClient should construct proper URLs', async () => {
    setupMockFetch();
    mockFetch.setup([{ ok: true, status: 200, json: { success: true } }]);
    
    const client = new ApiClient('http://localhost:8001');
    await client.get('/test');
    
    const call = mockFetch.calls[0];
    assert(call.url === 'http://localhost:8001/api/v1/test', 'Should construct proper v1 API URL');
    
    teardownMockFetch();
});

TestFramework.test('ApiClient should include authentication headers', async () => {
    setupMockFetch();
    mockFetch.setup([{ ok: true, status: 200, json: { success: true } }]);
    
    const client = new ApiClient('', 'test-api-key');
    await client.get('/test');
    
    const call = mockFetch.calls[0];
    assert(call.options.headers['X-API-Key'] === 'test-api-key', 'Should include API key');
    assert(call.options.headers['Content-Type'] === 'application/json', 'Should include content type');
    
    teardownMockFetch();
});

TestFramework.test('ApiClient should handle successful responses', async () => {
    setupMockFetch();
    mockFetch.setup([{ 
        ok: true, 
        status: 200, 
        json: { data: 'test', message: 'success' } 
    }]);
    
    const client = new ApiClient();
    const result = await client.get('/test');
    
    assert(result.data === 'test', 'Should return parsed JSON data');
    assert(result.message === 'success', 'Should include all response fields');
    
    teardownMockFetch();
});

TestFramework.test('ApiClient should handle API errors', async () => {
    setupMockFetch();
    mockFetch.setup([{ 
        ok: false, 
        status: 422, 
        json: { 
            error: 'Validation Error', 
            detail: 'Invalid input data',
            timestamp: '2024-01-01T00:00:00Z'
        } 
    }]);
    
    const client = new ApiClient();
    
    try {
        await client.get('/test');
        assert(false, 'Should have thrown an error');
    } catch (error) {
        assert(error instanceof ApiError, 'Should throw ApiError');
        assert(error.status === 422, 'Should preserve status code');
        assert(error.error === 'Validation Error', 'Should include error type');
        assert(error.detail === 'Invalid input data', 'Should include error detail');
    }
    
    teardownMockFetch();
});

TestFramework.test('ApiClient should handle network errors', async () => {
    setupMockFetch();
    window.fetch = async () => {
        throw new Error('Network error');
    };
    
    const client = new ApiClient();
    
    try {
        await client.get('/test');
        assert(false, 'Should have thrown an error');
    } catch (error) {
        assert(error instanceof ApiError, 'Should throw ApiError');
        assert(error.status === 0, 'Network errors should have status 0');
        assert(error.error === 'Network Error', 'Should identify as network error');
    }
    
    teardownMockFetch();
});

TestFramework.test('ApiClient should send POST data correctly', async () => {
    setupMockFetch();
    mockFetch.setup([{ ok: true, status: 201, json: { id: '123' } }]);
    
    const client = new ApiClient();
    const testData = { name: 'test', value: 42 };
    
    await client.post('/test', testData);
    
    const call = mockFetch.calls[0];
    assert(call.options.method === 'POST', 'Should use POST method');
    assert(call.options.body === JSON.stringify(testData), 'Should serialize data as JSON');
    
    teardownMockFetch();
});

TestFramework.test('ApiClient generation endpoint should work', async () => {
    setupMockFetch();
    mockFetch.setup([{ 
        ok: true, 
        status: 201, 
        json: { 
            job_id: 'job-123', 
            status: 'pending',
            message: 'Generation started'
        } 
    }]);
    
    const client = new ApiClient();
    const config = {
        name: 'Test Generation',
        total_patients: 100,
        injury_distribution: { Disease: 0.5, 'Non-Battle Injury': 0.3, 'Battle Injury': 0.2 }
    };
    
    const result = await client.generatePatients(config);
    
    assert(result.job_id === 'job-123', 'Should return job ID');
    assert(result.status === 'pending', 'Should return job status');
    
    const call = mockFetch.calls[0];
    assert(call.url.endsWith('/api/v1/generation/'), 'Should call generation endpoint');
    
    teardownMockFetch();
});

TestFramework.test('ApiClient job polling should work', async () => {
    setupMockFetch();
    // First call: running, second call: completed
    mockFetch.setup([
        { ok: true, status: 200, json: { job_id: 'job-123', status: 'running', progress: 50 } },
        { ok: true, status: 200, json: { job_id: 'job-123', status: 'completed', progress: 100 } }
    ]);
    
    const client = new ApiClient();
    let progressCalls = 0;
    
    const result = await client.pollJobStatus('job-123', (job) => {
        progressCalls++;
        console.log(`Job progress: ${job.progress}%`);
    });
    
    assert(result.status === 'completed', 'Should resolve when job completes');
    assert(progressCalls >= 1, 'Should call progress callback');
    assert(mockFetch.calls.length >= 2, 'Should make multiple polling requests');
    
    teardownMockFetch();
});

TestFramework.test('ApiClient should handle blob responses for downloads', async () => {
    setupMockFetch();
    const testBlob = new Blob(['test data'], { type: 'application/zip' });
    mockFetch.setup([{ ok: true, status: 200, blob: testBlob }]);
    
    const client = new ApiClient();
    const result = await client.downloadJobResults('job-123');
    
    assert(result instanceof Blob, 'Should return Blob for download');
    
    const call = mockFetch.calls[0];
    assert(call.url.endsWith('/api/v1/downloads/job-123'), 'Should call download endpoint');
    
    teardownMockFetch();
});

TestFramework.test('ApiError should provide utility methods', () => {
    const networkError = new ApiError(0, 'Network Error', 'Connection failed');
    const authError = new ApiError(401, 'Unauthorized', 'Invalid API key');
    const notFoundError = new ApiError(404, 'Not Found', 'Resource not found');
    const validationError = new ApiError(422, 'Validation Error', 'Invalid data');
    const serverError = new ApiError(500, 'Internal Server Error', 'Server crashed');
    
    assert(networkError.isNetworkError(), 'Should identify network errors');
    assert(authError.isAuthError(), 'Should identify auth errors');
    assert(notFoundError.isNotFound(), 'Should identify not found errors');
    assert(validationError.isValidationError(), 'Should identify validation errors');
    assert(serverError.isServerError(), 'Should identify server errors');
    
    const errorJson = authError.toJSON();
    assert(errorJson.status === 401, 'Should serialize status');
    assert(errorJson.error === 'Unauthorized', 'Should serialize error type');
});

TestFramework.test('Global API client should be available', () => {
    assert(typeof window.apiClient !== 'undefined', 'Global apiClient should be available');
    assert(window.apiClient instanceof ApiClient, 'Should be ApiClient instance');
    assert(typeof window.ApiError !== 'undefined', 'ApiError should be available globally');
});

console.log('🧪 API client tests loaded. Run TestFramework.runAll() to execute.');