// Template Manager Module

export class TemplateManager {
    constructor(apiClient) {
        this.apiClient = apiClient;
        this.templates = new Map();
        this.builtInTemplates = this.initializeBuiltInTemplates();
    }

    initializeBuiltInTemplates() {
        return {
            'nato': {
                id: 'nato',
                name: 'NATO Exercise',
                description: 'Standard NATO multi-national exercise scenario',
                configuration: {
                    total_patients: 500,
                    exercise_name: 'NATO Exercise 2025',
                    exercise_base_date: new Date().toISOString().split('T')[0],
                    description: 'Multi-national NATO training exercise with coalition forces',
                    
                    medical_facility_defaults: {
                        point_of_injury: {
                            name: 'Point of Injury',
                            capacity: 0,
                            kia_rate: 0.025,
                            rtd_rate: 0.10,
                            description: ''
                        },
                        role_1: {
                            name: 'Role 1 (Battalion Aid)',
                            capacity: 10,
                            kia_rate: 0.01,
                            rtd_rate: 0.15,
                            description: ''
                        },
                        role_2: {
                            name: 'Role 2 (Forward Hospital)',
                            capacity: 50,
                            kia_rate: 0.005,
                            rtd_rate: 0.30,
                            description: ''
                        },
                        role_3: {
                            name: 'Role 3 (Combat Hospital)',
                            capacity: 200,
                            kia_rate: 0.002,
                            rtd_rate: 0.25,
                            description: ''
                        },
                        role_4: {
                            name: 'Role 4 (CONUS Hospital)',
                            capacity: 500,
                            kia_rate: 0.001,
                            rtd_rate: 0.40,
                            description: ''
                        }
                    },
                    
                    fronts: [
                        {
                            id: 'front-1',
                            name: 'Eastern Sector',
                            type: 'Combat',
                            casualty_rate: 0.60,
                            nationality_distribution: {
                                'United States': 40,
                                'United Kingdom': 25,
                                'Germany': 20,
                                'France': 15
                            },
                            medical_facilities: null
                        },
                        {
                            id: 'front-2',
                            name: 'Western Sector',
                            type: 'Combat',
                            casualty_rate: 0.40,
                            nationality_distribution: {
                                'Canada': 30,
                                'Netherlands': 25,
                                'Poland': 25,
                                'Denmark': 20
                            },
                            medical_facilities: null
                        }
                    ],
                    
                    injury_distribution: {
                        'Disease': 40,
                        'Non-Battle Injury': 35,
                        'Battle Trauma': 25
                    },
                    
                    output_formats: ['json', 'xml'],
                    use_compression: true,
                    use_encryption: true,
                    encryption_password: ''
                }
            },
            
            'training': {
                id: 'training',
                name: 'Single Nation Training',
                description: 'Single nation medical training exercise',
                configuration: {
                    total_patients: 200,
                    exercise_name: 'Medical Training Exercise',
                    exercise_base_date: new Date().toISOString().split('T')[0],
                    description: 'Single nation medical training exercise focused on trauma care',
                    
                    fronts: [
                        {
                            id: 'front-1',
                            name: 'Training Area Alpha',
                            type: 'Training',
                            casualty_rate: 1.0,
                            nationality_distribution: {
                                'United States': 100
                            },
                            medical_facilities: null
                        }
                    ],
                    
                    injury_distribution: {
                        'Disease': 30,
                        'Non-Battle Injury': 50,
                        'Battle Trauma': 20
                    },
                    
                    output_formats: ['json'],
                    use_compression: false,
                    use_encryption: false,
                    encryption_password: ''
                }
            },
            
            'humanitarian': {
                id: 'humanitarian',
                name: 'Humanitarian Mission',
                description: 'Humanitarian aid and disaster relief scenario',
                configuration: {
                    total_patients: 1000,
                    exercise_name: 'Humanitarian Aid Mission',
                    exercise_base_date: new Date().toISOString().split('T')[0],
                    description: 'Disaster relief and humanitarian aid operation',
                    
                    fronts: [
                        {
                            id: 'front-1',
                            name: 'Disaster Zone',
                            type: 'Humanitarian',
                            casualty_rate: 1.0,
                            nationality_distribution: {
                                'Local Population': 80,
                                'International Aid Workers': 20
                            },
                            medical_facilities: null
                        }
                    ],
                    
                    injury_distribution: {
                        'Disease': 70,
                        'Non-Battle Injury': 28,
                        'Battle Trauma': 2
                    },
                    
                    output_formats: ['json', 'csv'],
                    use_compression: true,
                    use_encryption: false,
                    encryption_password: ''
                }
            },
            
            'large': {
                id: 'large',
                name: 'Large Scale Operation',
                description: 'Large scale multi-front operation',
                configuration: {
                    total_patients: 2000,
                    exercise_name: 'Large Scale Operation',
                    exercise_base_date: new Date().toISOString().split('T')[0],
                    description: 'Large scale multi-front military operation with extensive medical support',
                    
                    fronts: [
                        {
                            id: 'front-1',
                            name: 'Northern Front',
                            type: 'Combat',
                            casualty_rate: 0.40,
                            nationality_distribution: {
                                'United States': 50,
                                'United Kingdom': 30,
                                'Canada': 20
                            },
                            medical_facilities: null
                        },
                        {
                            id: 'front-2',
                            name: 'Southern Front',
                            type: 'Combat',
                            casualty_rate: 0.35,
                            nationality_distribution: {
                                'France': 40,
                                'Germany': 35,
                                'Italy': 25
                            },
                            medical_facilities: null
                        },
                        {
                            id: 'front-3',
                            name: 'Central Front',
                            type: 'Combat',
                            casualty_rate: 0.25,
                            nationality_distribution: {
                                'Poland': 40,
                                'Netherlands': 30,
                                'Belgium': 30
                            },
                            medical_facilities: null
                        }
                    ],
                    
                    injury_distribution: {
                        'Disease': 35,
                        'Non-Battle Injury': 30,
                        'Battle Trauma': 35
                    },
                    
                    output_formats: ['json', 'xml', 'csv'],
                    use_compression: true,
                    use_encryption: true,
                    encryption_password: ''
                }
            }
        };
    }

