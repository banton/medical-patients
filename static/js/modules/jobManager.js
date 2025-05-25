/**
 * Job Management Module - Handles job polling and status updates
 */
import { apiClient } from './api.js';
import { eventBus, Events } from './events.js';
import { uiManager } from './ui.js';

export class JobManager {
    constructor() {
        this.activeJobs = new Map();
        this.pollingIntervals = new Map();
        this.POLLING_INTERVAL = 1000; // 1 second
    }

    /**
     * Create a new job from generation response
     */
    async createJob(jobData) {
        const jobId = jobData.job_id;
        
        // Store job info
        this.activeJobs.set(jobId, {
            id: jobId,
            status: jobData.status,
            createdAt: new Date(),
            progress: 0
        });
        
        // Create job card in UI
        uiManager.createJobCard(jobId);
        
        // Start polling
        this.startPolling(jobId);
        
        // Emit event
        eventBus.emit(Events.JOB_CREATED, { jobId, jobData });
        
        return jobId;
    }

    /**
     * Start polling for job status
     */
    startPolling(jobId) {
        if (this.pollingIntervals.has(jobId)) {
            return; // Already polling
        }

        const interval = setInterval(async () => {
            try {
                const status = await apiClient.getJobStatus(jobId);
                this.updateJobStatus(jobId, status);
                
                if (status.status === 'completed' || status.status === 'failed') {
                    this.stopPolling(jobId);
                    
                    if (status.status === 'completed') {
                        await this.handleJobCompletion(jobId, status);
                    } else {
                        this.handleJobFailure(jobId, status);
                    }
                }
            } catch (error) {
                console.error(`Error polling job ${jobId}:`, error);
                // Continue polling even on error
            }
        }, this.POLLING_INTERVAL);
        
        this.pollingIntervals.set(jobId, interval);
    }

    /**
     * Stop polling for job status
     */
    stopPolling(jobId) {
        const interval = this.pollingIntervals.get(jobId);
        if (interval) {
            clearInterval(interval);
            this.pollingIntervals.delete(jobId);
        }
    }

    /**
     * Update job status
     */
    updateJobStatus(jobId, status) {
        const job = this.activeJobs.get(jobId);
        if (!job) return;
        
        job.status = status.status;
        job.progress = status.progress || 0;
        job.progressDetails = status.progress_details;
        
        // Update UI
        uiManager.updateJobCard(jobId, status);
        
        // Emit event
        eventBus.emit(Events.JOB_UPDATED, { jobId, status });
    }

    /**
     * Handle job completion
     */
    async handleJobCompletion(jobId, status) {
        try {
            const results = await apiClient.getJobResults(jobId);
            
            // Update UI with results
            uiManager.showJobResults(jobId, results);
            
            // Remove from active jobs
            this.activeJobs.delete(jobId);
            
            // Emit event
            eventBus.emit(Events.JOB_COMPLETED, { jobId, status, results });
        } catch (error) {
            console.error(`Error fetching results for job ${jobId}:`, error);
            uiManager.showJobError(jobId, 'Failed to fetch results');
        }
    }

    /**
     * Handle job failure
     */
    handleJobFailure(jobId, status) {
        // Update UI
        uiManager.showJobError(jobId, status.error || 'Job failed');
        
        // Remove from active jobs
        this.activeJobs.delete(jobId);
        
        // Emit event
        eventBus.emit(Events.JOB_FAILED, { jobId, status });
    }

    /**
     * Download job results
     */
    async downloadResults(jobId) {
        try {
            await apiClient.downloadJobResults(jobId);
        } catch (error) {
            console.error(`Error downloading results for job ${jobId}:`, error);
            uiManager.showError('Failed to download results');
        }
    }

    /**
     * Load existing jobs on page load
     */
    async loadExistingJobs() {
        // This would typically fetch active jobs from the API
        // For now, we'll just clear any orphaned intervals
        this.pollingIntervals.forEach((interval, jobId) => {
            clearInterval(interval);
        });
        this.pollingIntervals.clear();
        this.activeJobs.clear();
    }

    /**
     * Get all active jobs
     */
    getActiveJobs() {
        return Array.from(this.activeJobs.values());
    }

    /**
     * Stop all polling
     */
    stopAllPolling() {
        this.pollingIntervals.forEach((interval) => {
            clearInterval(interval);
        });
        this.pollingIntervals.clear();
    }
}

// Export singleton instance
export const jobManager = new JobManager();