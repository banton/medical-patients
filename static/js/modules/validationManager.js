// Validation Manager Module

export class ValidationManager {
    constructor() {
        this.rules = this.initializeValidationRules();
    }

    initializeValidationRules() {
        return {
            total_patients: {
                required: true,
                min: 1,
                max: 10000,
                type: 'number'
            },
            exercise_base_date: {
                required: true,
                type: 'date'
            },
            exercise_name: {
                required: false,
                maxLength: 255
            },
            description: {
                required: false,
                maxLength: 1000
            },
            fronts: {
                required: true,
                minItems: 1,
                items: {
                    name: { required: true, maxLength: 100 },
                    type: { required: true },
                    casualty_rate: { required: true, min: 0, max: 1, type: 'number' },
                    nationality_distribution: { required: true, sumTo: 100 }
                }
            },
            injury_distribution: {
                required: true,
                sumTo: 100
            },
            output_formats: {
                required: true,
                minItems: 1
            },
            medical_facilities: {
                required: true,
                facilities: ['point_of_injury', 'role_1', 'role_2', 'role_3', 'role_4'],
                facilityRules: {
                    capacity: { required: true, min: 0, type: 'number' },
                    kia_rate: { required: true, min: 0, max: 1, type: 'number' },
                    rtd_rate: { required: true, min: 0, max: 1, type: 'number' },
                    combined_rates_warning: { max: 1 }
                }
            }
        };
    }

    validateConfiguration(config) {
        const errors = [];
        const warnings = [];

        // Basic validation
        this.validateBasicSettings(config, errors);
        
        // Front validation
        this.validateFronts(config, errors, warnings);
        
        // Injury distribution validation
        this.validateInjuryDistribution(config, errors);
        
        // Output formats validation
        this.validateOutputFormats(config, errors);
        
        // Cross-validation checks
        this.validateCrossConstraints(config, errors, warnings);

        return {
            isValid: errors.length === 0,
            errors,
            warnings
        };
    }

    validateBasicSettings(config, errors) {
        // Total patients
        if (!config.total_patients) {
            errors.push({
                field: 'total_patients',
                message: 'Total patients is required',
                code: 'REQUIRED'
            });
        } else if (config.total_patients < 1 || config.total_patients > 10000) {
            errors.push({
                field: 'total_patients',
                message: 'Total patients must be between 1 and 10,000',
                code: 'OUT_OF_RANGE'
            });
        }

        // Exercise base date
        if (!config.exercise_base_date) {
            errors.push({
                field: 'exercise_base_date',
                message: 'Exercise base date is required',
                code: 'REQUIRED'
            });
        } else if (!this.isValidDate(config.exercise_base_date)) {
            errors.push({
                field: 'exercise_base_date',
                message: 'Exercise base date must be a valid date',
                code: 'INVALID_FORMAT'
            });
        }

        // Exercise name length
        if (config.exercise_name && config.exercise_name.length > 255) {
            errors.push({
                field: 'exercise_name',
                message: 'Exercise name cannot exceed 255 characters',
                code: 'TOO_LONG'
            });
        }

        // Description length
        if (config.description && config.description.length > 1000) {
            errors.push({
                field: 'description',
                message: 'Description cannot exceed 1000 characters',
                code: 'TOO_LONG'
            });
        }
    }

    validateFronts(config, errors, warnings) {
        if (!config.fronts || config.fronts.length === 0) {
            errors.push({
                field: 'fronts',
                message: 'At least one front is required',
                code: 'REQUIRED'
            });
            return;
        }

        // Check for duplicate front names
        const frontNames = config.fronts.map(f => f.name.toLowerCase());
        const duplicates = frontNames.filter((name, index) => frontNames.indexOf(name) !== index);
        if (duplicates.length > 0) {
            errors.push({
                field: 'fronts',
                message: 'Front names must be unique',
                code: 'DUPLICATE_VALUES'
            });
        }

        // Validate each front
        config.fronts.forEach((front, index) => {
            this.validateFront(front, index, errors, warnings);
        });

        // Validate total casualty rate
        const totalCasualtyRate = config.fronts.reduce((sum, f) => sum + (f.casualty_rate || 0), 0);
        if (Math.abs(totalCasualtyRate - 1.0) > 0.001) {
            errors.push({
                field: 'fronts.casualty_rate',
                message: `Total casualty rate across all fronts must equal 100% (currently ${Math.round(totalCasualtyRate * 100)}%)`,
                code: 'INVALID_SUM'
            });
        }
    }

