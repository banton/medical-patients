/**
 * Configuration Persistence Module - Handles saving/loading configurations
 */
import { eventBus, Events } from './events.js';

class ConfigurationPersistence {
    constructor() {
        this.STORAGE_KEY = 'patientGeneratorConfig';
        this.DRAFTS_KEY = 'patientGeneratorDrafts';
        this.TEMPLATES_KEY = 'patientGeneratorTemplates';
        this.MAX_UNDO_HISTORY = 20;
        this.undoHistory = [];
        this.redoHistory = [];
        this.autoSaveTimer = null;
        this.autoSaveInterval = 30000; // 30 seconds
    }

    /**
     * Save current configuration to localStorage
     */
    saveConfiguration(config, name = 'default') {
        try {
            const savedConfigs = this.getSavedConfigurations();
            savedConfigs[name] = {
                ...config,
                savedAt: new Date().toISOString(),
                version: '1.0'
            };
            
            localStorage.setItem(this.STORAGE_KEY, JSON.stringify(savedConfigs));
            eventBus.emit('config:saved', { name, config });
            return true;
        } catch (error) {
            console.error('Failed to save configuration:', error);
            return false;
        }
    }

    /**
     * Load configuration from localStorage
     */
    loadConfiguration(name = 'default') {
        try {
            const savedConfigs = this.getSavedConfigurations();
            const config = savedConfigs[name];
            
            if (config) {
                eventBus.emit('config:loaded', { name, config });
                return config;
            }
            return null;
        } catch (error) {
            console.error('Failed to load configuration:', error);
            return null;
        }
    }

    /**
     * Get all saved configurations
     */
    getSavedConfigurations() {
        try {
            const saved = localStorage.getItem(this.STORAGE_KEY);
            return saved ? JSON.parse(saved) : {};
        } catch (error) {
            console.error('Failed to parse saved configurations:', error);
            return {};
        }
    }

    /**
     * Delete a saved configuration
     */
    deleteConfiguration(name) {
        try {
            const savedConfigs = this.getSavedConfigurations();
            if (savedConfigs[name]) {
                delete savedConfigs[name];
                localStorage.setItem(this.STORAGE_KEY, JSON.stringify(savedConfigs));
                eventBus.emit('config:deleted', { name });
                return true;
            }
            return false;
        } catch (error) {
            console.error('Failed to delete configuration:', error);
            return false;
        }
    }

    /**
     * Export configuration as JSON file
     */
    exportConfiguration(config, filename = 'patient-generator-config.json') {
        try {
            const dataStr = JSON.stringify(config, null, 2);
            const dataBlob = new Blob([dataStr], { type: 'application/json' });
            const url = URL.createObjectURL(dataBlob);
            
            const link = document.createElement('a');
            link.href = url;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
            
            eventBus.emit('config:exported', { filename });
            return true;
        } catch (error) {
            console.error('Failed to export configuration:', error);
            return false;
        }
    }

