// Military Patient Generator - Main Application Module

import { ConfigurationManager } from './modules/configurationManager.js';
import { JobManager } from './modules/jobManager.js';
import { TemplateManager } from './modules/templateManager.js';
import { ValidationManager } from './modules/validationManager.js';
import { APIClient } from './modules/apiClient.js';
import { UIComponents } from './modules/uiComponents.js';

class MilitaryPatientGeneratorApp {
    constructor() {
        this.apiClient = new APIClient();
        this.configManager = new ConfigurationManager();
        this.jobManager = new JobManager(this.apiClient);
        this.templateManager = new TemplateManager(this.apiClient);
        this.validationManager = new ValidationManager();
        this.uiComponents = new UIComponents();
        
        this.state = {
            currentConfig: null,
            activeJobs: new Map(),
            templates: [],
            isGenerating: false
        };
    }

    async init() {
        console.log('Initializing Military Patient Generator...');
        
        // Initialize UI components
        await this.initializeUI();
        
        // Load initial data
        await this.loadInitialData();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Start job polling
        this.jobManager.startPolling();
        
        console.log('Application initialized successfully');
    }

    async initializeUI() {
        // Render all UI components
        this.uiComponents.renderBasicSettings('basicSettings');
        this.uiComponents.renderMedicalFacilityDefaults('medicalFacilityDefaults');
        this.uiComponents.renderFrontConfiguration('frontConfiguration');
        this.uiComponents.renderInjuryDistribution('injuryDistribution');
        this.uiComponents.renderOutputConfiguration('outputConfiguration');
        this.uiComponents.renderTemplateSystem('templateSystem');
        
        // Initialize with default configuration
        const defaultConfig = this.configManager.getDefaultConfiguration();
        this.loadConfiguration(defaultConfig);
    }

    async loadInitialData() {
        try {
            // Load templates
            this.templates = await this.templateManager.loadTemplates();
            this.uiComponents.updateTemplateList(this.templates);
            
            // Load active jobs
            const jobs = await this.jobManager.loadActiveJobs();
            this.updateJobsPanel(jobs);
            
            // Load reference data
            const nationalities = await this.apiClient.getNationalities();
            this.uiComponents.setNationalityOptions(nationalities);
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showError('Failed to load initial data. Please refresh the page.');
        }
    }

    setupEventListeners() {
        // Generate button
        document.getElementById('generateBtn').addEventListener('click', () => {
            this.handleGenerate();
        });
        
        // Reset button
        document.getElementById('resetAllBtn').addEventListener('click', () => {
            this.handleReset();
        });
        
        // Quick start button
        document.getElementById('quickStartBtn').addEventListener('click', () => {
            this.showTemplateModal();
        });
        
        // Template system events
        document.addEventListener('template-selected', (e) => {
            this.loadTemplate(e.detail.templateId);
        });
        
        document.addEventListener('template-save', (e) => {
            this.saveAsTemplate(e.detail.name);
        });
        
        // Configuration change events
        document.addEventListener('config-changed', () => {
            this.validateConfiguration();
        });
        
        // Front management events
        document.addEventListener('front-added', () => {
            this.handleFrontAdded();
        });
        
        document.addEventListener('front-removed', (e) => {
            this.handleFrontRemoved(e.detail.frontId);
        });
        
        // Job events
        document.addEventListener('job-status-update', (e) => {
            this.handleJobStatusUpdate(e.detail);
        });
        
        document.addEventListener('job-cancel', (e) => {
            this.cancelJob(e.detail.jobId);
        });
        
        document.addEventListener('job-download', (e) => {
            this.downloadJobResults(e.detail.jobId);
        });
    }

    async handleGenerate() {
        // Validate configuration
        const validation = this.validationManager.validateConfiguration(this.getCurrentConfiguration());
        if (!validation.isValid) {
            this.showValidationErrors(validation.errors);
            return;
        }
        
        // Disable generate button
        this.setGenerating(true);
        
        try {
            // Get current configuration
            const config = this.getCurrentConfiguration();
            
            // Prepare configuration for API
            const apiRequest = this.configManager.prepareForAPI(config);
            
            // Start generation
            const response = await this.apiClient.startGeneration(apiRequest);
            
            // Show progress modal
            this.showProgressModal(response.job_id);
            
            // Add to active jobs
            this.jobManager.trackJob(response.job_id);
            
            // Update jobs panel
            this.updateJobsPanel();
        } catch (error) {
            console.error('Generation error:', error);
            this.showError('Failed to start generation: ' + error.message);
            this.setGenerating(false);
        }
    }

    handleReset() {
        if (confirm('Are you sure you want to reset all configuration to defaults?')) {
            const defaultConfig = this.configManager.getDefaultConfiguration();
            this.loadConfiguration(defaultConfig);
            this.showSuccess('Configuration reset to defaults');
        }
    }

    showTemplateModal() {
        const modal = new bootstrap.Modal(document.getElementById('templateModal'));
        modal.show();
    }

