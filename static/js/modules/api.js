/**
 * API Module - Handles all API communication
 */
export class APIClient {
    constructor(config = window.API_CONFIG) {
        this.config = config;
        this.baseURL = config.API_BASE_URL;
        this.headers = config.getHeaders();
    }

    /**
     * Fetch nationalities from the API
     */
    async fetchNationalities() {
        try {
            const response = await fetch(`${this.baseURL}/api/v1/configurations/reference/nationalities/`, {
                headers: this.headers
            });
            if (!response.ok) throw new Error('Failed to fetch nationalities');
            return await response.json();
        } catch (error) {
            console.error("Error fetching nationalities:", error);
            throw error;
        }
    }

    /**
     * Fetch existing configurations
     */
    async fetchConfigurations() {
        try {
            const response = await fetch(`${this.baseURL}/api/v1/configurations/`, {
                headers: this.headers
            });
            if (!response.ok) throw new Error('Failed to fetch configurations');
            return await response.json();
        } catch (error) {
            console.error("Error fetching configurations:", error);
            throw error;
        }
    }

    /**
     * Generate patients with configuration
     */
    async generatePatients(payload) {
        try {
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
        } catch (error) {
            console.error("Error generating patients:", error);
            throw error;
        }
    }

    /**
     * Get job status
     */
    async getJobStatus(jobId) {
        try {
            const response = await fetch(`${this.baseURL}/api/jobs/${jobId}`, {
                headers: this.headers
            });
            if (!response.ok) throw new Error('Failed to fetch job status');
            return await response.json();
        } catch (error) {
            console.error("Error fetching job status:", error);
            throw error;
        }
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