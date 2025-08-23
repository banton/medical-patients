/**
 * Accordion Component
 * Manages vertical accordion behavior for configuration sections
 */

/* eslint no-console: "off", max-len: "off" */

class AccordionComponent {
    constructor(container) {
        this.container = container;
        this.items = [];
        this.activeIndex = -1;
        this.validators = new Map();

        this.init();
    }

    init() {
        this.setupItems();
        this.bindEvents();
        this.setupValidation();

        // Set initial state - first item expanded
        this.expand(0);

        // Validate all items with default content on initialization
        this.validateAllItems();
    }

    setupItems() {
        const itemElements = this.container.querySelectorAll('.accordion__item');

        itemElements.forEach((element, index) => {
            const header = element.querySelector('.accordion__header');
            const content = element.querySelector('.accordion__content');
            const editor = element.querySelector('.accordion__editor');
            const status = element.querySelector('.accordion__status');
            const validation = element.querySelector('.accordion__validation');

            this.items.push({
                element,
                header,
                content,
                editor,
                status,
                validation,
                index,
                isValid: null // null = unknown, true = valid, false = invalid
            });

            // Set up ARIA attributes
            header.setAttribute('aria-expanded', 'false');
            header.setAttribute('aria-controls', `accordion-content-${index}`);
            content.setAttribute('id', `accordion-content-${index}`);

            // Ensure editor has proper ID for accessibility
            if (editor && !editor.id) {
                editor.id = `accordion-editor-${index}`;
            }
        });
    }

    bindEvents() {
        this.items.forEach((item, index) => {
            // Click events
            item.header.addEventListener('click', () => {
                this.toggle(index);
            });

            // Keyboard events
            item.header.addEventListener('keydown', (e) => {
                this.handleKeyDown(e, index);
            });

            // Editor input events for validation
            if (item.editor) {
                item.editor.addEventListener('input', () => {
                    this.validateItem(index);
                });

                item.editor.addEventListener('blur', () => {
                    this.validateItem(index);
                });
            }
        });
    }

    setupValidation() {
        // Set up JSON validators for each section
        this.validators.set(0, this.validateBattleFronts.bind(this));
        this.validators.set(1, this.validateInjuries.bind(this));
        this.validators.set(2, this.validateMedicalSimulation.bind(this)); // Medical Simulation Settings
        this.validators.set(3, this.validateAdvancedConfig.bind(this)); // Advanced Configuration
    }

    handleKeyDown(e, index) {
        switch (e.key) {
            case 'Enter':
            case ' ':
                e.preventDefault();
                this.toggle(index);
                break;
            case 'ArrowDown':
                e.preventDefault();
                this.focusNext(index);
                break;
            case 'ArrowUp':
                e.preventDefault();
                this.focusPrevious(index);
                break;
            case 'Home':
                e.preventDefault();
                this.items[0].header.focus();
                break;
            case 'End':
                e.preventDefault();
                this.items[this.items.length - 1].header.focus();
                break;
        }
    }

    focusNext(currentIndex) {
        const nextIndex = (currentIndex + 1) % this.items.length;
        this.items[nextIndex].header.focus();
    }

    focusPrevious(currentIndex) {
        const prevIndex = currentIndex === 0 ? this.items.length - 1 : currentIndex - 1;
        this.items[prevIndex].header.focus();
    }

    toggle(index) {
        if (this.activeIndex === index) {
            // Collapse if clicking active item
            this.collapse(index);
        } else {
            // Expand new item (this will auto-collapse others)
            this.expand(index);
        }
    }

    expand(index) {
        // Collapse all other items first
        this.items.forEach((item, i) => {
            if (i !== index) {
                this.collapse(i);
            }
        });

        const item = this.items[index];

        // Expand the selected item
        item.header.classList.add('accordion__header--active');
        item.content.classList.add('accordion__content--expanded');
        item.header.setAttribute('aria-expanded', 'true');

        this.activeIndex = index;

        // Focus the editor when section opens
        if (item.editor) {
            setTimeout(() => {
                item.editor.focus();
            }, 100);
        }

        // Validate the content
        this.validateItem(index);

        // Emit custom event
        this.container.dispatchEvent(
            new CustomEvent('accordion:expand', {
                detail: { index, item }
            })
        );
    }

