/**
 * UI Module - Handles DOM manipulation and UI updates
 */
import { eventBus, Events } from './events.js';

export class UIManager {
    constructor() {
        this.jobCardTemplate = null;
        this.jobsContainer = null;
        this.generateBtn = null;
        this.initialized = false;
    }

    /**
     * Initialize UI manager
     */
    initialize() {
        this.jobCardTemplate = document.getElementById('jobCardTemplate')?.innerHTML;
        this.jobsContainer = document.getElementById('jobsContainer');
        this.generateBtn = document.getElementById('generateBtn');
        this.initialized = true;
        
        if (!this.jobCardTemplate) {
            console.error('Job card template not found');
        }
    }

    /**
     * Create a new job card
     */
    createJobCard(jobId) {
        if (!this.initialized || !this.jobCardTemplate || !this.jobsContainer) {
            console.error('UIManager not properly initialized');
            return;
        }

        let jobCardHtml = this.jobCardTemplate
            .replace(/{job_id}/g, jobId)
            .replace(/{timestamp}/g, new Date().toLocaleString());
        
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = jobCardHtml;
        const jobCard = tempDiv.firstElementChild;
        
        this.jobsContainer.prepend(jobCard);
        
        return jobCard;
    }

    /**
     * Update job card with status
     */
    updateJobCard(jobId, status) {
        const card = document.getElementById(`job-${jobId}`);
        if (!card) return;

        // Update status badge
        const statusBadge = card.querySelector('.job-status');
        if (statusBadge) {
            statusBadge.className = `badge job-status bg-${this.getStatusColor(status.status)}`;
            statusBadge.textContent = status.status.charAt(0).toUpperCase() + status.status.slice(1);
        }

        // Update progress
        if (status.progress !== undefined) {
            const progressBar = card.querySelector('.progress-bar');
            if (progressBar) {
                progressBar.style.width = `${status.progress}%`;
                progressBar.textContent = `${status.progress}%`;
            }
        }

        // Update progress details
        if (status.progress_details) {
            const pd = status.progress_details;
            const phaseElement = card.querySelector(`#phase-${jobId}`);
            const descElement = card.querySelector(`#phase-description-${jobId}`);
            
            if (phaseElement) phaseElement.textContent = pd.current_phase || '';
            if (descElement) descElement.textContent = pd.phase_description || '';
        }
    }

    /**
     * Show job results
     */
    showJobResults(jobId, results) {
        const card = document.getElementById(`job-${jobId}`);
        if (!card) return;

        // Hide progress section
        const progressSection = card.querySelector('.card-body > div:nth-child(2)');
        if (progressSection) progressSection.style.display = 'none';

        // Show results
        const resultsSection = card.querySelector('.job-results');
        if (resultsSection) {
            resultsSection.style.display = 'block';
            
            // Update summary
            const summaryList = resultsSection.querySelector('.list-unstyled');
            if (summaryList && results.summary) {
                summaryList.innerHTML = `
                    <li><strong>Total Patients:</strong> ${results.summary.total_patients || 0}</li>
                    <li><strong>Generation Time:</strong> ${results.summary.generation_time || 'N/A'}</li>
                    <li><strong>Formats:</strong> ${results.summary.output_formats?.join(', ') || 'N/A'}</li>
                `;
            }

            // Add download button handler
            const downloadBtn = resultsSection.querySelector('.download-results-btn');
            if (downloadBtn) {
                downloadBtn.dataset.jobId = jobId;
                downloadBtn.onclick = () => {
                    eventBus.emit('job:download', { jobId });
                };
            }
        }
    }

    /**
     * Show job error
     */
    showJobError(jobId, error) {
        const card = document.getElementById(`job-${jobId}`);
        if (!card) return;

        // Update status to failed
        const statusBadge = card.querySelector('.job-status');
        if (statusBadge) {
            statusBadge.className = 'badge job-status bg-danger';
            statusBadge.textContent = 'Failed';
        }

        // Show error message
        const cardBody = card.querySelector('.card-body');
        if (cardBody) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'alert alert-danger mt-3';
            errorDiv.innerHTML = `<strong>Error:</strong> ${error}`;
            cardBody.appendChild(errorDiv);
        }
    }

    /**
     * Show general error message
     */
    showError(message) {
        this.showToast(message, 'error');
        eventBus.emit(Events.UI_ERROR_SHOW, { message });
    }

    /**
     * Show success message
     */
    showSuccess(message) {
        this.showToast(message, 'success');
    }

    /**
     * Show info message
     */
    showInfo(message) {
        this.showToast(message, 'info');
    }
    
    /**
     * Show warning message
     */
    showWarning(message) {
        this.showToast(message, 'warning');
    }
    
    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        // Create toast container if it doesn't exist
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999;';
            document.body.appendChild(toastContainer);
        }
        
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `alert alert-${this.getAlertType(type)} alert-dismissible fade show`;
        toast.style.cssText = 'min-width: 250px; margin-bottom: 10px;';
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        toastContainer.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 150);
        }, 5000);
    }
    
    /**
     * Get Bootstrap alert type from message type
     */
    getAlertType(type) {
        const types = {
            'success': 'success',
            'error': 'danger',
            'warning': 'warning',
            'info': 'info'
        };
        return types[type] || 'info';
    }

    /**
     * Set loading state
     */
    setLoading(isLoading) {
        if (this.generateBtn) {
            this.generateBtn.disabled = isLoading;
            this.generateBtn.innerHTML = isLoading ? 
                '<span class="spinner-border spinner-border-sm me-2"></span>Generating...' :
                '<i class="fas fa-play me-2"></i>Generate Patients';
        }
        
        eventBus.emit(isLoading ? Events.UI_LOADING_START : Events.UI_LOADING_END);
    }

    /**
     * Get status color for badge
     */
    getStatusColor(status) {
        const colors = {
            'queued': 'secondary',
            'initializing': 'info',
            'running': 'primary',
            'completed': 'success',
            'failed': 'danger'
        };
        return colors[status] || 'secondary';
    }

    /**
     * Clear all job cards
     */
    clearJobs() {
        if (this.jobsContainer) {
            this.jobsContainer.innerHTML = '';
        }
    }

    /**
     * Update facility configuration display
     */
    updateFacilityConfig(facilityConfigs) {
        // This would update the facility configuration display
        // Implementation depends on your UI structure
    }
}

// Export singleton instance
export const uiManager = new UIManager();