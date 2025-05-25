/**
 * API Module - Handles all API communication
 */
import { retryWithBackoff } from './utils.js';
import { clientCache } from './cache.js';

export class APIClient {
    constructor(config = window.API_CONFIG) {
        this.config = config;
        this.baseURL = config.API_BASE_URL;
        this.headers = config.getHeaders();
        this.maxRetries = 3;
        this.baseRetryDelay = 1000;
        this.nationalitiesCache = null;
        this.nationalitiesPromise = null;
        this.cache = clientCache;
    }

    /**
     * Fetch nationalities from the API with lazy loading and caching
     */
    async fetchNationalities() {
        const cacheKey = 'nationalities';
        
        // Check browser cache first
        const cached = this.cache.get(cacheKey);
        if (cached) {
            this.nationalitiesCache = cached;
            return cached;
        }
        
        // Return in-memory cache if available
        if (this.nationalitiesCache) {
            return this.nationalitiesCache;
        }
        
        // Return existing promise if request is in progress
        if (this.nationalitiesPromise) {
            return this.nationalitiesPromise;
        }
        
        // Create new request with retry logic
        this.nationalitiesPromise = retryWithBackoff(async () => {
            const response = await fetch(`${this.baseURL}/api/v1/configurations/reference/nationalities/`, {
                headers: this.headers
            });
            if (!response.ok) throw new Error('Failed to fetch nationalities');
            return await response.json();
        }, this.maxRetries, this.baseRetryDelay);
        
        try {
            this.nationalitiesCache = await this.nationalitiesPromise;
            // Cache in browser for 24 hours
            this.cache.set(cacheKey, this.nationalitiesCache, 86400000);
            return this.nationalitiesCache;
        } catch (error) {
            console.error("Error fetching nationalities:", error);
            throw error;
        } finally {
            this.nationalitiesPromise = null;
        }
    }

    /**
     * Fetch existing configurations with caching
     */
    async fetchConfigurations() {
        const cacheKey = 'configurations';
        
        // Check browser cache first (short TTL for configurations)
        const cached = this.cache.get(cacheKey);
        if (cached) {
            return cached;
        }
        
        return retryWithBackoff(async () => {
            const response = await fetch(`${this.baseURL}/api/v1/configurations/`, {
                headers: this.headers
            });
            if (!response.ok) throw new Error('Failed to fetch configurations');
            const data = await response.json();
            
            // Cache for 5 minutes
            this.cache.set(cacheKey, data, 300000);
            return data;
        }, this.maxRetries, this.baseRetryDelay);
    }

    /**
     * Generate patients with configuration and retry logic
     */
    async generatePatients(payload) {
        return retryWithBackoff(async () => {
            const response = await fetch(`${this.baseURL}/api/generate`, {
                method: 'POST',
                headers: this.headers,
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `Generation failed: ${response.statusText}`);
            }

            return await response.json();
        }, this.maxRetries, this.baseRetryDelay);
    }

    /**
     * Get job status with retry logic
     */
    async getJobStatus(jobId) {
        return retryWithBackoff(async () => {
            const response = await fetch(`${this.baseURL}/api/jobs/${jobId}`, {
                headers: this.headers
            });
            if (!response.ok) throw new Error('Failed to fetch job status');
            return await response.json();
        }, this.maxRetries, this.baseRetryDelay);
    }

    /**
     * Get job results
     */
    async getJobResults(jobId) {
        try {
            const response = await fetch(`${this.baseURL}/api/jobs/${jobId}/results`, {
                headers: this.headers
            });
            if (!response.ok) throw new Error('Failed to fetch job results');
            return await response.json();
        } catch (error) {
            console.error("Error fetching job results:", error);
            throw error;
        }
    }

    /**
     * Download job results
     */
    async downloadJobResults(jobId) {
        try {
            const response = await fetch(`${this.baseURL}/api/download/${jobId}`, {
                headers: this.headers
            });
            if (!response.ok) throw new Error('Failed to download results');
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `job_${jobId}_results.zip`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            console.error("Error downloading results:", error);
            throw error;
        }
    }
}

// Export singleton instance for backward compatibility
export const apiClient = new APIClient();