    collapse(index) {
        const item = this.items[index];

        item.header.classList.remove('accordion__header--active');
        item.content.classList.remove('accordion__content--expanded');
        item.header.setAttribute('aria-expanded', 'false');

        if (this.activeIndex === index) {
            this.activeIndex = -1;
        }

        // Emit custom event
        this.container.dispatchEvent(
            new CustomEvent('accordion:collapse', {
                detail: { index, item }
            })
        );
    }

    validateItem(index) {
        const item = this.items[index];
        const validator = this.validators.get(index);

        // Special handling for Medical Simulation Settings (index 2) - no editor, uses checkboxes
        // and Advanced Configuration (index 3) - optional section with default valid state
        if (index === 2 || index === 3) {
            if (!validator) {
                return;
            }

            // For Advanced Config, use editor content if available, otherwise empty string
            let content = '';
            if (index === 3 && item.editor) {
                content = item.editor.value.trim();
            }

            const result = validator(content);
            this.updateValidationUI(index, result);
            item.isValid = result.valid;
            // Emit validation event
            this.container.dispatchEvent(
                new CustomEvent('accordion:validate', {
                    detail: { index, result, item }
                })
            );
            return;
        }

        if (!item.editor || !validator) {
            return;
        }

        const content = item.editor.value.trim();
        const result = validator(content);

        this.updateValidationUI(index, result);
        item.isValid = result.valid;

        // Emit validation event
        this.container.dispatchEvent(
            new CustomEvent('accordion:validate', {
                detail: { index, result, item }
            })
        );
    }

    updateValidationUI(index, result) {
        const item = this.items[index];

        // Update status indicator
        item.status.className = 'accordion__status';
        if (result.valid) {
            item.status.classList.add('accordion__status--valid');
            item.status.textContent = '✓';
        } else {
            item.status.classList.add('accordion__status--invalid');
            item.status.textContent = '✗';
        }

        // Update editor styling (only if editor exists)
        if (item.editor) {
            item.editor.classList.toggle('accordion__editor--invalid', !result.valid);
        }

        // Update validation message
        if (item.validation) {
            item.validation.className = 'accordion__validation';

            if (result.valid) {
                item.validation.classList.add('accordion__validation--success');
                item.validation.textContent = result.message || 'Configuration is valid';
            } else {
                item.validation.classList.add('accordion__validation--error');
                item.validation.textContent = result.message || 'Invalid configuration';
            }
        }
    }

    // Validation methods for each section

    validateBattleFronts(content) {
        if (!content) {
            return { valid: false, message: 'Battle fronts configuration is required' };
        }

        try {
            const config = JSON.parse(content);

            if (!Array.isArray(config.front_configs)) {
                return { valid: false, message: 'Missing or invalid "front_configs" array' };
            }

            if (config.front_configs.length === 0) {
                return { valid: false, message: 'At least one battle front must be configured' };
            }

            // Calculate total casualty rate across all fronts
            let totalCasualtyRate = 0;

            // Validate each front
            for (const front of config.front_configs) {
                if (!front.id || !front.name) {
                    return { valid: false, message: 'Each front must have "id" and "name"' };
                }

                // Validate casualty rate
                if (typeof front.casualty_rate !== 'number' || front.casualty_rate < 0 || front.casualty_rate > 1) {
                    return { valid: false, message: `Front "${front.name}" has invalid casualty_rate (must be 0-1)` };
                }
                totalCasualtyRate += front.casualty_rate;

                // Validate nationality distribution
                if (!front.nationality_distribution || !Array.isArray(front.nationality_distribution)) {
                    return { valid: false, message: `Front "${front.name}" missing nationality distribution` };
                }

                // Check nationality distribution percentages total 100%
                let totalPercentage = 0;
                for (const natDist of front.nationality_distribution) {
                    if (!natDist.nationality_code || typeof natDist.percentage !== 'number') {
                        return {
                            valid: false,
                            message: `Front "${front.name}" has invalid nationality distribution format`
                        };
                    }
                    if (natDist.percentage < 0 || natDist.percentage > 100) {
                        return {
                            valid: false,
                            message: `Front "${front.name}" has invalid percentage for ${natDist.nationality_code} (must be 0-100)`
                        };
                    }
                    totalPercentage += natDist.percentage;
                }

                // Allow small tolerance for floating point precision
                if (Math.abs(totalPercentage - 100) > 0.01) {
                    return {
                        valid: false,
                        message: `Front "${front.name}" nationality percentages total ${totalPercentage.toFixed(1)}% (must equal 100%)`
                    };
                }
            }

            // Check total casualty rate equals 1.0 (100%)
            if (Math.abs(totalCasualtyRate - 1.0) > 0.01) {
                return {
                    valid: false,
                    message: `Total casualty rate is ${(totalCasualtyRate * 100).toFixed(1)}% (must equal 100%)`
                };
            }

            return { valid: true, message: `${config.front_configs.length} battle fronts configured with valid rates` };
        } catch (e) {
            return { valid: false, message: `JSON syntax error: ${e.message}` };
        }
    }

