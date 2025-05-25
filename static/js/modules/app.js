/**
 * Main Application Module - Orchestrates all other modules
 */
import { apiClient } from './api.js';
import { validationManager } from './validation.js';
import { frontConfigManager } from './frontConfig.js';
import { jobManager } from './jobManager.js';
import { uiManager } from './ui.js';
import { eventBus, Events } from './events.js';

class PatientGeneratorApp {
    constructor() {
        this.initialized = false;
        this.defaultFacilityConfigs = [
            {id: "POINT_OF_INJURY", name: "Point of Injury", mortality_rate: 0.20, rtd_rate: 0.0},
            {id: "ROLE_1", name: "Role 1", mortality_rate: 0.10, rtd_rate: 0.1},
            {id: "ROLE_2", name: "Role 2", mortality_rate: 0.05, rtd_rate: 0.2},
            {id: "ROLE_3", name: "Role 3", mortality_rate: 0.02, rtd_rate: 0.3},
            {id: "ROLE_4", name: "Role 4", mortality_rate: 0.01, rtd_rate: 0.0}
        ];
    }

    /**
     * Initialize the application
     */
    async initialize() {
        try {
            // Initialize UI manager
            uiManager.initialize();
            
            // Setup event listeners
            this.setupEventListeners();
            
            // Load nationalities and initialize front config
            const nationalities = await apiClient.fetchNationalities();
            await frontConfigManager.initialize(nationalities);
            
            // Load existing jobs
            await jobManager.loadExistingJobs();
            
            // Setup form handlers
            this.setupFormHandlers();
            
            this.initialized = true;
            console.log('Patient Generator Application initialized');
            
        } catch (error) {
            console.error('Failed to initialize application:', error);
            uiManager.showError('Failed to initialize application. Please refresh the page.');
        }
    }

    /**
     * Setup event listeners for inter-module communication
     */
    setupEventListeners() {
        // Job events
        eventBus.on(Events.JOB_CREATED, (data) => {
            console.log('Job created:', data.jobId);
        });
        
        eventBus.on(Events.JOB_COMPLETED, (data) => {
            console.log('Job completed:', data.jobId);
            uiManager.showSuccess('Patient generation completed successfully!');
        });
        
        eventBus.on(Events.JOB_FAILED, (data) => {
            console.error('Job failed:', data.jobId, data.status.error);
        });
        
        // Form events
        eventBus.on(Events.FORM_ERROR, (data) => {
            uiManager.showError(data.message);
        });
        
        // Job download event
        eventBus.on('job:download', async (data) => {
            await jobManager.downloadResults(data.jobId);
        });
    }

    /**
     * Setup form handlers
     */
    setupFormHandlers() {
        const form = document.getElementById('generatorForm');
        if (!form) return;
        
        // Form submission
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.handleFormSubmission();
        });
        
        // Injury percentage validation
        document.querySelectorAll('.injury-percent').forEach(input => {
            input.addEventListener('input', () => {
                validationManager.validateInjuryPercentages();
            });
        });
        
        // Add front button
        const addFrontBtn = document.getElementById('addFrontBtn');
        if (addFrontBtn) {
            addFrontBtn.onclick = () => frontConfigManager.addNewFront();
        }
    }

    /**
     * Handle form submission
     */
    async handleFormSubmission() {
        try {
            // Validate form
            if (!validationManager.validateForm()) {
                const errors = validationManager.getErrors();
                console.error('Validation errors:', errors);
                eventBus.emit(Events.FORM_ERROR, { 
                    message: 'Please fix validation errors before submitting.' 
                });
                return;
            }
            
            // Get front configurations
            const frontConfigs = frontConfigManager.getFrontConfigurations();
            if (frontConfigs.length === 0) {
                eventBus.emit(Events.FORM_ERROR, { 
                    message: 'At least one front with a casualty rate and nationality distribution must be configured.' 
                });
                return;
            }
            
            // Build configuration payload
            const configuration = this.buildConfiguration(frontConfigs);
            
            // Set loading state
            uiManager.setLoading(true);
            
            // Submit generation request
            const payload = {
                configuration: configuration,
                output_formats: this.getSelectedFormats(),
                use_compression: document.getElementById('useCompression')?.checked || false,
                use_encryption: document.getElementById('useEncryption')?.checked || false,
                encryption_password: document.getElementById('encryptionPassword')?.value || null
            };
            
            const response = await apiClient.generatePatients(payload);
            
            // Create job and start polling
            await jobManager.createJob(response);
            
            // Reset loading state
            uiManager.setLoading(false);
            
            // Emit success event
            eventBus.emit(Events.FORM_SUBMITTED, { configuration, response });
            
        } catch (error) {
            console.error('Error submitting form:', error);
            uiManager.setLoading(false);
            eventBus.emit(Events.FORM_ERROR, { 
                message: error.message || 'Failed to generate patients' 
            });
        }
    }

    /**
     * Build configuration object from form data
     */
    buildConfiguration(frontConfigs) {
        return {
            name: "Scenario from Dynamic Front Configuration",
            description: `Generated on ${new Date().toISOString()} using dynamic front configuration.`,
            front_configs: frontConfigs,
            facility_configs: this.defaultFacilityConfigs,
            total_patients: parseInt(document.getElementById('totalPatients')?.value || '100'),
            injury_distribution: {
                "Disease": parseFloat(document.getElementById('diseasePercent')?.value || '0'),
                "Non-Battle Injury": parseFloat(document.getElementById('nonBattleInjuryPercent')?.value || '0'),
                "Battle Injury": parseFloat(document.getElementById('battleInjuryPercent')?.value || '0')
            }
        };
    }

    /**
     * Get selected output formats
     */
    getSelectedFormats() {
        const formats = [];
        if (document.getElementById('formatJson')?.checked) formats.push('json');
        if (document.getElementById('formatXml')?.checked) formats.push('xml');
        if (document.getElementById('formatCsv')?.checked) formats.push('csv');
        if (document.getElementById('formatNdef')?.checked) formats.push('ndef');
        
        return formats.length > 0 ? formats : ['json'];
    }
}

// Create and export app instance
export const app = new PatientGeneratorApp();

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => app.initialize());
} else {
    app.initialize();
}