    async loadTemplates() {
        try {
            // Load custom templates from API
            const customTemplates = await this.apiClient.getTemplates();
            
            // Combine with built-in templates
            const allTemplates = [
                ...Object.values(this.builtInTemplates),
                ...customTemplates
            ];
            
            // Update internal map
            this.templates.clear();
            allTemplates.forEach(template => {
                this.templates.set(template.id, template);
            });
            
            return allTemplates;
        } catch (error) {
            console.warn('Failed to load custom templates, using built-in only:', error);
            
            // Return only built-in templates
            const builtInArray = Object.values(this.builtInTemplates);
            builtInArray.forEach(template => {
                this.templates.set(template.id, template);
            });
            
            return builtInArray;
        }
    }

    async loadTemplate(templateId) {
        // Check if template is cached
        if (this.templates.has(templateId)) {
            return this.templates.get(templateId);
        }
        
        // Check if it's a built-in template
        if (this.builtInTemplates[templateId]) {
            return this.builtInTemplates[templateId];
        }
        
        // Try to load from API
        try {
            const template = await this.apiClient.getTemplate(templateId);
            this.templates.set(templateId, template);
            return template;
        } catch (error) {
            throw new Error(`Template not found: ${templateId}`);
        }
    }

    async saveTemplate(name, configuration) {
        try {
            const templateData = {
                name,
                description: `Custom template: ${name}`,
                configuration: this.cleanConfiguration(configuration),
                created_at: new Date().toISOString(),
                is_custom: true
            };
            
            const savedTemplate = await this.apiClient.saveTemplate(templateData);
            
            // Add to local cache
            this.templates.set(savedTemplate.id, savedTemplate);
            
            return savedTemplate;
        } catch (error) {
            throw new Error(`Failed to save template: ${error.message}`);
        }
    }

