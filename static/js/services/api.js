/**
 * v1 API Client Service
 * Handles all communication with the standardized v1 backend API
 */

/* eslint no-console: "off" */

class ApiClient {
    constructor(baseUrl = '', apiKey = null) {
        this.baseUrl = baseUrl;
        // Use config API key if available, fallback to parameter or default
        this.apiKey = apiKey || (typeof window !== 'undefined' && window.config ? window.config.apiKey : 'your_secret_api_key_here');
        this.defaultHeaders = {
            'Content-Type': 'application/json',
            'X-API-Key': this.apiKey
        };
    }

    /**
     * Make authenticated HTTP request
     */
    async request(method, endpoint, data = null, options = {}) {
        const url = `${this.baseUrl}/api/v1${endpoint}`;
        const config = {
            method,
            headers: {
                ...this.defaultHeaders,
                ...options.headers
            },
            ...options
        };

        if (data && ['POST', 'PUT', 'PATCH'].includes(method.toUpperCase())) {
            config.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(url, config);

            // Handle non-JSON responses (like downloads)
            if (options.responseType === 'blob') {
                if (!response.ok) {
                    throw new ApiError(response.status, 'Download failed', await response.text());
                }
                return response.blob();
            }

            // Parse JSON response
            const result = await response.json();

            if (!response.ok) {
                throw new ApiError(response.status, result.error || 'Request failed', result.detail || result.message);
            }

            return result;
        } catch (error) {
            if (error instanceof ApiError) {
                throw error;
            }

            // Network or other errors
            throw new ApiError(0, 'Network Error', error.message);
        }
    }

    // HTTP method helpers
    async get(endpoint, options = {}) {
        return this.request('GET', endpoint, null, options);
    }

    async post(endpoint, data, options = {}) {
        return this.request('POST', endpoint, data, options);
    }

    async put(endpoint, data, options = {}) {
        return this.request('PUT', endpoint, data, options);
    }

    async delete(endpoint, options = {}) {
        return this.request('DELETE', endpoint, null, options);
    }

    // Generation API endpoints
    async generatePatients(configuration) {
        return this.post('/generation/', configuration);
    }

    // Job management endpoints
    async getJob(jobId) {
        return this.get(`/jobs/${jobId}`);
    }

    async listJobs() {
        return this.get('/jobs/');
    }

    async deleteJob(jobId) {
        return this.delete(`/jobs/${jobId}`);
    }

    // Download endpoints
    async downloadJobResults(jobId) {
        return this.get(`/downloads/${jobId}`, { responseType: 'blob' });
    }

    // Configuration endpoints
    async listConfigurations() {
        return this.get('/configurations/');
    }

    async createConfiguration(configuration) {
        return this.post('/configurations/', configuration);
    }

    async getConfiguration(configId) {
        return this.get(`/configurations/${configId}`);
    }

    async updateConfiguration(configId, configuration) {
        return this.put(`/configurations/${configId}`, configuration);
    }

    async deleteConfiguration(configId) {
        return this.delete(`/configurations/${configId}`);
    }

    // Reference data endpoints
    async getNationalities() {
        return this.get('/configurations/reference/nationalities/');
    }

    async getConditionTypes() {
        return this.get('/configurations/reference/condition-types/');
    }

    async getFacilityTypes() {
        return this.get('/configurations/reference/facility-types/');
    }

    async getStaticFronts() {
        return this.get('/configurations/reference/static-fronts/');
    }

    // Visualization endpoints
    async getDashboardData() {
        return this.get('/visualizations/dashboard-data');
    }

    // Utility methods
    async healthCheck() {
        try {
            const response = await fetch(`${this.baseUrl}/docs`);
            return response.ok;
        } catch {
            return false;
        }
    }

    async getApiDocumentation() {
        try {
            const response = await fetch(`${this.baseUrl}/docs`);
            return response.ok ? `${this.baseUrl}/docs` : null;
        } catch {
            return null;
        }
    }

    // Job polling utility
    async pollJobStatus(jobId, onProgress = null, timeoutMs = 300000) {
        const startTime = Date.now();
        const pollInterval = 2000; // 2 seconds

        return new Promise((resolve, reject) => {
            const poll = async () => {
                try {
                    if (Date.now() - startTime > timeoutMs) {
                        reject(new ApiError(408, 'Timeout', 'Job polling timed out'));
                        return;
                    }

                    const job = await this.getJob(jobId);

                    if (onProgress) {
                        onProgress(job);
                    }

                    if (job.status === 'completed') {
                        resolve(job);
                    } else if (job.status === 'failed') {
                        reject(new ApiError(500, 'Job Failed', job.error_message || 'Job processing failed'));
                    } else {
                        // Job still running, continue polling
                        setTimeout(poll, pollInterval);
                    }
                } catch (error) {
                    reject(error);
                }
            };

            poll();
        });
    }
}

/**
 * Custom API Error class
 */
class ApiError extends Error {
    constructor(status, error, detail = '') {
        super(`${error}: ${detail}`);
        this.name = 'ApiError';
        this.status = status;
        this.error = error;
        this.detail = detail;
        this.timestamp = new Date().toISOString();
    }

    isNetworkError() {
        return this.status === 0;
    }

    isAuthError() {
        return this.status === 401 || this.status === 403;
    }

    isNotFound() {
        return this.status === 404;
    }

    isValidationError() {
        return this.status === 422;
    }

    isServerError() {
        return this.status >= 500;
    }

    toJSON() {
        return {
            name: this.name,
            message: this.message,
            status: this.status,
            error: this.error,
            detail: this.detail,
            timestamp: this.timestamp
        };
    }
}

// Create global API client instance (after config is loaded)
let apiClient;

// Initialize API client when DOM is ready
if (typeof window !== 'undefined') {
    window.addEventListener('DOMContentLoaded', () => {
        apiClient = new ApiClient();
        window.apiClient = apiClient;
        console.log('🔌 v1 API Client initialized with environment config');
    });
}

// Export for modules and global use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ApiClient, ApiError, apiClient };
}

if (typeof window !== 'undefined') {
    window.ApiClient = ApiClient;
    window.ApiError = ApiError;
    window.apiClient = apiClient;
}

// console.log('🔌 v1 API Client loaded and ready');
