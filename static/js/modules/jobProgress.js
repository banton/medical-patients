/**
 * Job Progress Modal Module
 * Displays real-time progress updates for patient generation jobs
 */

import { eventBus, Events } from './events.js';
import { apiClient } from './api.js';

class JobProgressModal {
    constructor() {
        this.currentJobId = null;
        this.pollingInterval = null;
        this.modalElement = null;
        this.progressBar = null;
        this.progressText = null;
        this.phaseText = null;
        this.statsContainer = null;
        this.isVisible = false;
        
        this.initializeModal();
        this.setupEventListeners();
    }

    /**
     * Initialize the modal HTML structure
     */
    initializeModal() {
        // Create modal HTML
        const modalHtml = `
            <div class="modal fade" id="jobProgressModal" tabindex="-1" data-bs-backdrop="static" data-bs-keyboard="false">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-sync-alt fa-spin me-2"></i>
                                Generating Patients
                            </h5>
                        </div>
                        <div class="modal-body">
                            <div class="mb-4">
                                <div class="d-flex justify-content-between mb-2">
                                    <span class="text-muted">Progress</span>
                                    <span id="progressPercentText" class="fw-bold">0%</span>
                                </div>
                                <div class="progress" style="height: 30px;">
                                    <div id="jobProgressBar" 
                                         class="progress-bar progress-bar-striped progress-bar-animated" 
                                         role="progressbar" 
                                         style="width: 0%"
                                         aria-valuenow="0" 
                                         aria-valuemin="0" 
                                         aria-valuemax="100">
                                    </div>
                                </div>
                            </div>
                            
                            <div class="mb-4">
                                <h6 class="text-muted mb-2">Current Phase</h6>
                                <div id="phaseDescription" class="alert alert-info">
                                    <i class="fas fa-hourglass-start me-2"></i>
                                    <span id="phaseText">Initializing...</span>
                                </div>
                            </div>
                            
                            <div id="progressDetails" class="mb-3">
                                <div class="row text-center">
                                    <div class="col-md-4">
                                        <div class="card bg-light">
                                            <div class="card-body py-2">
                                                <h6 class="card-title text-muted mb-1">Total Patients</h6>
                                                <p class="card-text fs-4 fw-bold mb-0" id="totalPatientsText">-</p>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="col-md-4">
                                        <div class="card bg-light">
                                            <div class="card-body py-2">
                                                <h6 class="card-title text-muted mb-1">Processed</h6>
                                                <p class="card-text fs-4 fw-bold mb-0" id="processedPatientsText">-</p>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="col-md-4">
                                        <div class="card bg-light">
                                            <div class="card-body py-2">
                                                <h6 class="card-title text-muted mb-1">Time Elapsed</h6>
                                                <p class="card-text fs-4 fw-bold mb-0" id="timeElapsedText">-</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Job completion stats (hidden initially) -->
                            <div id="completionStats" class="d-none">
                                <hr>
                                <h5 class="mb-3">
                                    <i class="fas fa-chart-bar me-2"></i>
                                    Generation Summary
                                </h5>
                                <div id="statsContainer">
                                    <!-- Stats will be dynamically inserted here -->
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary d-none" id="closeProgressBtn" data-bs-dismiss="modal">
                                Close
                            </button>
                            <button type="button" class="btn btn-primary d-none" id="viewResultsBtn">
                                <i class="fas fa-chart-line me-2"></i>
                                View Results
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Add modal to body
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Get references to elements
        this.modalElement = document.getElementById('jobProgressModal');
        this.progressBar = document.getElementById('jobProgressBar');
        this.progressText = document.getElementById('progressPercentText');
        this.phaseText = document.getElementById('phaseText');
        this.statsContainer = document.getElementById('statsContainer');
        
        // Initialize Bootstrap modal
        this.modal = new bootstrap.Modal(this.modalElement);
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Listen for job created event
        eventBus.on(Events.JOB_CREATED, (data) => {
            this.showProgress(data.jobId);
        });
        
        // Listen for job completed event
        eventBus.on(Events.JOB_COMPLETED, (data) => {
            if (data.jobId === this.currentJobId) {
                this.showCompletionStats(data);
            }
        });
        
        // Listen for job failed event
        eventBus.on(Events.JOB_FAILED, (data) => {
            if (data.jobId === this.currentJobId) {
                this.showError(data.status.error || 'Job failed');
            }
        });
        
        // View results button
        document.getElementById('viewResultsBtn').addEventListener('click', () => {
            this.viewResults();
        });
    }

    /**
     * Show progress modal and start polling
     */
    showProgress(jobId) {
        this.currentJobId = jobId;
        this.isVisible = true;
        
        // Reset UI
        this.resetProgress();
        
        // Show modal
        this.modal.show();
        
        // Start polling for progress
        this.startPolling();
    }

    /**
     * Reset progress UI
     */
    resetProgress() {
        this.updateProgress(0);
        this.phaseText.textContent = 'Initializing...';
        document.getElementById('totalPatientsText').textContent = '-';
        document.getElementById('processedPatientsText').textContent = '-';
        document.getElementById('timeElapsedText').textContent = '-';
        document.getElementById('completionStats').classList.add('d-none');
        document.getElementById('closeProgressBtn').classList.add('d-none');
        document.getElementById('viewResultsBtn').classList.add('d-none');
    }

    /**
     * Start polling for job progress
     */
    startPolling() {
        // Clear any existing interval
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
        }
        
        // Poll immediately
        this.pollProgress();
        
        // Then poll every 500ms
        this.pollingInterval = setInterval(() => {
            this.pollProgress();
        }, 500);
    }

    /**
     * Poll for job progress
     */
    async pollProgress() {
        try {
            const status = await apiClient.getJobStatus(this.currentJobId);
            
            if (!this.isVisible) return;
            
            // Update progress based on status
            if (status.progress_details) {
                const details = status.progress_details;
                const progress = Math.round(status.progress * 100);
                
                // Update progress bar (in 10% increments)
                const roundedProgress = Math.floor(progress / 10) * 10;
                this.updateProgress(roundedProgress);
                
                // Update phase text
                if (details.phase_description) {
                    this.phaseText.textContent = details.phase_description;
                }
                
                // Update counters
                if (details.total_patients) {
                    document.getElementById('totalPatientsText').textContent = details.total_patients.toLocaleString();
                }
                if (details.processed_patients !== undefined) {
                    document.getElementById('processedPatientsText').textContent = details.processed_patients.toLocaleString();
                }
                
                // Update time elapsed
                if (status.created_at) {
                    const elapsed = this.calculateElapsedTime(status.created_at);
                    document.getElementById('timeElapsedText').textContent = elapsed;
                }
            }
            
            // Check if job is complete
            if (status.status === 'completed') {
                this.stopPolling();
                this.showCompletionStats(status);
            } else if (status.status === 'failed') {
                this.stopPolling();
                this.showError(status.error || 'Job failed');
            }
            
        } catch (error) {
            console.error('Error polling job progress:', error);
            // Continue polling unless job is no longer visible
            if (!this.isVisible) {
                this.stopPolling();
            }
        }
    }

    /**
     * Update progress bar
     */
    updateProgress(percentage) {
        this.progressBar.style.width = `${percentage}%`;
        this.progressBar.setAttribute('aria-valuenow', percentage);
        this.progressText.textContent = `${percentage}%`;
    }

    /**
     * Calculate elapsed time
     */
    calculateElapsedTime(startTime) {
        const start = new Date(startTime);
        const now = new Date();
        const elapsed = Math.floor((now - start) / 1000); // seconds
        
        if (elapsed < 60) {
            return `${elapsed}s`;
        } else if (elapsed < 3600) {
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            return `${minutes}m ${seconds}s`;
        } else {
            const hours = Math.floor(elapsed / 3600);
            const minutes = Math.floor((elapsed % 3600) / 60);
            return `${hours}h ${minutes}m`;
        }
    }

    /**
     * Show completion statistics
     */
    async showCompletionStats(jobData) {
        // Update to 100%
        this.updateProgress(100);
        this.phaseText.textContent = 'Generation Complete!';
        
        // Change phase alert color
        document.getElementById('phaseDescription').className = 'alert alert-success';
        
        try {
            // Fetch job results for statistics
            const results = await apiClient.getJobResults(this.currentJobId);
            
            if (results.summary) {
                this.displayStats(results.summary);
            }
            
        } catch (error) {
            console.error('Error fetching job results:', error);
        }
        
        // Show completion buttons
        document.getElementById('completionStats').classList.remove('d-none');
        document.getElementById('closeProgressBtn').classList.remove('d-none');
        document.getElementById('viewResultsBtn').classList.remove('d-none');
    }

    /**
     * Display statistics
     */
    displayStats(summary) {
        const statsHtml = `
            <div class="row">
                <div class="col-md-6 mb-3">
                    <div class="card border-primary">
                        <div class="card-body">
                            <h6 class="card-title text-primary">Patient Outcomes</h6>
                            <ul class="list-unstyled mb-0">
                                <li><strong>RTD:</strong> ${summary.rtd_count || 0} patients (${this.calculatePercentage(summary.rtd_count, summary.total_patients)}%)</li>
                                <li><strong>KIA:</strong> ${summary.kia_count || 0} patients (${this.calculatePercentage(summary.kia_count, summary.total_patients)}%)</li>
                                <li><strong>Evacuated:</strong> ${summary.evacuated_count || 0} patients (${this.calculatePercentage(summary.evacuated_count, summary.total_patients)}%)</li>
                            </ul>
                        </div>
                    </div>
                </div>
                <div class="col-md-6 mb-3">
                    <div class="card border-info">
                        <div class="card-body">
                            <h6 class="card-title text-info">Injury Distribution</h6>
                            <ul class="list-unstyled mb-0">
                                ${this.renderInjuryStats(summary.injury_distribution)}
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="col-md-6 mb-3">
                    <div class="card border-success">
                        <div class="card-body">
                            <h6 class="card-title text-success">Nationality Distribution</h6>
                            <ul class="list-unstyled mb-0">
                                ${this.renderNationalityStats(summary.nationality_distribution)}
                            </ul>
                        </div>
                    </div>
                </div>
                <div class="col-md-6 mb-3">
                    <div class="card border-warning">
                        <div class="card-body">
                            <h6 class="card-title text-warning">Output Files</h6>
                            <ul class="list-unstyled mb-0">
                                ${this.renderOutputFiles(summary.output_files)}
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        this.statsContainer.innerHTML = statsHtml;
    }

