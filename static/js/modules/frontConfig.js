/**
 * Front Configuration Module - Manages dynamic front configuration
 */
import { validationManager } from './validation.js';
import { eventBus } from './events.js';

export class FrontConfigManager {
    constructor() {
        this.availableNationalities = [];
        this.defaultFrontNames = ["Polish Front", "Estonian Front", "Finnish Front"];
        this.frontCounter = 0;
        this.frontsContainer = null;
        this.initialized = false;
    }

    /**
     * Initialize the front configuration manager
     */
    async initialize(nationalities) {
        this.availableNationalities = nationalities;
        this.frontsContainer = document.getElementById('frontsContainer');
        this.initialized = true;
        
        // Add first front if container is empty
        if (this.frontsContainer && this.frontsContainer.children.length === 0) {
            this.addNewFront();
        }
    }

    /**
     * Add a new front configuration
     */
    addNewFront() {
        if (!this.initialized) {
            console.error('FrontConfigManager not initialized');
            return;
        }

        this.frontCounter++;
        const frontId = `front-${this.frontCounter}`;
        const frontBlock = this.createFrontBlock(frontId);
        
        this.frontsContainer.appendChild(frontBlock);
        
        // Set data attribute for accessibility
        const frontIndex = this.frontsContainer.children.length - 1;
        frontBlock.setAttribute('data-front-index', frontIndex);
        
        // Emit event
        eventBus.emit('front:added', { frontId, frontBlock });
        eventBus.emit('front-added', { index: frontIndex });
        
        // Add initial nationality
        const nationalitiesContainer = frontBlock.querySelector('.nationalities-container');
        const initialNatId = `nat-${frontId}-${Date.now()}-initial`;
        const initialNatBlock = this.createNationalityDistributionElement(frontId, initialNatId, true);
        initialNatBlock.setAttribute('data-nationality-index', 0);
        nationalitiesContainer.appendChild(initialNatBlock);
        
        // Setup event handlers
        this.setupFrontEventHandlers(frontBlock, frontId);
        
        return frontBlock;
    }

