/**
 * Main Application Module - Orchestrates all other modules
 */
import { apiClient } from './api.js';
import { validationManager } from './validation.js';
import { frontConfigManager } from './frontConfig.js';
import { jobManager } from './jobManager.js';
import { uiManager } from './ui.js';
import { eventBus, Events } from './events.js';
import { configPersistence } from './persistence.js';
import { AccessibilityManager } from './accessibility.js';

class PatientGeneratorApp {
    constructor() {
        this.initialized = false;
        this.defaultFacilityConfigs = [
            {id: "POINT_OF_INJURY", name: "Point of Injury", kia_rate: 0.20, rtd_rate: 0.0},
            {id: "ROLE_1", name: "Role 1", kia_rate: 0.10, rtd_rate: 0.1},
            {id: "ROLE_2", name: "Role 2", kia_rate: 0.05, rtd_rate: 0.2},
            {id: "ROLE_3", name: "Role 3", kia_rate: 0.02, rtd_rate: 0.3},
            {id: "ROLE_4", name: "Role 4", kia_rate: 0.01, rtd_rate: 0.0}
        ];
        this.accessibilityManager = null;
    }

    /**
     * Initialize the application
     */
    async initialize() {
        try {
            // Initialize UI manager
            uiManager.initialize();
            
            // Initialize accessibility manager
            this.accessibilityManager = new AccessibilityManager(eventBus);
            this.accessibilityManager.init();
            
            // Setup event listeners
            this.setupEventListeners();
            
            // Try to load nationalities with graceful degradation
            let nationalities = [];
            try {
                nationalities = await apiClient.fetchNationalities();
            } catch (error) {
                console.warn('Failed to load nationalities from API, using fallback data');
                // Use fallback nationality data
                nationalities = this.getFallbackNationalities();
                uiManager.showWarning('Running in offline mode. Some features may be limited.');
            }
            
            await frontConfigManager.initialize(nationalities);
            
            // Try to load existing jobs (non-critical)
            try {
                await jobManager.loadExistingJobs();
            } catch (error) {
                console.warn('Failed to load existing jobs:', error);
            }
            
            // Setup form handlers
            this.setupFormHandlers();
            
            // Setup persistence handlers
            this.setupPersistenceHandlers();
            
            // Start auto-save
            configPersistence.startAutoSave(() => this.getCurrentConfiguration());
            
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
            eventBus.emit('generation-completed');
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
        
        // Injury percentage validation with debouncing
        document.querySelectorAll('.injury-percent').forEach(input => {
            input.addEventListener('input', () => {
                validationManager.debouncedValidateInjury();
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
            eventBus.emit('generation-started');
            
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
                "Non-Battle Injury": parseFloat(document.getElementById('nonBattlePercent')?.value || '0'),
                "Battle Injury": parseFloat(document.getElementById('battleTraumaPercent')?.value || '0')
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

    /**
     * Get current form configuration
     */
    getCurrentConfiguration() {
        const frontConfigs = frontConfigManager.getFrontConfigurations();
        if (frontConfigs.length === 0) return null;
        
        return this.buildConfiguration(frontConfigs);
    }

    /**
     * Load configuration into form
     */
    loadConfigurationIntoForm(config) {
        try {
            // Set total patients
            const totalPatientsInput = document.getElementById('totalPatients');
            if (totalPatientsInput && config.total_patients) {
                totalPatientsInput.value = config.total_patients;
            }

            // Set injury distribution
            if (config.injury_distribution) {
                const diseaseInput = document.getElementById('diseasePercent');
                const nonBattleInput = document.getElementById('nonBattlePercent');
                const battleInput = document.getElementById('battleTraumaPercent');
                
                if (diseaseInput) diseaseInput.value = config.injury_distribution['Disease'] || 0;
                if (nonBattleInput) nonBattleInput.value = config.injury_distribution['Non-Battle Injury'] || 0;
                if (battleInput) battleInput.value = config.injury_distribution['Battle Injury'] || 0;
                
                validationManager.validateInjuryPercentages();
            }

            // Load front configurations
            if (config.front_configs && Array.isArray(config.front_configs)) {
                frontConfigManager.loadFrontConfigurations(config.front_configs);
            }

            return true;
        } catch (error) {
            console.error('Failed to load configuration into form:', error);
            return false;
        }
    }

    /**
     * Setup persistence event handlers
     */
    setupPersistenceHandlers() {
        // Save configuration button
        const saveBtn = document.getElementById('saveConfigBtn');
        if (saveBtn) {
            saveBtn.onclick = () => this.showSaveDialog();
        }

        // Load configuration button
        const loadBtn = document.getElementById('loadConfigBtn');
        if (loadBtn) {
            loadBtn.onclick = () => this.showLoadDialog();
        }

        // Templates button
        const templatesBtn = document.getElementById('templatesBtn');
        if (templatesBtn) {
            templatesBtn.onclick = () => this.showTemplatesDialog();
        }

        // Import/Export handlers
        const importBtn = document.getElementById('importConfigBtn');
        const exportBtn = document.getElementById('exportConfigBtn');
        const importInput = document.getElementById('importConfigInput');

        if (importBtn && importInput) {
            importBtn.onclick = (e) => {
                e.preventDefault();
                importInput.click();
            };

            importInput.onchange = async (e) => {
                const file = e.target.files[0];
                if (file) {
                    try {
                        const config = await configPersistence.importConfiguration(file);
                        this.loadConfigurationIntoForm(config);
                        uiManager.showSuccess('Configuration imported successfully');
                    } catch (error) {
                        uiManager.showError('Failed to import configuration: ' + error.message);
                    }
                    importInput.value = ''; // Reset input
                }
            };
        }

        if (exportBtn) {
            exportBtn.onclick = (e) => {
                e.preventDefault();
                const config = this.getCurrentConfiguration();
                if (config) {
                    const filename = `patient-config-${new Date().toISOString().split('T')[0]}.json`;
                    configPersistence.exportConfiguration(config, filename);
                } else {
                    uiManager.showError('No configuration to export');
                }
            };
        }

        // Undo/Redo handlers
        const undoBtn = document.getElementById('undoBtn');
        const redoBtn = document.getElementById('redoBtn');

        if (undoBtn) {
            undoBtn.onclick = (e) => {
                e.preventDefault();
                const previousState = configPersistence.undo();
                if (previousState) {
                    this.loadConfigurationIntoForm(previousState);
                    uiManager.showInfo('Undo successful');
                }
            };
        }

        if (redoBtn) {
            redoBtn.onclick = (e) => {
                e.preventDefault();
                const nextState = configPersistence.redo();
                if (nextState) {
                    this.loadConfigurationIntoForm(nextState);
                    uiManager.showInfo('Redo successful');
                }
            };
        }

        // Clear configuration
        const clearBtn = document.getElementById('clearConfigBtn');
        if (clearBtn) {
            clearBtn.onclick = (e) => {
                e.preventDefault();
                if (confirm('Are you sure you want to clear all configurations?')) {
                    location.reload(); // Simple way to reset everything
                }
            };
        }

        // Listen for persistence events
        eventBus.on('config:autosaved', () => {
            const autoSaveStatus = document.getElementById('autoSaveStatus');
            if (autoSaveStatus) {
                autoSaveStatus.style.display = 'block';
                setTimeout(() => {
                    autoSaveStatus.style.display = 'none';
                }, 3000);
            }
        });

        // Track changes for undo/redo
        this.trackConfigurationChanges();
    }

    /**
     * Show save configuration dialog
     */
    showSaveDialog() {
        const modal = new bootstrap.Modal(document.getElementById('saveConfigModal'));
        const confirmBtn = document.getElementById('confirmSaveBtn');
        const nameInput = document.getElementById('configName');

        confirmBtn.onclick = () => {
            const name = nameInput.value.trim();
            if (name) {
                const config = this.getCurrentConfiguration();
                if (config) {
                    configPersistence.saveConfiguration(config, name);
                    uiManager.showSuccess(`Configuration "${name}" saved`);
                    modal.hide();
                    nameInput.value = '';
                } else {
                    uiManager.showError('No configuration to save');
                }
            } else {
                uiManager.showError('Please enter a configuration name');
            }
        };

        modal.show();
    }

    /**
     * Show load configuration dialog
     */
    showLoadDialog() {
        const modal = new bootstrap.Modal(document.getElementById('loadConfigModal'));
        const listContainer = document.getElementById('savedConfigsList');
        const noConfigsMsg = document.getElementById('noSavedConfigs');

        // Get saved configurations
        const savedConfigs = configPersistence.getSavedConfigurations();
        const configNames = Object.keys(savedConfigs);

        listContainer.innerHTML = '';

        if (configNames.length === 0) {
            noConfigsMsg.style.display = 'block';
        } else {
            noConfigsMsg.style.display = 'none';

            configNames.forEach(name => {
                const config = savedConfigs[name];
                const item = document.createElement('button');
                item.className = 'list-group-item list-group-item-action';
                item.innerHTML = `
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="mb-1">${name}</h6>
                            <small class="text-muted">Saved: ${new Date(config.savedAt).toLocaleString()}</small>
                        </div>
                        <button class="btn btn-sm btn-danger delete-config-btn" data-name="${name}">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                `;

                item.onclick = (e) => {
                    if (!e.target.closest('.delete-config-btn')) {
                        this.loadConfigurationIntoForm(config);
                        uiManager.showSuccess(`Configuration "${name}" loaded`);
                        modal.hide();
                    }
                };

                // Delete button handler
                const deleteBtn = item.querySelector('.delete-config-btn');
                deleteBtn.onclick = (e) => {
                    e.stopPropagation();
                    if (confirm(`Delete configuration "${name}"?`)) {
                        configPersistence.deleteConfiguration(name);
                        this.showLoadDialog(); // Refresh the list
                    }
                };

                listContainer.appendChild(item);
            });
        }

        modal.show();
    }

    /**
     * Show templates dialog
     */
    showTemplatesDialog() {
        const modal = new bootstrap.Modal(document.getElementById('templatesModal'));
        const listContainer = document.getElementById('templatesList');

        const templates = configPersistence.getTemplates();
        listContainer.innerHTML = '';

        Object.entries(templates).forEach(([key, template]) => {
            const col = document.createElement('div');
            col.className = 'col-md-6 mb-3';
            col.innerHTML = `
                <div class="card h-100 template-card" role="button">
                    <div class="card-body">
                        <h5 class="card-title">${template.templateName}</h5>
                        <p class="card-text">${template.description}</p>
                        <div class="small text-muted">
                            <div><i class="fas fa-flag me-1"></i>${template.front_configs.length} front(s)</div>
                            <div><i class="fas fa-users me-1"></i>${template.total_patients} patients</div>
                        </div>
                    </div>
                </div>
            `;

            col.querySelector('.template-card').onclick = () => {
                this.loadConfigurationIntoForm(template);
                uiManager.showSuccess(`Template "${template.templateName}" loaded`);
                modal.hide();
            };

            listContainer.appendChild(col);
        });

        modal.show();
    }

    /**
     * Track configuration changes for undo/redo
     */
    trackConfigurationChanges() {
        let changeTimeout;
        const trackChange = () => {
            clearTimeout(changeTimeout);
            changeTimeout = setTimeout(() => {
                const config = this.getCurrentConfiguration();
                if (config) {
                    configPersistence.addToUndoHistory(config);
                }
            }, 1000); // Debounce changes
        };

        // Track all form changes
        document.getElementById('generatorForm').addEventListener('input', trackChange);
        document.getElementById('generatorForm').addEventListener('change', trackChange);

        // Track front configuration changes
        eventBus.on('front:added', trackChange);
        eventBus.on('front:removed', trackChange);
    }
    
    /**
     * Get fallback nationality data for offline mode
     */
    getFallbackNationalities() {
        return [
            { code: "US", name: "United States" },
            { code: "UK", name: "United Kingdom" },
            { code: "PL", name: "Poland" },
            { code: "DE", name: "Germany" },
            { code: "FR", name: "France" },
            { code: "CA", name: "Canada" },
            { code: "AU", name: "Australia" },
            { code: "IT", name: "Italy" },
            { code: "ES", name: "Spain" },
            { code: "NL", name: "Netherlands" }
        ];
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