    /**
     * Calculate percentage
     */
    calculatePercentage(value, total) {
        if (!total || total === 0) return 0;
        return ((value / total) * 100).toFixed(1);
    }

    /**
     * Render injury statistics
     */
    renderInjuryStats(injuryDist) {
        if (!injuryDist) return '<li>No injury data available</li>';
        
        return Object.entries(injuryDist)
            .map(([type, count]) => `<li><strong>${type}:</strong> ${count} patients</li>`)
            .join('');
    }

    /**
     * Render nationality statistics
     */
    renderNationalityStats(nationalityDist) {
        if (!nationalityDist) return '<li>No nationality data available</li>';
        
        // Sort by count and take top 5
        const sorted = Object.entries(nationalityDist)
            .sort(([, a], [, b]) => b - a)
            .slice(0, 5);
        
        return sorted
            .map(([code, count]) => `<li><strong>${code}:</strong> ${count} patients</li>`)
            .join('');
    }

    /**
     * Render output files
     */
    renderOutputFiles(files) {
        if (!files || files.length === 0) return '<li>No output files generated</li>';
        
        return files
            .map(file => {
                const filename = file.split('/').pop();
                return `<li><i class="fas fa-file me-1"></i>${filename}</li>`;
            })
            .join('');
    }

    /**
     * Show error state
     */
    showError(errorMessage) {
        this.phaseText.textContent = `Error: ${errorMessage}`;
        document.getElementById('phaseDescription').className = 'alert alert-danger';
        document.getElementById('closeProgressBtn').classList.remove('d-none');
        
        // Stop progress bar animation
        this.progressBar.classList.remove('progress-bar-animated');
        this.progressBar.classList.add('bg-danger');
    }

    /**
     * Stop polling
     */
    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    }

    /**
     * View results in visualization dashboard
     */
    viewResults() {
        // Navigate to visualization dashboard with job ID
        window.location.href = `/static/visualizations.html?job_id=${this.currentJobId}`;
    }

    /**
     * Hide modal
     */
    hide() {
        this.isVisible = false;
        this.stopPolling();
        this.modal.hide();
    }
}

// Export singleton instance
export const jobProgressModal = new JobProgressModal();