    /**
     * Import configuration from JSON file
     */
    async importConfiguration(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            
            reader.onload = (e) => {
                try {
                    const config = JSON.parse(e.target.result);
                    
                    // Validate the imported configuration
                    if (this.validateImportedConfig(config)) {
                        eventBus.emit('config:imported', { config });
                        resolve(config);
                    } else {
                        reject(new Error('Invalid configuration format'));
                    }
                } catch (error) {
                    reject(error);
                }
            };
            
            reader.onerror = () => reject(new Error('Failed to read file'));
            reader.readAsText(file);
        });
    }

    /**
     * Validate imported configuration structure
     */
    validateImportedConfig(config) {
        // Basic validation - can be expanded
        return config && 
               config.front_configs && 
               Array.isArray(config.front_configs) &&
               config.total_patients &&
               config.injury_distribution;
    }

    /**
     * Save configuration template
     */
    saveTemplate(config, name, description = '') {
        try {
            const templates = this.getTemplates();
            templates[name] = {
                ...config,
                templateName: name,
                description: description,
                createdAt: new Date().toISOString()
            };
            
            localStorage.setItem(this.TEMPLATES_KEY, JSON.stringify(templates));
            eventBus.emit('template:saved', { name, config });
            return true;
        } catch (error) {
            console.error('Failed to save template:', error);
            return false;
        }
    }

    /**
     * Get all templates
     */
    getTemplates() {
        try {
            const saved = localStorage.getItem(this.TEMPLATES_KEY);
            return saved ? JSON.parse(saved) : this.getDefaultTemplates();
        } catch (error) {
            console.error('Failed to parse templates:', error);
            return this.getDefaultTemplates();
        }
    }

    /**
     * Get default configuration templates
     */
    getDefaultTemplates() {
        return {
            'nato-exercise': {
                templateName: 'NATO Exercise',
                description: 'Standard NATO multi-national exercise scenario',
                front_configs: [
                    {
                        id: 'eastern_front',
                        name: 'Eastern Front',
                        casualty_rate: 0.3,
                        nationality_distribution: [
                            { nationality_code: 'POL', percentage: 40 },
                            { nationality_code: 'USA', percentage: 30 },
                            { nationality_code: 'GBR', percentage: 30 }
                        ]
                    },
                    {
                        id: 'northern_front',
                        name: 'Northern Front',
                        casualty_rate: 0.2,
                        nationality_distribution: [
                            { nationality_code: 'FIN', percentage: 50 },
                            { nationality_code: 'SWE', percentage: 30 },
                            { nationality_code: 'NOR', percentage: 20 }
                        ]
                    }
                ],
                total_patients: 500,
                injury_distribution: {
                    'Disease': 40,
                    'Non-Battle Injury': 35,
                    'Battle Injury': 25
                }
            },
            'single-nation': {
                templateName: 'Single Nation Training',
                description: 'Single nation medical training exercise',
                front_configs: [
                    {
                        id: 'training_area',
                        name: 'Training Area',
                        casualty_rate: 0.15,
                        nationality_distribution: [
                            { nationality_code: 'USA', percentage: 100 }
                        ]
                    }
                ],
                total_patients: 200,
                injury_distribution: {
                    'Disease': 50,
                    'Non-Battle Injury': 40,
                    'Battle Injury': 10
                }
            },
            'humanitarian': {
                templateName: 'Humanitarian Mission',
                description: 'Medical support for humanitarian operations',
                front_configs: [
                    {
                        id: 'relief_zone',
                        name: 'Relief Zone',
                        casualty_rate: 0.25,
                        nationality_distribution: [
                            { nationality_code: 'FRA', percentage: 40 },
                            { nationality_code: 'DEU', percentage: 30 },
                            { nationality_code: 'ITA', percentage: 30 }
                        ]
                    }
                ],
                total_patients: 300,
                injury_distribution: {
                    'Disease': 70,
                    'Non-Battle Injury': 25,
                    'Battle Injury': 5
                }
            }
        };
    }

    /**
     * Add current state to undo history
     */
    addToUndoHistory(state) {
        this.undoHistory.push(JSON.stringify(state));
        if (this.undoHistory.length > this.MAX_UNDO_HISTORY) {
            this.undoHistory.shift();
        }
        // Clear redo history when new action is performed
        this.redoHistory = [];
    }

    /**
     * Undo last action
     */
    undo() {
        if (this.undoHistory.length > 1) {
            const currentState = this.undoHistory.pop();
            this.redoHistory.push(currentState);
            const previousState = this.undoHistory[this.undoHistory.length - 1];
            return JSON.parse(previousState);
        }
        return null;
    }

    /**
     * Redo last undone action
     */
    redo() {
        if (this.redoHistory.length > 0) {
            const state = this.redoHistory.pop();
            this.undoHistory.push(state);
            return JSON.parse(state);
        }
        return null;
    }

    /**
     * Save draft configuration
     */
    saveDraft(config) {
        try {
            const drafts = this.getDrafts();
            const draftId = `draft_${Date.now()}`;
            
            // Keep only last 5 drafts
            const draftKeys = Object.keys(drafts).sort().reverse();
            if (draftKeys.length >= 5) {
                draftKeys.slice(4).forEach(key => delete drafts[key]);
            }
            
            drafts[draftId] = {
                ...config,
                savedAt: new Date().toISOString()
            };
            
            localStorage.setItem(this.DRAFTS_KEY, JSON.stringify(drafts));
            return draftId;
        } catch (error) {
            console.error('Failed to save draft:', error);
            return null;
        }
    }

    /**
     * Get all drafts
     */
    getDrafts() {
        try {
            const saved = localStorage.getItem(this.DRAFTS_KEY);
            return saved ? JSON.parse(saved) : {};
        } catch (error) {
            console.error('Failed to parse drafts:', error);
            return {};
        }
    }

    /**
     * Start auto-save
     */
    startAutoSave(getConfigCallback) {
        this.stopAutoSave();
        
        this.autoSaveTimer = setInterval(() => {
            const config = getConfigCallback();
            if (config) {
                this.saveDraft(config);
                eventBus.emit('config:autosaved');
            }
        }, this.autoSaveInterval);
    }

    /**
     * Stop auto-save
     */
    stopAutoSave() {
        if (this.autoSaveTimer) {
            clearInterval(this.autoSaveTimer);
            this.autoSaveTimer = null;
        }
    }

    /**
     * Clear all saved data
     */
    clearAll() {
        localStorage.removeItem(this.STORAGE_KEY);
        localStorage.removeItem(this.DRAFTS_KEY);
        localStorage.removeItem(this.TEMPLATES_KEY);
        this.undoHistory = [];
        this.redoHistory = [];
    }
}

// Export singleton instance
export const configPersistence = new ConfigurationPersistence();