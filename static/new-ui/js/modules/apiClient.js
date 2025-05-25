// API Client Module

export class APIClient {
    constructor() {
        this.baseUrl = window.location.origin;
        this.apiKey = 'your_secret_api_key_here'; // Should be configurable
        this.headers = {
            'Content-Type': 'application/json',
            'X-API-Key': this.apiKey
        };
    }

    async request(method, endpoint, data = null) {
        const options = {
            method,
            headers: this.headers
        };

        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(`${this.baseUrl}${endpoint}`, options);
        
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        return response.json();
    }

    // Configuration Templates
    async getTemplates() {
        return this.request('GET', '/api/v1/configurations/');
    }

    async getTemplate(templateId) {
        return this.request('GET', `/api/v1/configurations/${templateId}`);
    }

    async saveTemplate(config) {
        return this.request('POST', '/api/v1/configurations/', config);
    }

    // Reference Data
    async getNationalities() {
        // Reference endpoints don't require API key
        const response = await fetch(`${this.baseUrl}/api/v1/configurations/reference/nationalities/`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        const data = await response.json();
        // Convert to simple array of names for UI
        return data.map(item => item.name);
    }

    async getMedicalConditions() {
        const response = await fetch(`${this.baseUrl}/api/v1/configurations/reference/condition-types/`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return response.json();
    }

    // Patient Generation
    async startGeneration(config) {
        return this.request('POST', '/api/generate', config);
    }

    async getJobStatus(jobId) {
        return this.request('GET', `/api/jobs/${jobId}`);
    }

    async getJobs() {
        return this.request('GET', '/api/jobs/');
    }

    async cancelJob(jobId) {
        return this.request('POST', `/api/jobs/${jobId}/cancel`);
    }

    // Downloads
    async getDownloadUrl(jobId) {
        // Return the direct download URL
        return `${this.baseUrl}/api/downloads/job/${jobId}`;
    }

    // WebSocket for real-time updates (if implemented)
    connectWebSocket(jobId, onMessage) {
        const ws = new WebSocket(`ws://${window.location.host}/ws/jobs/${jobId}`);
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            onMessage(data);
        };
        
        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
        
        return ws;
    }
}