    validateInjuries(content) {
        if (!content) {
            return { valid: false, message: 'Scenario configuration is required' };
        }

        try {
            const config = JSON.parse(content);

            // Check if this is simplified scenario format (injury_mix) or legacy format (injury_distribution)
            const hasInjuryMix = config.injury_mix && typeof config.injury_mix === 'object';

            if (hasInjuryMix || config.base_date || config.days_of_fighting) {
                // Validate scenario configuration
                if (!config.total_patients || typeof config.total_patients !== 'number' || config.total_patients < 1) {
                    return { valid: false, message: 'total_patients must be a positive number' };
                }

                if (
                    config.days_of_fighting &&
                    (typeof config.days_of_fighting !== 'number' || config.days_of_fighting < 1)
                ) {
                    return { valid: false, message: 'days_of_fighting must be a positive number' };
                }

                if (config.intensity && !['low', 'medium', 'high', 'extreme'].includes(config.intensity)) {
                    return { valid: false, message: 'intensity must be one of: low, medium, high, extreme' };
                }

                if (
                    config.tempo &&
                    !['sustained', 'escalating', 'surge', 'declining', 'intermittent'].includes(config.tempo)
                ) {
                    return {
                        valid: false,
                        message: 'tempo must be one of: sustained, escalating, surge, declining, intermittent'
                    };
                }

                // Validate injury_mix if present
                if (config.injury_mix) {
                    const requiredTypes = ['Disease', 'Non-Battle Injury', 'Battle Injury'];
                    const missing = requiredTypes.filter((type) => !(type in config.injury_mix));

                    if (missing.length > 0) {
                        return { valid: false, message: `Missing injury types in injury_mix: ${missing.join(', ')}` };
                    }

                    const total = Object.values(config.injury_mix).reduce((sum, val) => sum + (val || 0), 0);
                    if (Math.abs(total - 1) > 0.01) {
                        return {
                            valid: false,
                            message: `Injury mix percentages should sum to 1.0 (currently ${total.toFixed(2)})`
                        };
                    }
                }

                return { valid: true, message: 'Scenario configuration is valid' };
            }

            // Legacy format validation
            if (!config.injury_distribution || typeof config.injury_distribution !== 'object') {
                return { valid: false, message: 'Missing or invalid "injury_distribution" object' };
            }

            // Check for required injury types
            const requiredTypes = ['Disease', 'Non-Battle Injury', 'Battle Injury'];
            const missing = requiredTypes.filter((type) => !(type in config.injury_distribution));

            if (missing.length > 0) {
                return { valid: false, message: `Missing injury types: ${missing.join(', ')}` };
            }

            // Check if percentages are valid
            const total = Object.values(config.injury_distribution).reduce((sum, val) => sum + (val || 0), 0);
            if (Math.abs(total - 1) > 0.01) {
                return {
                    valid: false,
                    message: `Injury percentages should sum to 1.0 (currently ${total.toFixed(2)})`
                };
            }

            return { valid: true, message: 'Injury distribution is properly configured' };
        } catch (e) {
            return { valid: false, message: `JSON syntax error: ${e.message}` };
        }
    }