    /**
     * Create front block HTML element
     */
    createFrontBlock(frontId) {
        const frontBlock = document.createElement('div');
        frontBlock.className = 'front-block';
        frontBlock.id = frontId;

        const frontNumber = this.frontsContainer.children.length + 1;
        const defaultName = this.frontsContainer.children.length < this.defaultFrontNames.length ? 
                            this.defaultFrontNames[this.frontsContainer.children.length] : 
                            `Front ${frontNumber}`;

        // Hide remove button for the first front
        const isFirstFront = this.frontsContainer.children.length === 0;
        const removeButtonHtml = isFirstFront ? '' : 
            '<button type="button" class="btn btn-danger btn-sm remove-front-btn"><i class="fas fa-trash"></i> Remove Front</button>';

        frontBlock.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-2">
                <h6 class="mb-0">Front ${frontNumber}</h6>
                ${removeButtonHtml}
            </div>
            <div class="mb-2">
                <label for="${frontId}-name" class="form-label form-label-sm">Front Name</label>
                <input type="text" class="form-control form-control-sm front-name" id="${frontId}-name" value="${defaultName}">
            </div>
            <div class="mb-2">
                <label for="${frontId}-casualtyRate" class="form-label form-label-sm">Casualty Rate (%)</label>
                <input type="number" class="form-control form-control-sm front-casualty-rate" id="${frontId}-casualtyRate" placeholder="e.g. 30 for 30%" min="0" max="100" step="0.1">
            </div>
            <h6>Nationality Distribution for this Front</h6>
            <div class="nationalities-container mb-2">
            </div>
            <button type="button" class="btn btn-outline-primary btn-sm add-nationality-btn mb-2"><i class="fas fa-plus me-1"></i>Add Nationality to Front</button>
            <div class="form-text text-danger hidden" id="${frontId}-natPercentError">Nationality percentages for this front must sum to 100%.</div>
        `;
        
        return frontBlock;
    }

    /**
     * Create nationality distribution element
     */
    createNationalityDistributionElement(frontId, natId, isFirstNationality = false) {
        const natBlock = document.createElement('div');
        natBlock.className = 'nationality-block mb-2';
        natBlock.dataset.id = natId;

        const selectNat = document.createElement('select');
        selectNat.className = 'form-select form-select-sm me-2 nationality-code';
        selectNat.dataset.frontId = frontId;
        selectNat.dataset.natId = natId;
        
        // Get already selected nationalities in this front
        const parentFrontBlock = document.getElementById(frontId);
        const selectedCodesInThisFront = new Set();
        if (parentFrontBlock) {
            parentFrontBlock.querySelectorAll('.nationality-code').forEach(existingSelect => {
                if (existingSelect.value && existingSelect.dataset.natId !== natId) {
                    selectedCodesInThisFront.add(existingSelect.value);
                }
            });
        }
        
        // Add empty option
        const emptyOption = document.createElement('option');
        emptyOption.value = "";
        emptyOption.textContent = "Select nationality...";
        selectNat.appendChild(emptyOption);
        
        // Add nationality options
        this.availableNationalities.forEach(nat => {
            const option = document.createElement('option');
            option.value = nat.code;
            option.textContent = `${nat.name} (${nat.code})`;
            if (selectedCodesInThisFront.has(nat.code)) {
                option.disabled = true;
            }
            selectNat.appendChild(option);
        });
        
        selectNat.onchange = () => {
            this.handleNationalitySelectionChange(frontId);
            validationManager.debouncedValidateFrontNationality(document.getElementById(frontId));
        };

        const inputPercent = document.createElement('input');
        inputPercent.type = 'number';
        inputPercent.className = 'form-control form-control-sm me-2 nationality-percentage';
        inputPercent.placeholder = '%';
        inputPercent.min = "0";
        inputPercent.max = "100";
        inputPercent.step = "0.1";
        inputPercent.style.width = '80px';
        inputPercent.oninput = () => validationManager.debouncedValidateFrontNationality(document.getElementById(frontId));

        natBlock.appendChild(selectNat);
        natBlock.appendChild(inputPercent);
        
        // Only add remove button if it's not the first nationality
        if (!isFirstNationality) {
            const removeNatBtn = document.createElement('button');
            removeNatBtn.type = 'button';
            removeNatBtn.className = 'btn btn-danger btn-sm remove-nationality-btn';
            removeNatBtn.innerHTML = '<i class="fas fa-minus"></i>';
            removeNatBtn.onclick = () => this.removeNationality(natBlock, frontId);
            natBlock.appendChild(removeNatBtn);
        }
        
        return natBlock;
    }

    /**
     * Setup event handlers for a front block
     */
    setupFrontEventHandlers(frontBlock, frontId) {
        // Remove front button (if it exists)
        const removeFrontBtn = frontBlock.querySelector('.remove-front-btn');
        if (removeFrontBtn) {
            removeFrontBtn.onclick = () => {
                if (this.frontsContainer.children.length > 1) {
                    frontBlock.remove();
                    validationManager.validateOverallFrontCasualtyRates();
                    eventBus.emit('front:removed', { frontId });
                    eventBus.emit('front-removed');
                } else {
                    alert("At least one front must be configured.");
                }
            };
        }

        // Add nationality button
        const addNationalityBtn = frontBlock.querySelector('.add-nationality-btn');
        const nationalitiesContainer = frontBlock.querySelector('.nationalities-container');
        
        addNationalityBtn.onclick = () => {
            const natId = `nat-${frontId}-${Date.now()}`;
            const natBlock = this.createNationalityDistributionElement(frontId, natId);
            const nationalityIndex = nationalitiesContainer.querySelectorAll('.nationality-block').length;
            natBlock.setAttribute('data-nationality-index', nationalityIndex);
            nationalitiesContainer.appendChild(natBlock);
            
            const frontIndex = Array.from(this.frontsContainer.children).indexOf(frontBlock);
            eventBus.emit('nationality-added', { frontIndex, nationalityIndex });
        };

        // Casualty rate input
        const casualtyRateInput = frontBlock.querySelector('.front-casualty-rate');
        if (casualtyRateInput) {
            casualtyRateInput.addEventListener('input', () => {
                validationManager.debouncedValidateFrontCasualty();
            });
        }
    }

    /**
     * Handle nationality selection change
     */
    handleNationalitySelectionChange(frontId) {
        const frontBlockElement = document.getElementById(frontId);
        if (!frontBlockElement) return;

        const selectedCodesInThisFront = new Set();
        frontBlockElement.querySelectorAll('.nationality-code').forEach(selectElement => {
            if (selectElement.value) {
                selectedCodesInThisFront.add(selectElement.value);
            }
        });

        // Update all selects in this front to disable/enable options
        frontBlockElement.querySelectorAll('.nationality-code').forEach(selectElement => {
            const currentSelectedValue = selectElement.value;
            for (let i = 0; i < selectElement.options.length; i++) {
                const option = selectElement.options[i];
                if (option.value === "") continue;

                if (selectedCodesInThisFront.has(option.value) && option.value !== currentSelectedValue) {
                    option.disabled = true;
                } else {
                    option.disabled = false;
                }
            }
        });
    }

    /**
     * Remove nationality from front
     */
    removeNationality(natBlock, frontId) {
        const parentFrontBlock = natBlock.closest('.front-block');
        if (parentFrontBlock.querySelectorAll('.nationality-block').length > 1) {
            natBlock.remove();
            this.handleNationalitySelectionChange(frontId);
            validationManager.validateFrontNationalityPercentages(parentFrontBlock);
            eventBus.emit('nationality-removed');
        } else {
            alert("At least one nationality must be present in a front's distribution.");
        }
    }

    /**
     * Get front configurations for submission
     */
    getFrontConfigurations() {
        const adHocFrontConfigs = [];
        
        document.querySelectorAll('#frontsContainer .front-block').forEach(frontBlock => {
            const frontName = frontBlock.querySelector('.front-name').value || 'Unnamed Front';
            const casualtyRate = parseFloat(frontBlock.querySelector('.front-casualty-rate').value) / 100.0 || 0;
            
            const nationality_distribution = [];
            frontBlock.querySelectorAll('.nationality-block').forEach(natBlock => {
                const code = natBlock.querySelector('.nationality-code').value;
                const percent = parseFloat(natBlock.querySelector('.nationality-percentage').value) || 0;
                if (code && percent > 0) {
                    nationality_distribution.push({ nationality_code: code, percentage: percent });
                }
            });

            if (casualtyRate > 0 && nationality_distribution.length > 0) {
                adHocFrontConfigs.push({
                    id: frontName.replace(/\s+/g, '_').toLowerCase() + `_${Date.now()}`,
                    name: frontName,
                    nationality_distribution: nationality_distribution,
                    casualty_rate: casualtyRate
                });
            }
        });
        
        return adHocFrontConfigs;
    }

    /**
     * Load front configurations into the form
     */
    loadFrontConfigurations(frontConfigs) {
        // Clear existing fronts
        this.frontsContainer.innerHTML = '';
        this.frontCounter = 0;

        // Add each front configuration
        frontConfigs.forEach((frontConfig, index) => {
            const frontBlock = this.addNewFront();
            
            // Set front name
            const frontNameInput = frontBlock.querySelector('.front-name');
            if (frontNameInput) {
                frontNameInput.value = frontConfig.name || `Front ${index + 1}`;
            }

            // Set casualty rate
            const casualtyRateInput = frontBlock.querySelector('.front-casualty-rate');
            if (casualtyRateInput) {
                casualtyRateInput.value = (frontConfig.casualty_rate * 100).toFixed(1);
            }

            // Clear default nationality and add configured ones
            const nationalitiesContainer = frontBlock.querySelector('.nationalities-container');
            nationalitiesContainer.innerHTML = '';

            // Add nationalities
            frontConfig.nationality_distribution.forEach((natDist, natIndex) => {
                const natId = `nat-${frontBlock.id}-${Date.now()}-${natIndex}`;
                const natBlock = this.createNationalityDistributionElement(
                    frontBlock.id, 
                    natId, 
                    natIndex === 0 // First nationality
                );

                // Set nationality code
                const codeSelect = natBlock.querySelector('.nationality-code');
                if (codeSelect) {
                    codeSelect.value = natDist.nationality_code;
                }

                // Set percentage
                const percentInput = natBlock.querySelector('.nationality-percentage');
                if (percentInput) {
                    percentInput.value = natDist.percentage;
                }

                nationalitiesContainer.appendChild(natBlock);
            });

            // Update nationality selections
            this.handleNationalitySelectionChange(frontBlock.id);

            // Validate the loaded front
            validationManager.validateFrontNationalityPercentages(frontBlock);
        });

        // Validate overall casualty rates
        validationManager.validateOverallFrontCasualtyRates();
    }
}

// Export singleton instance
export const frontConfigManager = new FrontConfigManager();