    validateFront(front, index, errors, warnings) {
        const prefix = `fronts[${index}]`;

        // Front name
        if (!front.name || front.name.trim() === '') {
            errors.push({
                field: `${prefix}.name`,
                message: `Front ${index + 1} name is required`,
                code: 'REQUIRED'
            });
        }

        // Casualty rate
        if (front.casualty_rate === undefined || front.casualty_rate === null) {
            errors.push({
                field: `${prefix}.casualty_rate`,
                message: `Front ${index + 1} casualty rate is required`,
                code: 'REQUIRED'
            });
        } else if (front.casualty_rate < 0 || front.casualty_rate > 1) {
            errors.push({
                field: `${prefix}.casualty_rate`,
                message: `Front ${index + 1} casualty rate must be between 0% and 100%`,
                code: 'OUT_OF_RANGE'
            });
        }

        // Nationality distribution
        if (!front.nationality_distribution || Object.keys(front.nationality_distribution).length === 0) {
            errors.push({
                field: `${prefix}.nationality_distribution`,
                message: `Front ${index + 1} must have at least one nationality`,
                code: 'REQUIRED'
            });
        } else {
            this.validateNationalityDistribution(front.nationality_distribution, prefix, errors, warnings);
        }

        // Medical facilities (if custom)
        if (front.medical_facilities) {
            this.validateMedicalFacilities(front.medical_facilities, prefix, errors, warnings);
        }
    }

    validateNationalityDistribution(distribution, prefix, errors, warnings) {
        const total = Object.values(distribution).reduce((sum, value) => sum + (value || 0), 0);
        
        if (Math.abs(total - 100) > 0.01) {
            errors.push({
                field: `${prefix}.nationality_distribution`,
                message: `Nationality distribution must sum to 100% (currently ${total.toFixed(1)}%)`,
                code: 'INVALID_SUM'
            });
        }

        // Check for zero or negative percentages
        Object.entries(distribution).forEach(([nationality, percentage]) => {
            if (percentage <= 0) {
                errors.push({
                    field: `${prefix}.nationality_distribution`,
                    message: `${nationality} percentage must be greater than 0%`,
                    code: 'OUT_OF_RANGE'
                });
            }
        });
    }

    validateMedicalFacilities(facilities, prefix, errors, warnings) {
        const requiredFacilities = ['point_of_injury', 'role_1', 'role_2', 'role_3', 'role_4'];
        
        requiredFacilities.forEach(facilityType => {
            const facility = facilities[facilityType];
            
            if (!facility) {
                errors.push({
                    field: `${prefix}.medical_facilities.${facilityType}`,
                    message: `${this.getFacilityDisplayName(facilityType)} is required`,
                    code: 'REQUIRED'
                });
                return;
            }

            this.validateFacility(facility, `${prefix}.medical_facilities.${facilityType}`, facilityType, errors, warnings);
        });
    }

    validateFacility(facility, prefix, facilityType, errors, warnings) {
        const displayName = this.getFacilityDisplayName(facilityType);

        // Capacity
        if (facility.capacity === undefined || facility.capacity === null) {
            errors.push({
                field: `${prefix}.capacity`,
                message: `${displayName} capacity is required`,
                code: 'REQUIRED'
            });
        } else if (facility.capacity < 0) {
            errors.push({
                field: `${prefix}.capacity`,
                message: `${displayName} capacity must be non-negative`,
                code: 'OUT_OF_RANGE'
            });
        }

        // KIA rate
        if (facility.kia_rate === undefined || facility.kia_rate === null) {
            errors.push({
                field: `${prefix}.kia_rate`,
                message: `${displayName} KIA rate is required`,
                code: 'REQUIRED'
            });
        } else if (facility.kia_rate < 0 || facility.kia_rate > 1) {
            errors.push({
                field: `${prefix}.kia_rate`,
                message: `${displayName} KIA rate must be between 0% and 100%`,
                code: 'OUT_OF_RANGE'
            });
        }

        // RTD rate
        if (facility.rtd_rate === undefined || facility.rtd_rate === null) {
            errors.push({
                field: `${prefix}.rtd_rate`,
                message: `${displayName} RTD rate is required`,
                code: 'REQUIRED'
            });
        } else if (facility.rtd_rate < 0 || facility.rtd_rate > 1) {
            errors.push({
                field: `${prefix}.rtd_rate`,
                message: `${displayName} RTD rate must be between 0% and 100%`,
                code: 'OUT_OF_RANGE'
            });
        }

        // Combined rates warning
        if (facility.kia_rate && facility.rtd_rate && (facility.kia_rate + facility.rtd_rate > 1)) {
            warnings.push({
                field: `${prefix}`,
                message: `${displayName} combined KIA + RTD rates exceed 100% (${Math.round((facility.kia_rate + facility.rtd_rate) * 100)}%)`,
                code: 'COMBINED_RATES_HIGH',
                severity: 'warning'
            });
        }
    }