    validateMedicalSimulation(content) {
        // Medical Simulation Settings don't need JSON validation - they use checkboxes
        // This section is always valid
        return { valid: true, message: 'Medical simulation settings configured' };
    }

    validateAdvancedConfig(content) {
        // Advanced configuration is optional - empty is valid
        if (!content || content.trim() === '') {
            return { valid: true, message: 'Using default medical simulation parameters' };
        }

        try {
            const config = JSON.parse(content);

            // Validate treatment effectiveness if provided
            if (config.treatment_effectiveness) {
                for (const [treatment, value] of Object.entries(config.treatment_effectiveness)) {
                    if (treatment === 'description') {
                        continue;
                    }
                    if (typeof value !== 'number' || value < 0 || value > 1) {
                        return {
                            valid: false,
                            message: `Invalid treatment effectiveness for ${treatment} (must be 0.0-1.0)`
                        };
                    }
                }
            }

            // Validate diagnostic accuracy if provided
            if (config.diagnostic_accuracy) {
                for (const [facility, value] of Object.entries(config.diagnostic_accuracy)) {
                    if (facility === 'description') {
                        continue;
                    }
                    if (typeof value !== 'number' || value < 0 || value > 1) {
                        return {
                            valid: false,
                            message: `Invalid diagnostic accuracy for ${facility} (must be 0.0-1.0)`
                        };
                    }
                }
            }

            // Validate markov overrides if provided
            if (config.markov_overrides) {
                for (const [transition, value] of Object.entries(config.markov_overrides)) {
                    if (transition === 'description') continue;
                    if (value !== null && (typeof value !== 'number' || value < 0 || value > 1)) {
                        return {
                            valid: false,
                            message: `Invalid markov override for ${transition} (must be null or 0.0-1.0)`
                        };
                    }
                }
            }

            // Validate polytrauma rates if provided
            if (config.polytrauma_rates) {
                for (const [warfareType, value] of Object.entries(config.polytrauma_rates)) {
                    if (warfareType === 'description') continue;
                    if (typeof value !== 'number' || value < 0 || value > 1) {
                        return {
                            valid: false,
                            message: `Invalid polytrauma rate for ${warfareType} (must be 0.0-1.0)`
                        };
                    }
                }
            }

            return { valid: true, message: 'Advanced configuration is valid' };
        } catch (e) {
            return { valid: false, message: `JSON syntax error: ${e.message}` };
        }
    }

    // Public API methods
    getActiveIndex() {
        return this.activeIndex;
    }

    getItemValidation(index) {
        return this.items[index]?.isValid;
    }

    getAllValidation() {
        return this.items.map((item) => item.isValid);
    }

    isAllValid() {
        return this.items.every((item) => item.isValid === true);
    }

    setContent(index, content) {
        const item = this.items[index];
        if (item?.editor) {
            item.editor.value = content;
            this.validateItem(index);
        }
    }

    getContent(index) {
        const item = this.items[index];
        return item?.editor?.value || '';
    }

    getAllContent() {
        return this.items.map((item) => item.editor?.value || '');
    }

    validateAllItems() {
        this.items.forEach((item, index) => {
            this.validateItem(index);
        });

        // Emit a global validation event for the app to catch
        this.container.dispatchEvent(
            new CustomEvent('accordion:validate', {
                detail: {
                    allValid: this.isAllValid(),
                    validationStates: this.getAllValidation()
                }
            })
        );
    }
}

// Initialize accordion when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const accordionContainer = document.querySelector('.accordion');
    if (accordionContainer) {
        window.accordion = new AccordionComponent(accordionContainer);
        // console.log('🎵 Accordion component initialized');
    }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AccordionComponent;
}
