// Configuration Manager Module

export class ConfigurationManager {
    constructor() {
        this.defaultConfig = this.getDefaultConfiguration();
    }

    getDefaultConfiguration() {
        return {
            // Basic settings
            total_patients: 200,
            exercise_name: '',
            exercise_base_date: new Date().toISOString().split('T')[0],
            description: '',
            
            // Medical facility defaults
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
            
            // Fronts
            fronts: [
                {
                    id: 'front-1',
                    name: 'Training Area',
                    type: 'Training',
                    casualty_rate: 1.0,
                    nationality_distribution: {
                        'United States': 100
                    },
                    medical_facilities: null // Uses defaults
                }
            ],
            
            // Injury distribution
            injury_distribution: {
                'Disease': 50,
                'Non-Battle Injury': 40,
                'Battle Trauma': 10
            },
            
            // Output configuration
            output_formats: ['json', 'xml'],
            use_compression: true,
            use_encryption: true,
            encryption_password: ''
        };
    }

    validateConfiguration(config) {
        const errors = [];
        
        // Basic settings validation
        if (!config.total_patients || config.total_patients < 1 || config.total_patients > 10000) {
            errors.push({
                field: 'total_patients',
                message: 'Total patients must be between 1 and 10,000'
            });
        }
        
        if (!config.exercise_base_date) {
            errors.push({
                field: 'exercise_base_date',
                message: 'Exercise base date is required'
            });
        }
        
        // Front validation
        if (!config.fronts || config.fronts.length === 0) {
            errors.push({
                field: 'fronts',
                message: 'At least one front is required'
            });
        } else {
            // Validate each front
            config.fronts.forEach((front, index) => {
                if (!front.name) {
                    errors.push({
                        field: `fronts[${index}].name`,
                        message: `Front ${index + 1} name is required`
                    });
                }
                
                // Validate nationality distribution
                const nationalityTotal = Object.values(front.nationality_distribution || {})
                    .reduce((sum, value) => sum + value, 0);
                
                if (Math.abs(nationalityTotal - 100) > 0.01) {
                    errors.push({
                        field: `fronts[${index}].nationality_distribution`,
                        message: `Front ${index + 1} nationality distribution must sum to 100%`
                    });
                }
                
                // Validate casualty rate
                const totalCasualtyRate = config.fronts.reduce((sum, f) => sum + f.casualty_rate, 0);
                if (Math.abs(totalCasualtyRate - 1.0) > 0.01) {
                    errors.push({
                        field: 'fronts.casualty_rate',
                        message: 'Total casualty rate across all fronts must equal 100%'
                    });
                }
                
                // Validate medical facilities if custom
                if (front.medical_facilities) {
                    this.validateMedicalFacilities(front.medical_facilities, `fronts[${index}]`, errors);
                }
            });
        }
        
        // Validate injury distribution
        const injuryTotal = Object.values(config.injury_distribution || {})
            .reduce((sum, value) => sum + value, 0);
        
        if (Math.abs(injuryTotal - 100) > 0.01) {
            errors.push({
                field: 'injury_distribution',
                message: 'Injury distribution must sum to 100%'
            });
        }
        
        // Validate output formats
        if (!config.output_formats || config.output_formats.length === 0) {
            errors.push({
                field: 'output_formats',
                message: 'At least one output format must be selected'
            });
        }
        
        return {
            isValid: errors.length === 0,
            errors
        };
    }

    validateMedicalFacilities(facilities, prefix, errors) {
        const facilityTypes = ['point_of_injury', 'role_1', 'role_2', 'role_3', 'role_4'];
        
        facilityTypes.forEach(type => {
            const facility = facilities[type];
            if (!facility) {
                errors.push({
                    field: `${prefix}.medical_facilities.${type}`,
                    message: `${type} facility is required`
                });
                return;
            }
            
            // Validate rates
            if (facility.kia_rate < 0 || facility.kia_rate > 1) {
                errors.push({
                    field: `${prefix}.medical_facilities.${type}.kia_rate`,
                    message: `${type} KIA rate must be between 0 and 100%`
                });
            }
            
            if (facility.rtd_rate < 0 || facility.rtd_rate > 1) {
                errors.push({
                    field: `${prefix}.medical_facilities.${type}.rtd_rate`,
                    message: `${type} RTD rate must be between 0 and 100%`
                });
            }
            
            // Warn if combined rates exceed 100%
            if (facility.kia_rate + facility.rtd_rate > 1) {
                errors.push({
                    field: `${prefix}.medical_facilities.${type}`,
                    message: `${type} combined KIA + RTD rates exceed 100%`,
                    severity: 'warning'
                });
            }
            
            // Validate capacity
            if (facility.capacity < 0) {
                errors.push({
                    field: `${prefix}.medical_facilities.${type}.capacity`,
                    message: `${type} capacity must be non-negative`
                });
            }
        });
    }