    cleanConfiguration(config) {
        // Remove UI-specific fields and clean up the configuration
        const cleaned = JSON.parse(JSON.stringify(config));
        
        // Remove temporary IDs from fronts
        if (cleaned.fronts) {
            cleaned.fronts.forEach(front => {
                delete front.id;
            });
        }
        
        // Ensure all required fields are present
        if (!cleaned.medical_facility_defaults) {
            cleaned.medical_facility_defaults = this.builtInTemplates.nato.configuration.medical_facility_defaults;
        }
        
        return cleaned;
    }

    getTemplate(templateId) {
        return this.templates.get(templateId) || this.builtInTemplates[templateId];
    }

    getAllTemplates() {
        return Array.from(this.templates.values());
    }

    getBuiltInTemplates() {
        return Object.values(this.builtInTemplates);
    }

    getCustomTemplates() {
        return Array.from(this.templates.values()).filter(t => t.is_custom);
    }

    async deleteTemplate(templateId) {
        // Can't delete built-in templates
        if (this.builtInTemplates[templateId]) {
            throw new Error('Cannot delete built-in templates');
        }
        
        try {
            await this.apiClient.deleteTemplate(templateId);
            this.templates.delete(templateId);
        } catch (error) {
            throw new Error(`Failed to delete template: ${error.message}`);
        }
    }

    async duplicateTemplate(templateId, newName) {
        const original = await this.loadTemplate(templateId);
        if (!original) {
            throw new Error('Template not found');
        }
        
        return this.saveTemplate(newName, original.configuration);
    }

    exportTemplate(templateId) {
        const template = this.getTemplate(templateId);
        if (!template) {
            throw new Error('Template not found');
        }
        
        const exportData = {
            name: template.name,
            description: template.description,
            configuration: template.configuration,
            exported_at: new Date().toISOString(),
            version: '1.0'
        };
        
        return JSON.stringify(exportData, null, 2);
    }

    async importTemplate(templateData) {
        try {
            const parsed = typeof templateData === 'string' ? 
                JSON.parse(templateData) : templateData;
            
            // Validate template structure
            if (!parsed.name || !parsed.configuration) {
                throw new Error('Invalid template format');
            }
            
            // Save as new template
            return this.saveTemplate(parsed.name, parsed.configuration);
        } catch (error) {
            throw new Error(`Failed to import template: ${error.message}`);
        }
    }

    searchTemplates(query) {
        const results = [];
        const searchTerm = query.toLowerCase();
        
        this.templates.forEach(template => {
            if (template.name.toLowerCase().includes(searchTerm) ||
                template.description.toLowerCase().includes(searchTerm)) {
                results.push(template);
            }
        });
        
        return results;
    }

    getTemplateStatistics(templateId) {
        const template = this.getTemplate(templateId);
        if (!template) return null;
        
        const config = template.configuration;
        
        return {
            totalPatients: config.total_patients,
            frontCount: config.fronts ? config.fronts.length : 0,
            nationalityCount: this.countUniqueNationalities(config.fronts),
            injuryTypes: Object.keys(config.injury_distribution || {}),
            outputFormats: config.output_formats || [],
            hasEncryption: config.use_encryption || false,
            hasCompression: config.use_compression || false
        };
    }

    countUniqueNationalities(fronts) {
        const nationalities = new Set();
        
        if (fronts) {
            fronts.forEach(front => {
                if (front.nationality_distribution) {
                    Object.keys(front.nationality_distribution).forEach(nat => {
                        nationalities.add(nat);
                    });
                }
            });
        }
        
        return nationalities.size;
    }

    validateTemplate(template) {
        const errors = [];
        
        if (!template.name) {
            errors.push('Template name is required');
        }
        
        if (!template.configuration) {
            errors.push('Template configuration is required');
        } else {
            // Basic configuration validation
            const config = template.configuration;
            
            if (!config.total_patients || config.total_patients < 1) {
                errors.push('Total patients must be greater than 0');
            }
            
            if (!config.fronts || config.fronts.length === 0) {
                errors.push('At least one front is required');
            }
            
            if (!config.injury_distribution) {
                errors.push('Injury distribution is required');
            }
        }
        
        return {
            isValid: errors.length === 0,
            errors
        };
    }
}