    async loadTemplate(templateId) {
        try {
            const template = await this.templateManager.loadTemplate(templateId);
            this.loadConfiguration(template.configuration);
            this.showSuccess(`Loaded template: ${template.name}`);
        } catch (error) {
            this.showError('Failed to load template: ' + error.message);
        }
    }

    async saveAsTemplate(name) {
        try {
            const config = this.getCurrentConfiguration();
            const template = await this.templateManager.saveTemplate(name, config);
            this.templates.push(template);
            this.uiComponents.updateTemplateList(this.templates);
            this.showSuccess(`Template saved: ${name}`);
        } catch (error) {
            this.showError('Failed to save template: ' + error.message);
        }
    }

    getCurrentConfiguration() {
        return this.uiComponents.collectConfiguration();
    }

    loadConfiguration(config) {
        this.uiComponents.loadConfiguration(config);
        this.validateConfiguration();
    }

    validateConfiguration() {
        const config = this.getCurrentConfiguration();
        const validation = this.validationManager.validateConfiguration(config);
        this.uiComponents.updateValidationState(validation);
    }

    showValidationErrors(errors) {
        const errorList = errors.map(e => `• ${e.field}: ${e.message}`).join('\n');
        this.showError('Please fix the following errors:\n' + errorList);
    }

    setGenerating(isGenerating) {
        this.state.isGenerating = isGenerating;
        const generateBtn = document.getElementById('generateBtn');
        generateBtn.disabled = isGenerating;
        generateBtn.innerHTML = isGenerating ? 
            '<span class="spinner-border spinner-border-sm me-1"></span>Generating...' : 
            '<i class="bi bi-play-fill me-1"></i>Generate Patients';
    }

    showProgressModal(jobId) {
        const modal = new bootstrap.Modal(document.getElementById('progressModal'));
        modal.show();
        
        // Reset progress
        this.updateProgress(0, 'Initializing...', '0/0', 'Starting generation...');
        
        // Cancel button handler
        document.getElementById('cancelJobBtn').onclick = () => {
            this.cancelJob(jobId);
            modal.hide();
        };
    }

    updateProgress(percentage, status, patients, phase) {
        const progressBar = document.getElementById('progressBar');
        progressBar.style.width = percentage + '%';
        progressBar.textContent = percentage + '%';
        
        document.getElementById('progressStatus').textContent = status;
        document.getElementById('progressPatients').textContent = patients;
        document.getElementById('progressPhase').textContent = phase;
    }

    async handleJobStatusUpdate(jobStatus) {
        // Update progress modal if visible
        const progressModal = bootstrap.Modal.getInstance(document.getElementById('progressModal'));
        if (progressModal && progressModal._isShown) {
            const percentage = Math.round(jobStatus.progress * 100);
            const patients = `${jobStatus.processed_patients}/${jobStatus.total_patients}`;
            this.updateProgress(percentage, jobStatus.status, patients, jobStatus.phase_description);
            
            // Close modal if completed
            if (jobStatus.status === 'completed' || jobStatus.status === 'failed') {
                progressModal.hide();
                this.setGenerating(false);
                
                if (jobStatus.status === 'completed') {
                    this.showSuccess('Generation completed successfully!');
                } else {
                    this.showError('Generation failed: ' + (jobStatus.error_message || 'Unknown error'));
                }
            }
        }
        
        // Update jobs panel
        this.updateJobsPanel();
    }

    async updateJobsPanel(jobs = null) {
        if (!jobs) {
            jobs = await this.jobManager.getActiveJobs();
        }
        this.uiComponents.renderJobsPanel('jobsPanel', jobs);
    }

    async cancelJob(jobId) {
        try {
            await this.apiClient.cancelJob(jobId);
            this.showSuccess('Job cancelled');
            this.updateJobsPanel();
        } catch (error) {
            this.showError('Failed to cancel job: ' + error.message);
        }
    }

    async downloadJobResults(jobId) {
        try {
            const url = await this.apiClient.getDownloadUrl(jobId);
            window.location.href = url;
        } catch (error) {
            this.showError('Failed to download results: ' + error.message);
        }
    }

    handleFrontAdded() {
        const fronts = this.uiComponents.getFronts();
        this.uiComponents.addFront(fronts.length);
        this.validateConfiguration();
    }

    handleFrontRemoved(frontId) {
        this.uiComponents.removeFront(frontId);
        this.validateConfiguration();
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'danger');
    }

    showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
        notification.style.zIndex = '9999';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(notification);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    const app = new MilitaryPatientGeneratorApp();
    
    // Make app globally available
    window.app = app;
    
    try {
        await app.init();
        
        // Try to load auto-saved configuration
        const autoSaved = window.loadAutoSavedConfiguration();
        if (autoSaved && confirm('Found auto-saved configuration. Would you like to restore it?')) {
            app.loadConfiguration(autoSaved);
        }
    } catch (error) {
        console.error('Failed to initialize application:', error);
        app.showError('Failed to initialize application. Please refresh the page.');
    }
});