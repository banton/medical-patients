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
        this.validators.set(2, this.validateEvacuationTimes.bind(this));
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

        // Update editor styling
        item.editor.classList.toggle('accordion__editor--invalid', !result.valid);

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
            return { valid: false, message: 'Injury distribution is required' };
        }

        try {
            const config = JSON.parse(content);

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

    validateEvacuationTimes(content) {
        if (!content) {
            return { valid: false, message: 'Evacuation timing configuration is required' };
        }

        try {
            const config = JSON.parse(content);

            // Required top-level sections
            const requiredSections = ['evacuation_times', 'transit_times', 'kia_rate_modifiers', 'rtd_rate_modifiers'];
            const missingSections = requiredSections.filter((section) => !config[section]);
            if (missingSections.length > 0) {
                return { valid: false, message: `Missing required sections: ${missingSections.join(', ')}` };
            }

            // Required facilities and triage categories
            const requiredFacilities = ['POI', 'Role1', 'Role2', 'Role3', 'Role4'];
            const requiredTriageCategories = ['T1', 'T2', 'T3'];
            const requiredTransitRoutes = ['POI_to_Role1', 'Role1_to_Role2', 'Role2_to_Role3', 'Role3_to_Role4'];

            // Validate evacuation_times structure
            for (const facility of requiredFacilities) {
                if (!config.evacuation_times[facility]) {
                    return { valid: false, message: `Missing evacuation times for facility: ${facility}` };
                }

                for (const triage of requiredTriageCategories) {
                    const timeConfig = config.evacuation_times[facility][triage];
                    if (
                        !timeConfig ||
                        typeof timeConfig.min_hours !== 'number' ||
                        typeof timeConfig.max_hours !== 'number'
                    ) {
                        return { valid: false, message: `Invalid time configuration for ${facility} ${triage}` };
                    }

                    if (timeConfig.min_hours < 0 || timeConfig.max_hours < 0) {
                        return { valid: false, message: `Times must be positive for ${facility} ${triage}` };
                    }

                    if (timeConfig.min_hours > timeConfig.max_hours) {
                        return { valid: false, message: `Min time must be ≤ max time for ${facility} ${triage}` };
                    }
                }
            }

            // Validate transit_times structure
            for (const route of requiredTransitRoutes) {
                if (!config.transit_times[route]) {
                    return { valid: false, message: `Missing transit times for route: ${route}` };
                }

                for (const triage of requiredTriageCategories) {
                    const timeConfig = config.transit_times[route][triage];
                    if (
                        !timeConfig ||
                        typeof timeConfig.min_hours !== 'number' ||
                        typeof timeConfig.max_hours !== 'number'
                    ) {
                        return { valid: false, message: `Invalid transit time configuration for ${route} ${triage}` };
                    }

                    if (timeConfig.min_hours < 0 || timeConfig.max_hours < 0) {
                        return { valid: false, message: `Transit times must be positive for ${route} ${triage}` };
                    }

                    if (timeConfig.min_hours > timeConfig.max_hours) {
                        return { valid: false, message: `Min transit time must be ≤ max time for ${route} ${triage}` };
                    }
                }
            }

            // Validate rate modifiers
            for (const triage of requiredTriageCategories) {
                if (typeof config.kia_rate_modifiers[triage] !== 'number' || config.kia_rate_modifiers[triage] < 0) {
                    return {
                        valid: false,
                        message: `Invalid KIA rate modifier for ${triage} (must be positive number)`
                    };
                }

                if (typeof config.rtd_rate_modifiers[triage] !== 'number' || config.rtd_rate_modifiers[triage] < 0) {
                    return {
                        valid: false,
                        message: `Invalid RTD rate modifier for ${triage} (must be positive number)`
                    };
                }
            }

            // Calculate total configured routes and timing ranges
            const totalRoutes = requiredTransitRoutes.length;
            const totalFacilities = requiredFacilities.length;
            const totalConfigurations =
                totalRoutes * requiredTriageCategories.length + totalFacilities * requiredTriageCategories.length;

            return {
                valid: true,
                message: `Valid evacuation configuration: ${totalFacilities} facilities, ${totalRoutes} routes, ${totalConfigurations} timing configurations`
            };
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
