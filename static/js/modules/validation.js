/**
 * Validation Module - Handles all form validation logic
 */
import { debounce } from './utils.js';
import { eventBus } from './events.js';

export class ValidationManager {
    constructor() {
        this.errors = new Map();
        this.validationDelay = 300; // milliseconds
        
        // Create debounced versions of validation methods
        this.debouncedValidateInjury = debounce(
            this.validateInjuryPercentages.bind(this),
            this.validationDelay
        );
        
        this.debouncedValidateFrontCasualty = debounce(
            this.validateOverallFrontCasualtyRates.bind(this),
            this.validationDelay
        );
        
        this.debouncedValidateFrontNationality = debounce(
            this.validateFrontNationalityPercentages.bind(this),
            this.validationDelay
        );
    }

    /**
     * Validate injury percentages sum to 100%
     */
    validateInjuryPercentages() {
        const inputs = document.querySelectorAll('.injury-percent');
        let total = 0;
        
        inputs.forEach(input => {
            total += parseFloat(input.value) || 0;
        });
        
        const errorElement = document.getElementById('injuryPercentError');
        if (Math.abs(total - 100) > 0.1) {
            errorElement?.classList.remove('hidden');
            this.errors.set('injury', 'Percentages must add up to 100%');
            return false;
        } else {
            errorElement?.classList.add('hidden');
            this.errors.delete('injury');
            return true;
        }
    }

    /**
     * Validate overall front casualty rates sum to 100%
     */
    validateOverallFrontCasualtyRates() {
        let totalCasualtyRate = 0;
        const inputs = document.querySelectorAll('.front-casualty-rate');
        
        inputs.forEach(input => {
            totalCasualtyRate += parseFloat(input.value) || 0;
        });
        
        const errorElement = document.getElementById('frontsOverallError');
        if (Math.abs(totalCasualtyRate - 100) > 0.1 && totalCasualtyRate > 0) {
            errorElement?.classList.remove('hidden');
            this.errors.set('frontCasualty', 'Front casualty rates must sum to 100%');
            return false;
        } else {
            errorElement?.classList.add('hidden');
            this.errors.delete('frontCasualty');
            return true;
        }
    }

    /**
     * Validate nationality percentages for a specific front
     */
    validateFrontNationalityPercentages(frontBlockElement) {
        if (!frontBlockElement) return false;
        
        let totalNatPercentage = 0;
        const natErrorDiv = frontBlockElement.querySelector(`#${frontBlockElement.id}-natPercentError`);
        let hasSelectedNationality = false;
        let uniqueNatCodes = new Set();
        let duplicateFound = false;

        frontBlockElement.querySelectorAll('.nationality-block').forEach(nb => {
            const percentageInput = nb.querySelector('.nationality-percentage');
            const codeInput = nb.querySelector('.nationality-code');
            
            totalNatPercentage += parseFloat(percentageInput?.value) || 0;
            if (codeInput?.value) {
                hasSelectedNationality = true;
                if (uniqueNatCodes.has(codeInput.value)) {
                    duplicateFound = true;
                } else {
                    uniqueNatCodes.add(codeInput.value);
                }
            }
        });
        
        let isValid = true;
        const frontId = frontBlockElement.id;
        
        if (duplicateFound) {
            if (natErrorDiv) {
                natErrorDiv.textContent = "Duplicate nationalities selected in this front.";
                natErrorDiv.classList.remove('hidden');
            }
            this.errors.set(`${frontId}-nationality`, 'Duplicate nationalities');
            isValid = false;
        } else if (Math.abs(totalNatPercentage - 100) > 0.1 && hasSelectedNationality) {
            if (natErrorDiv) {
                natErrorDiv.textContent = "Nationality percentages for this front must sum to 100%.";
                natErrorDiv.classList.remove('hidden');
            }
            this.errors.set(`${frontId}-nationality`, 'Percentages must sum to 100%');
            isValid = false;
        } else {
            if (natErrorDiv) natErrorDiv.classList.add('hidden');
            this.errors.delete(`${frontId}-nationality`);
        }
        
        return isValid;
    }

    /**
     * Validate all fronts
     */
    validateAllFronts() {
        let allValid = true;
        
        document.querySelectorAll('.front-block').forEach(frontBlock => {
            if (!this.validateFrontNationalityPercentages(frontBlock)) {
                allValid = false;
            }
        });
        
        if (!this.validateOverallFrontCasualtyRates()) {
            allValid = false;
        }
        
        return allValid;
    }

    /**
     * Validate entire form
     */
    validateForm() {
        const injuryValid = this.validateInjuryPercentages();
        const frontsValid = this.validateAllFronts();
        
        return injuryValid && frontsValid && this.errors.size === 0;
    }

    /**
     * Get all current errors
     */
    getErrors() {
        return Array.from(this.errors.entries());
    }

    /**
     * Clear all errors
     */
    clearErrors() {
        this.errors.clear();
    }
}

// Export singleton instance
export const validationManager = new ValidationManager();