    validateInjuryDistribution(config, errors) {
        if (!config.injury_distribution) {
            errors.push({
                field: 'injury_distribution',
                message: 'Injury distribution is required',
                code: 'REQUIRED'
            });
            return;
        }

        const requiredTypes = ['Disease', 'Non-Battle Injury', 'Battle Trauma'];
        const total = Object.values(config.injury_distribution).reduce((sum, value) => sum + (value || 0), 0);

        // Check if all types are present
        requiredTypes.forEach(type => {
            if (!(type in config.injury_distribution)) {
                errors.push({
                    field: 'injury_distribution',
                    message: `${type} percentage is required`,
                    code: 'MISSING_TYPE'
                });
            }
        });

        // Check total equals 100%
        if (Math.abs(total - 100) > 0.01) {
            errors.push({
                field: 'injury_distribution',
                message: `Injury distribution must sum to 100% (currently ${total.toFixed(1)}%)`,
                code: 'INVALID_SUM'
            });
        }

        // Check individual values
        Object.entries(config.injury_distribution).forEach(([type, percentage]) => {
            if (percentage < 0 || percentage > 100) {
                errors.push({
                    field: 'injury_distribution',
                    message: `${type} percentage must be between 0% and 100%`,
                    code: 'OUT_OF_RANGE'
                });
            }
        });
    }

    validateOutputFormats(config, errors) {
        if (!config.output_formats || config.output_formats.length === 0) {
            errors.push({
                field: 'output_formats',
                message: 'At least one output format must be selected',
                code: 'REQUIRED'
            });
        }

        const validFormats = ['json', 'xml', 'csv'];
        if (config.output_formats) {
            config.output_formats.forEach(format => {
                if (!validFormats.includes(format)) {
                    errors.push({
                        field: 'output_formats',
                        message: `Invalid output format: ${format}`,
                        code: 'INVALID_VALUE'
                    });
                }
            });
        }
    }

    validateCrossConstraints(config, errors, warnings) {
        // Encryption password validation
        if (config.use_encryption && config.encryption_password) {
            const passwordStrength = this.checkPasswordStrength(config.encryption_password);
            if (passwordStrength.score < 3) {
                warnings.push({
                    field: 'encryption_password',
                    message: `Weak encryption password: ${passwordStrength.feedback}`,
                    code: 'WEAK_PASSWORD',
                    severity: 'warning'
                });
            }
        }

        // Check for logical inconsistencies
        if (config.total_patients && config.fronts) {
            const totalCasualtyCapacity = config.fronts.reduce((sum, front) => {
                if (front.medical_facilities) {
                    return sum + Object.values(front.medical_facilities).reduce((fSum, facility) => 
                        fSum + (facility.capacity || 0), 0);
                }
                return sum;
            }, 0);

            if (totalCasualtyCapacity > 0 && config.total_patients > totalCasualtyCapacity * 10) {
                warnings.push({
                    field: 'total_patients',
                    message: `Total patients (${config.total_patients}) significantly exceeds medical facility capacity (${totalCasualtyCapacity})`,
                    code: 'CAPACITY_MISMATCH',
                    severity: 'warning'
                });
            }
        }
    }

    // Utility methods
    isValidDate(dateString) {
        const date = new Date(dateString);
        return date instanceof Date && !isNaN(date);
    }

    getFacilityDisplayName(facilityType) {
        const names = {
            'point_of_injury': 'Point of Injury',
            'role_1': 'Role 1',
            'role_2': 'Role 2', 
            'role_3': 'Role 3',
            'role_4': 'Role 4'
        };
        return names[facilityType] || facilityType;
    }

    checkPasswordStrength(password) {
        let score = 0;
        const feedback = [];

        if (password.length >= 8) score++;
        else feedback.push('use at least 8 characters');

        if (password.match(/[a-z]/)) score++;
        else feedback.push('include lowercase letters');

        if (password.match(/[A-Z]/)) score++;
        else feedback.push('include uppercase letters');

        if (password.match(/[0-9]/)) score++;
        else feedback.push('include numbers');

        if (password.match(/[^a-zA-Z0-9]/)) score++;
        else feedback.push('include special characters');

        return {
            score,
            feedback: feedback.join(', ')
        };
    }

    // Real-time validation helpers
    validateField(fieldPath, value, config = {}) {
        const errors = [];
        
        // Field-specific validation logic
        switch (fieldPath) {
            case 'total_patients':
                if (!value || value < 1 || value > 10000) {
                    errors.push('Must be between 1 and 10,000');
                }
                break;
                
            case 'exercise_base_date':
                if (!value || !this.isValidDate(value)) {
                    errors.push('Must be a valid date');
                }
                break;
                
            // Add more field-specific validations as needed
        }
        
        return errors;
    }

    getValidationMessage(errorCode, context = {}) {
        const messages = {
            'REQUIRED': 'This field is required',
            'OUT_OF_RANGE': 'Value is outside the allowed range',
            'INVALID_FORMAT': 'Invalid format',
            'TOO_LONG': 'Value is too long',
            'DUPLICATE_VALUES': 'Duplicate values are not allowed',
            'INVALID_SUM': 'Values do not sum to the required total',
            'MISSING_TYPE': 'Required type is missing',
            'INVALID_VALUE': 'Invalid value',
            'WEAK_PASSWORD': 'Password is too weak',
            'CAPACITY_MISMATCH': 'Capacity may be insufficient',
            'COMBINED_RATES_HIGH': 'Combined rates are unusually high'
        };
        
        return messages[errorCode] || 'Validation error';
    }
}