    mergeWithDefaults(config) {
        // Deep merge configuration with defaults
        const merged = JSON.parse(JSON.stringify(this.defaultConfig));
        
        // Merge basic settings
        Object.assign(merged, {
            total_patients: config.total_patients || merged.total_patients,
            exercise_name: config.exercise_name || merged.exercise_name,
            exercise_base_date: config.exercise_base_date || merged.exercise_base_date,
            description: config.description || merged.description
        });
        
        // Merge fronts
        if (config.fronts) {
            merged.fronts = config.fronts.map(front => ({
                ...front,
                medical_facilities: front.medical_facilities || merged.medical_facility_defaults
            }));
        }
        
        // Merge injury distribution
        if (config.injury_distribution) {
            merged.injury_distribution = config.injury_distribution;
        }
        
        // Merge output configuration
        Object.assign(merged, {
            output_formats: config.output_formats || merged.output_formats,
            use_compression: config.use_compression !== undefined ? config.use_compression : merged.use_compression,
            use_encryption: config.use_encryption !== undefined ? config.use_encryption : merged.use_encryption,
            encryption_password: config.encryption_password || merged.encryption_password
        });
        
        return merged;
    }

    prepareForAPI(config) {
        // Transform configuration for API submission
        // The API expects either configuration_id or configuration object
        
        // First, prepare the configuration in the format expected by the API
        const configTemplate = {
            name: config.exercise_name || `Scenario from Dynamic Front Configuration`,
            description: config.description || `Generated on ${new Date().toISOString()} using dynamic front configuration.`,
            total_patients: config.total_patients,
            
            // Convert fronts to front_configs format
            front_configs: config.fronts.map((front, index) => ({
                id: front.id || `front_${index + 1}_${Date.now()}`,
                name: front.name,
                casualty_rate: front.casualty_rate,
                nationality_distribution: Object.entries(front.nationality_distribution || {}).map(([code, percentage]) => ({
                    nationality_code: this.getCountryCode(code),
                    percentage: percentage
                }))
            })),
            
            // Convert medical facilities to facility_configs format
            facility_configs: this.convertFacilitiesToAPI(config.medical_facility_defaults),
            
            // Convert injury distribution
            injury_distribution: {
                'Disease': config.injury_distribution['Disease'],
                'Battle Injury': config.injury_distribution['Battle Trauma'] || config.injury_distribution['Battle Injury'],
                'Non-Battle Injury': config.injury_distribution['Non-Battle Injury']
            }
        };
        
        // Wrap in generation request format
        const generationRequest = {
            configuration: configTemplate,
            output_formats: config.output_formats,
            use_compression: config.use_compression,
            use_encryption: config.use_encryption,
            encryption_password: config.encryption_password || undefined
        };
        
        // Remove undefined values
        return JSON.parse(JSON.stringify(generationRequest));
    }
    
    convertFacilitiesToAPI(facilities) {
        const facilityMap = {
            'point_of_injury': 'POINT_OF_INJURY',
            'role_1': 'ROLE_1', 
            'role_2': 'ROLE_2',
            'role_3': 'ROLE_3',
            'role_4': 'ROLE_4'
        };
        
        return Object.entries(facilities).map(([key, facility]) => ({
            id: facilityMap[key] || key.toUpperCase(),
            name: facility.name,
            description: facility.description || null,
            capacity: facility.capacity || null,
            kia_rate: facility.kia_rate,
            rtd_rate: facility.rtd_rate
        }));
    }
    
    getCountryCode(countryName) {
        // Map country names to codes
        const countryMap = {
            'United States': 'USA',
            'United Kingdom': 'GBR',
            'Germany': 'DEU',
            'France': 'FRA',
            'Canada': 'CAN',
            'Poland': 'POL',
            'Netherlands': 'NLD',
            'Denmark': 'DNK',
            'Norway': 'NOR',
            'Belgium': 'BEL',
            'Italy': 'ITA',
            'Spain': 'ESP',
            'Portugal': 'PRT',
            'Czech Republic': 'CZE',
            'Slovakia': 'SVK',
            'Hungary': 'HUN',
            'Romania': 'ROU',
            'Bulgaria': 'BGR',
            'Greece': 'GRC',
            'Turkey': 'TUR',
            'Estonia': 'EST',
            'Latvia': 'LVA',
            'Lithuania': 'LTU',
            'Slovenia': 'SVN',
            'Croatia': 'HRV',
            'Albania': 'ALB',
            'Montenegro': 'MNE',
            'North Macedonia': 'MKD',
            'Luxembourg': 'LUX',
            'Iceland': 'ISL',
            'Finland': 'FIN',
            'Sweden': 'SWE',
            'Local Population': 'LOCAL',
            'International Aid Workers': 'INTL'
        };
        
        return countryMap[countryName] || countryName.substring(0, 3).toUpperCase();
    }

    convertNationalityDistribution(distribution) {
        // Convert percentage values to decimals
        const converted = {};
        for (const [nationality, percentage] of Object.entries(distribution)) {
            converted[nationality] = percentage / 100;
        }
        return converted;
    }

    convertInjuryDistribution(distribution) {
        // Convert percentage values to decimals
        const converted = {};
        for (const [type, percentage] of Object.entries(distribution)) {
            converted[type] = percentage / 100;
        }
        return converted;
    }
}