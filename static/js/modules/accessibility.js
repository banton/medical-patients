/**
 * Accessibility Manager
 * Handles keyboard navigation, ARIA attributes, and screen reader support
 */

export class AccessibilityManager {
    constructor(eventBus) {
        this.eventBus = eventBus;
        this.focusableSelector = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
        this.tooltips = new Map();
        this.ariaLiveRegion = null;
    }

    init() {
        this.setupKeyboardNavigation();
        this.setupAriaAttributes();
        this.createAriaLiveRegion();
        this.setupTooltips();
        this.makeResponsive();
        this.bindEvents();
    }

    setupKeyboardNavigation() {
        // Global keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + S to save
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault();
                document.getElementById('saveConfigBtn')?.click();
            }
            
            // Ctrl/Cmd + O to load
            if ((e.ctrlKey || e.metaKey) && e.key === 'o') {
                e.preventDefault();
                document.getElementById('loadConfigBtn')?.click();
            }
            
            // Ctrl/Cmd + Z to undo
            if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
                e.preventDefault();
                document.getElementById('undoBtn')?.click();
            }
            
            // Ctrl/Cmd + Shift + Z to redo
            if ((e.ctrlKey || e.metaKey) && e.key === 'z' && e.shiftKey) {
                e.preventDefault();
                document.getElementById('redoBtn')?.click();
            }
            
            // Escape to close modals
            if (e.key === 'Escape') {
                const openModal = document.querySelector('.modal.show');
                if (openModal) {
                    bootstrap.Modal.getInstance(openModal)?.hide();
                }
            }
            
            // Tab navigation within fronts
            if (e.key === 'Tab') {
                this.handleTabNavigation(e);
            }
        });

        // Focus management for dynamic content
        this.eventBus.on('front-added', (data) => {
            setTimeout(() => {
                const newFront = document.querySelector(`[data-front-index="${data.index}"]`);
                if (newFront) {
                    const firstInput = newFront.querySelector('input');
                    firstInput?.focus();
                }
            }, 100);
        });

        this.eventBus.on('nationality-added', (data) => {
            setTimeout(() => {
                const newNationality = document.querySelector(`[data-front-index="${data.frontIndex}"] [data-nationality-index="${data.nationalityIndex}"]`);
                if (newNationality) {
                    const select = newNationality.querySelector('select');
                    select?.focus();
                }
            }, 100);
        });
    }

    handleTabNavigation(e) {
        const focusableElements = document.querySelectorAll(this.focusableSelector);
        const focusArray = Array.from(focusableElements).filter(el => !el.disabled && el.offsetParent !== null);
        const currentIndex = focusArray.indexOf(document.activeElement);
        
        if (currentIndex === -1) return;
        
        let nextIndex;
        if (e.shiftKey) {
            nextIndex = currentIndex === 0 ? focusArray.length - 1 : currentIndex - 1;
        } else {
            nextIndex = currentIndex === focusArray.length - 1 ? 0 : currentIndex + 1;
        }
        
        // Skip to next section if at end of a front block
        const currentFront = document.activeElement.closest('.front-block');
        const nextElement = focusArray[nextIndex];
        const nextFront = nextElement?.closest('.front-block');
        
        if (currentFront && nextFront && currentFront !== nextFront) {
            // Add visual indicator when moving between fronts
            nextFront.classList.add('focus-highlight');
            setTimeout(() => nextFront.classList.remove('focus-highlight'), 1000);
        }
    }

    setupAriaAttributes() {
        // Main form
        const form = document.getElementById('generatorForm');
        form?.setAttribute('role', 'form');
        form?.setAttribute('aria-label', 'Patient Generator Configuration');

        // Input fields
        this.addAriaToInput('totalPatients', 'Total number of patients to generate', 'number');
        this.addAriaToInput('diseasePercent', 'Percentage of disease cases', 'number', 0, 100);
        this.addAriaToInput('nonBattlePercent', 'Percentage of non-battle injuries', 'number', 0, 100);
        this.addAriaToInput('battleTraumaPercent', 'Percentage of battle trauma cases', 'number', 0, 100);
        this.addAriaToInput('baseDate', 'Base date for the exercise', 'date');
        this.addAriaToInput('encryptionPassword', 'Optional encryption password', 'password');

        // Checkboxes
        this.addAriaToCheckbox('formatJson', 'Generate JSON format output');
        this.addAriaToCheckbox('formatXml', 'Generate XML format output');
        this.addAriaToCheckbox('useCompression', 'Enable gzip compression for output files');
        this.addAriaToCheckbox('useEncryption', 'Enable AES-256-GCM encryption for output files');

        // Buttons
        this.addAriaToButton('generateBtn', 'Start patient generation');
        this.addAriaToButton('addFrontBtn', 'Add a new front configuration');
        this.addAriaToButton('saveConfigBtn', 'Save current configuration');
        this.addAriaToButton('loadConfigBtn', 'Load saved configuration');
        this.addAriaToButton('templatesBtn', 'Load configuration template');

        // Navigation
        const navbar = document.querySelector('.navbar');
        navbar?.setAttribute('role', 'navigation');
        navbar?.setAttribute('aria-label', 'Main navigation');

        // Jobs container
        const jobContainer = document.getElementById('jobContainer');
        jobContainer?.setAttribute('role', 'region');
        jobContainer?.setAttribute('aria-label', 'Job status and results');
        jobContainer?.setAttribute('aria-live', 'polite');
    }

    addAriaToInput(id, label, type, min, max) {
        const input = document.getElementById(id);
        if (input) {
            input.setAttribute('aria-label', label);
            input.setAttribute('aria-describedby', `${id}-help`);
            if (min !== undefined) input.setAttribute('aria-valuemin', min);
            if (max !== undefined) input.setAttribute('aria-valuemax', max);
            
            // Add help text if error container exists
            const errorElement = document.querySelector(`#${id}Error`);
            if (errorElement) {
                errorElement.setAttribute('id', `${id}-help`);
                errorElement.setAttribute('role', 'alert');
            }
        }
    }

    addAriaToCheckbox(id, label) {
        const checkbox = document.getElementById(id);
        if (checkbox) {
            checkbox.setAttribute('aria-label', label);
            const labelElement = checkbox.nextElementSibling;
            if (labelElement && labelElement.tagName === 'LABEL') {
                labelElement.setAttribute('id', `${id}-label`);
                checkbox.setAttribute('aria-labelledby', `${id}-label`);
            }
        }
    }

    addAriaToButton(id, label) {
        const button = document.getElementById(id);
        if (button) {
            button.setAttribute('aria-label', label);
            if (button.querySelector('i')) {
                button.querySelector('i').setAttribute('aria-hidden', 'true');
            }
        }
    }

    createAriaLiveRegion() {
        // Create a visually hidden live region for screen reader announcements
        this.ariaLiveRegion = document.createElement('div');
        this.ariaLiveRegion.setAttribute('role', 'status');
        this.ariaLiveRegion.setAttribute('aria-live', 'polite');
        this.ariaLiveRegion.setAttribute('aria-atomic', 'true');
        this.ariaLiveRegion.className = 'visually-hidden';
        document.body.appendChild(this.ariaLiveRegion);

        // Style for visually hidden content
        const style = document.createElement('style');
        style.textContent = `
            .visually-hidden {
                position: absolute !important;
                width: 1px !important;
                height: 1px !important;
                padding: 0 !important;
                margin: -1px !important;
                overflow: hidden !important;
                clip: rect(0, 0, 0, 0) !important;
                white-space: nowrap !important;
                border: 0 !important;
            }
            
            .focus-highlight {
                outline: 3px solid #0d6efd !important;
                outline-offset: 2px !important;
                transition: outline 0.3s ease-in-out;
            }
            
            @media (max-width: 768px) {
                .card {
                    margin-bottom: 10px;
                }
                
                .front-block {
                    padding: 10px;
                }
                
                .btn-group-sm .btn {
                    padding: 0.25rem 0.5rem;
                    font-size: 0.875rem;
                }
                
                .stat-card .number {
                    font-size: 1.5rem;
                }
                
                .modal-dialog {
                    margin: 0.5rem;
                }
            }
            
            @media (max-width: 576px) {
                .navbar-brand {
                    font-size: 1rem;
                }
                
                .card-header h4 {
                    font-size: 1.2rem;
                }
                
                .row.mb-3 > [class*="col-"] {
                    margin-bottom: 10px;
                }
                
                .btn-group {
                    flex-wrap: wrap;
                }
            }
            
            /* High contrast mode support */
            @media (prefers-contrast: high) {
                .front-block {
                    border-width: 2px;
                }
                
                .btn {
                    border-width: 2px;
                }
                
                .form-control:focus {
                    border-color: #000;
                    box-shadow: 0 0 0 0.25rem rgba(0, 0, 0, 0.25);
                }
            }
            
            /* Reduced motion support */
            @media (prefers-reduced-motion: reduce) {
                * {
                    animation-duration: 0.01ms !important;
                    animation-iteration-count: 1 !important;
                    transition-duration: 0.01ms !important;
                }
            }
        `;
        document.head.appendChild(style);
    }

    announce(message) {
        if (this.ariaLiveRegion) {
            this.ariaLiveRegion.textContent = message;
            // Clear after announcement
            setTimeout(() => {
                this.ariaLiveRegion.textContent = '';
            }, 1000);
        }
    }

    setupTooltips() {
        // Define tooltips for complex fields
        const tooltipData = [
            { selector: '#totalPatients', content: 'Enter the total number of patients to generate (1-10,000)' },
            { selector: '#diseasePercent', content: 'Percentage of patients with disease conditions' },
            { selector: '#nonBattlePercent', content: 'Percentage of patients with non-battle injuries' },
            { selector: '#battleTraumaPercent', content: 'Percentage of patients with battle trauma injuries' },
            { selector: '#useCompression', content: 'Enable to reduce file size using gzip compression' },
            { selector: '#useEncryption', content: 'Enable to encrypt patient data for security' },
            { selector: '#baseDate', content: 'Starting date for the military exercise simulation' },
            { selector: '.front-name', content: 'Name of the military front or operation area' },
            { selector: '.casualty-rate', content: 'Casualty rate as percentage of total patients for this front' }
        ];

        tooltipData.forEach(({ selector, content }) => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(element => {
                element.setAttribute('data-bs-toggle', 'tooltip');
                element.setAttribute('data-bs-placement', 'top');
                element.setAttribute('title', content);
                
                // Initialize Bootstrap tooltip
                new bootstrap.Tooltip(element);
            });
        });
    }

    makeResponsive() {
        // Add viewport meta if not present
        if (!document.querySelector('meta[name="viewport"]')) {
            const viewport = document.createElement('meta');
            viewport.name = 'viewport';
            viewport.content = 'width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes';
            document.head.appendChild(viewport);
        }

        // Handle orientation changes
        window.addEventListener('orientationchange', () => {
            this.announce('Screen orientation changed');
        });

        // Handle responsive navigation
        const navToggler = document.querySelector('.navbar-toggler');
        if (navToggler) {
            navToggler.addEventListener('click', () => {
                const expanded = navToggler.getAttribute('aria-expanded') === 'true';
                this.announce(expanded ? 'Navigation menu closed' : 'Navigation menu opened');
            });
        }
    }

    bindEvents() {
        // Announce form validation errors
        this.eventBus.on('validation-error', (data) => {
            this.announce(`Validation error: ${data.message}`);
        });

        // Announce successful operations
        this.eventBus.on('config-saved', () => {
            this.announce('Configuration saved successfully');
        });

        this.eventBus.on('config-loaded', () => {
            this.announce('Configuration loaded successfully');
        });

        this.eventBus.on('generation-started', () => {
            this.announce('Patient generation started');
        });

        this.eventBus.on('generation-completed', () => {
            this.announce('Patient generation completed');
        });

        // Update ARIA attributes for dynamic content
        this.eventBus.on('front-added', (data) => {
            setTimeout(() => {
                this.updateFrontAriaAttributes(data.index);
            }, 100);
        });

        this.eventBus.on('front-removed', () => {
            this.announce('Front configuration removed');
        });

        this.eventBus.on('nationality-added', () => {
            this.announce('Nationality added');
        });

        this.eventBus.on('nationality-removed', () => {
            this.announce('Nationality removed');
        });
    }

    updateFrontAriaAttributes(frontIndex) {
        const frontBlock = document.querySelector(`[data-front-index="${frontIndex}"]`);
        if (!frontBlock) return;

        // Set ARIA attributes for the front block
        frontBlock.setAttribute('role', 'group');
        frontBlock.setAttribute('aria-label', `Front configuration ${frontIndex + 1}`);

        // Update front name input
        const frontNameInput = frontBlock.querySelector('.front-name');
        if (frontNameInput) {
            frontNameInput.setAttribute('aria-label', `Front name for configuration ${frontIndex + 1}`);
            this.addTooltip(frontNameInput, 'Name of the military front or operation area');
        }

        // Update casualty rate input
        const casualtyRateInput = frontBlock.querySelector('.casualty-rate');
        if (casualtyRateInput) {
            casualtyRateInput.setAttribute('aria-label', `Casualty rate for front ${frontIndex + 1}`);
            casualtyRateInput.setAttribute('aria-valuemin', '0');
            casualtyRateInput.setAttribute('aria-valuemax', '100');
            this.addTooltip(casualtyRateInput, 'Casualty rate as percentage of total patients for this front');
        }

        // Update nationality blocks
        const nationalityBlocks = frontBlock.querySelectorAll('.nationality-block');
        nationalityBlocks.forEach((block, index) => {
            block.setAttribute('role', 'group');
            block.setAttribute('aria-label', `Nationality ${index + 1} for front ${frontIndex + 1}`);

            const select = block.querySelector('select');
            if (select) {
                select.setAttribute('aria-label', `Select nationality ${index + 1} for front ${frontIndex + 1}`);
            }

            const percentInput = block.querySelector('input[type="number"]');
            if (percentInput) {
                percentInput.setAttribute('aria-label', `Percentage for nationality ${index + 1} in front ${frontIndex + 1}`);
                percentInput.setAttribute('aria-valuemin', '0');
                percentInput.setAttribute('aria-valuemax', '100');
            }
        });

        // Update buttons
        const removeFrontBtn = frontBlock.querySelector('.remove-front-btn');
        if (removeFrontBtn) {
            removeFrontBtn.setAttribute('aria-label', `Remove front configuration ${frontIndex + 1}`);
        }

        const addNationalityBtn = frontBlock.querySelector('.add-nationality-btn');
        if (addNationalityBtn) {
            addNationalityBtn.setAttribute('aria-label', `Add nationality to front ${frontIndex + 1}`);
        }

        this.announce(`Front configuration ${frontIndex + 1} added`);
    }

    addTooltip(element, content) {
        if (element && !element.hasAttribute('data-bs-toggle')) {
            element.setAttribute('data-bs-toggle', 'tooltip');
            element.setAttribute('data-bs-placement', 'top');
            element.setAttribute('title', content);
            new bootstrap.Tooltip(element);
        }
    }

    destroy() {
        // Clean up tooltips
        const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltips.forEach(element => {
            const tooltip = bootstrap.Tooltip.getInstance(element);
            if (tooltip) {
                tooltip.dispose();
            }
        });

        // Remove ARIA live region
        if (this.ariaLiveRegion) {
            this.ariaLiveRegion.remove();
        }
    }
}