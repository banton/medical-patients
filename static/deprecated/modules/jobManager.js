// Job Manager Module

export class JobManager {
    constructor(apiClient) {
        this.apiClient = apiClient;
        this.activeJobs = new Map();
        this.pollingInterval = null;
        this.pollingRate = 5000; // 5 seconds - more reasonable
        this.lastPollTime = 0;
        this.minPollInterval = 1000; // Don't poll more than once per second
    }

    startPolling() {
        if (this.pollingInterval) return;
        
        // Use adaptive polling rate
        const poll = () => {
            this.pollActiveJobs();
            
            // Adjust polling rate based on active jobs
            const nextInterval = this.activeJobs.size > 0 ? 
                this.pollingRate : // 5 seconds when active
                30000; // 30 seconds when idle
            
            this.pollingInterval = setTimeout(poll, nextInterval);
        };
        
        // Initial poll
        poll();
    }

    stopPolling() {
        if (this.pollingInterval) {
            clearTimeout(this.pollingInterval);
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
        // Rate limiting
        const now = Date.now();
        if (now - this.lastPollTime < this.minPollInterval) {
            return;
        }
        this.lastPollTime = now;

        // Only poll if we have active jobs
        if (this.activeJobs.size === 0) {
            // Don't constantly reload the job list if there are no active jobs
            // The list will be refreshed when a new job is added via trackJob()
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
        
        // Trigger an immediate poll for this job
        this.pollSingleJob(jobId);
    }
    
    async pollSingleJob(jobId) {
        try {
            const status = await this.apiClient.getJobStatus(jobId);
            this.activeJobs.set(jobId, status);
            
            document.dispatchEvent(new CustomEvent('job-status-update', {
                detail: status
            }));
        } catch (error) {
            console.error(`Failed to poll job ${jobId}:`, error);
        }
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