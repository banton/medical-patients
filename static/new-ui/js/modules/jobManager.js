// Job Manager Module

export class JobManager {
    constructor(apiClient) {
        this.apiClient = apiClient;
        this.activeJobs = new Map();
        this.pollingInterval = null;
        this.pollingRate = 2000; // 2 seconds
    }

    startPolling() {
        if (this.pollingInterval) return;
        
        this.pollingInterval = setInterval(() => {
            this.pollActiveJobs();
        }, this.pollingRate);
        
        // Initial poll
        this.pollActiveJobs();
    }

    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    }

    async loadActiveJobs() {
        try {
            const jobs = await this.apiClient.getJobs();
            
            // Clear and repopulate active jobs
            this.activeJobs.clear();
            jobs.forEach(job => {
                if (['pending', 'running'].includes(job.status)) {
                    this.activeJobs.set(job.job_id, job);
                }
            });
            
            return jobs;
        } catch (error) {
            console.error('Failed to load jobs:', error);
            return [];
        }
    }

    async pollActiveJobs() {
        if (this.activeJobs.size === 0) {
            // No active jobs to poll, but still load job list
            await this.loadActiveJobs();
            return;
        }

        for (const [jobId, previousStatus] of this.activeJobs.entries()) {
            try {
                const status = await this.apiClient.getJobStatus(jobId);
                
                // Check if status changed
                if (this.hasStatusChanged(previousStatus, status)) {
                    // Update stored status
                    this.activeJobs.set(jobId, status);
                    
                    // Dispatch event
                    document.dispatchEvent(new CustomEvent('job-status-update', {
                        detail: status
                    }));
                    
                    // Remove from active jobs if completed
                    if (['completed', 'failed', 'cancelled'].includes(status.status)) {
                        this.activeJobs.delete(jobId);
                        
                        // Special event for completion
                        if (status.status === 'completed') {
                            document.dispatchEvent(new CustomEvent('job-completed', {
                                detail: { jobId, status }
                            }));
                        }
                    }
                }
            } catch (error) {
                console.error(`Failed to poll job ${jobId}:`, error);
            }
        }
    }

    hasStatusChanged(previous, current) {
        return (
            previous.status !== current.status ||
            previous.progress !== current.progress ||
            previous.processed_patients !== current.processed_patients ||
            previous.phase_description !== current.phase_description
        );
    }

    trackJob(jobId) {
        // Add job to active tracking
        this.activeJobs.set(jobId, {
            job_id: jobId,
            status: 'pending',
            progress: 0,
            processed_patients: 0,
            total_patients: 0
        });
        
        // Ensure polling is active
        this.startPolling();
    }

    async getActiveJobs() {
        return this.loadActiveJobs();
    }

    async cancelJob(jobId) {
        await this.apiClient.cancelJob(jobId);
        this.activeJobs.delete(jobId);
    }

    getJobDetails(jobId) {
        return this.activeJobs.get(jobId);
    }

    // Statistics methods
    getActiveJobCount() {
        return this.activeJobs.size;
    }

    getTotalProgress() {
        if (this.activeJobs.size === 0) return 0;
        
        let totalProgress = 0;
        this.activeJobs.forEach(job => {
            totalProgress += job.progress || 0;
        });
        
        return totalProgress / this.activeJobs.size;
    }

    getEstimatedCompletionTime() {
        let latestETA = null;
        
        this.activeJobs.forEach(job => {
            if (job.estimated_completion) {
                const eta = new Date(job.estimated_completion);
                if (!latestETA || eta > latestETA) {
                    latestETA = eta;
                }
            }
        });
        
        return latestETA;
    }
}