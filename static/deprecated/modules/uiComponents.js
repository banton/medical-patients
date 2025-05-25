// UI Components Module

export class UIComponents {
    constructor() {
        this.nationalityOptions = [];
        this.frontCounter = 0;
        this.fronts = new Map();
    }

    setNationalityOptions(nationalities) {
        this.nationalityOptions = nationalities.sort();
    }

    renderBasicSettings(containerId) {
        const container = document.getElementById(containerId);
        container.innerHTML = `
            <h6><i class="bi bi-gear-fill"></i>Basic Configuration</h6>
            <div class="row">
                <div class="col-md-6">
                    <div class="mb-3">
                        <label for="totalPatients" class="form-label">Total Patients</label>
                        <input type="number" class="form-control" id="totalPatients" 
                               min="1" max="10000" value="200" required>
                        <div class="form-text">Number of patients to generate (1-10,000)</div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="mb-3">
                        <label for="exerciseBaseDate" class="form-label">Exercise Base Date</label>
                        <input type="date" class="form-control" id="exerciseBaseDate" 
                               value="${new Date().toISOString().split('T')[0]}" required>
                    </div>
                </div>
            </div>
            <div class="mb-3">
                <label for="exerciseName" class="form-label">Exercise Name (Optional)</label>
                <input type="text" class="form-control" id="exerciseName" 
                       placeholder="e.g., NATO Exercise 2025">
            </div>
            <div class="mb-3">
                <label for="description" class="form-label">Description (Optional)</label>
                <textarea class="form-control" id="description" rows="2" 
                          placeholder="Additional notes about this generation..."></textarea>
            </div>
        `;
        
        // Add event listeners
        this.addConfigChangeListeners(container);
    }

    renderMedicalFacilityDefaults(containerId) {
        const container = document.getElementById(containerId);
        container.innerHTML = `
            <h6><i class="bi bi-hospital"></i>Default Medical Facility Settings</h6>
            <p class="text-muted mb-3">These defaults will be applied to all fronts. Individual fronts can override these values.</p>
            
            <div class="row mb-3">
                <div class="col-md-6">
                    <h6 class="text-secondary">Default Capacities</h6>
                    ${this.renderFacilityCapacities('default')}
                </div>
                <div class="col-md-6">
                    <h6 class="text-secondary">Default KIA Rates (%)</h6>
                    ${this.renderFacilityRates('default', 'kia')}
                </div>
            </div>
            <div class="row">
                <div class="col-md-6">
                    <h6 class="text-secondary">Default RTD Rates (%)</h6>
                    ${this.renderFacilityRates('default', 'rtd')}
                </div>
                <div class="col-md-6 d-flex align-items-end">
                    <button class="btn btn-sm btn-secondary" onclick="this.resetFacilityDefaults()">
                        <i class="bi bi-arrow-clockwise me-1"></i>Reset to System Defaults
                    </button>
                </div>
            </div>
        `;
        
        // Make resetFacilityDefaults available globally for onclick
        window.resetFacilityDefaults = () => this.resetFacilityDefaults();
        
        this.addConfigChangeListeners(container);
    }

    renderFacilityCapacities(prefix) {
        const facilities = [
            { id: 'point_of_injury', name: 'Point of Injury', default: 0 },
            { id: 'role_1', name: 'Role 1', default: 10 },
            { id: 'role_2', name: 'Role 2', default: 50 },
            { id: 'role_3', name: 'Role 3', default: 200 },
            { id: 'role_4', name: 'Role 4', default: 500 }
        ];

        return facilities.map(facility => `
            <div class="mb-2">
                <label for="${prefix}_${facility.id}_capacity" class="form-label small">${facility.name}</label>
                <div class="input-group input-group-sm">
                    <input type="number" class="form-control" id="${prefix}_${facility.id}_capacity" 
                           min="0" value="${facility.default}">
                    <span class="input-group-text">beds</span>
                </div>
            </div>
        `).join('');
    }

    renderFacilityRates(prefix, rateType) {
        const facilities = [
            { id: 'point_of_injury', name: 'Point of Injury', kia: 2.5, rtd: 10.0 },
            { id: 'role_1', name: 'Role 1', kia: 1.0, rtd: 15.0 },
            { id: 'role_2', name: 'Role 2', kia: 0.5, rtd: 30.0 },
            { id: 'role_3', name: 'Role 3', kia: 0.2, rtd: 25.0 },
            { id: 'role_4', name: 'Role 4', kia: 0.1, rtd: 40.0 }
        ];

        return facilities.map(facility => `
            <div class="mb-2">
                <label for="${prefix}_${facility.id}_${rateType}_rate" class="form-label small">${facility.name}</label>
                <div class="input-group input-group-sm">
                    <input type="number" class="form-control" id="${prefix}_${facility.id}_${rateType}_rate" 
                           min="0" max="100" step="0.1" value="${facility[rateType]}">
                    <span class="input-group-text">%</span>
                </div>
            </div>
        `).join('');
    }

    renderFrontConfiguration(containerId) {
        const container = document.getElementById(containerId);
        container.innerHTML = `
            <h6><i class="bi bi-bullseye"></i>Front Configuration</h6>
            <div id="frontsList"></div>
            <button class="btn btn-primary btn-sm mt-2" id="addFrontBtn">
                <i class="bi bi-plus-circle me-1"></i>Add Front
            </button>
        `;
        
        // Add initial front
        this.addFront(0);
        
        // Event listener for add button
        document.getElementById('addFrontBtn').addEventListener('click', () => {
            document.dispatchEvent(new CustomEvent('front-added'));
        });
    }

    addFront(index) {
        this.frontCounter++;
        const frontId = `front-${this.frontCounter}`;
        const frontsList = document.getElementById('frontsList');
        
        const frontCard = document.createElement('div');
        frontCard.className = 'front-card';
        frontCard.id = frontId;
        frontCard.innerHTML = this.createFrontHTML(frontId, index);
        
        frontsList.appendChild(frontCard);
        this.fronts.set(frontId, { id: frontId, index });
        
        // Add event listeners
        this.setupFrontEventListeners(frontId);
        this.addConfigChangeListeners(frontCard);
    }

    createFrontHTML(frontId, index) {
        return `
            <div class="front-header">
                <h6 class="mb-0">
                    <span class="front-number">Front ${index + 1}</span>
                    <button class="btn btn-sm btn-link text-decoration-none collapse-indicator" 
                            type="button" data-bs-toggle="collapse" data-bs-target="#${frontId}_content">
                        <i class="bi bi-chevron-down"></i>
                    </button>
                </h6>
                <button class="btn btn-sm btn-outline-danger" onclick="window.removeFront('${frontId}')">
                    <i class="bi bi-trash"></i>
                </button>
            </div>
            <div class="collapse show" id="${frontId}_content">
                <div class="row mb-3">
                    <div class="col-md-6">
                        <label class="form-label">Front Name</label>
                        <input type="text" class="form-control" id="${frontId}_name" 
                               value="Training Area ${index + 1}" required>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">Front Type</label>
                        <select class="form-select" id="${frontId}_type">
                            <option value="Training">Training</option>
                            <option value="Combat">Combat</option>
                            <option value="Humanitarian">Humanitarian</option>
                            <option value="Exercise">Exercise</option>
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">Casualty Rate (%)</label>
                        <input type="number" class="form-control" id="${frontId}_casualty_rate" 
                               min="0" max="100" step="0.1" value="100" required>
                    </div>
                </div>
                
                <div class="mb-3">
                    <label class="form-label">Nationality Distribution</label>
                    <div id="${frontId}_nationalities" class="border rounded p-2">
                        <div class="nationality-item">
                            <select class="form-select nationality-select">
                                <option value="United States">United States</option>
                            </select>
                            <input type="number" class="form-control" min="0" max="100" value="100">
                            <span>%</span>
                            <button class="btn btn-sm btn-outline-danger btn-remove" disabled>
                                <i class="bi bi-x"></i>
                            </button>
                        </div>
                    </div>
                    <button class="btn btn-sm btn-outline-primary mt-2" 
                            onclick="window.addNationality('${frontId}')">
                        <i class="bi bi-plus"></i> Add Nationality
                    </button>
                </div>
                
                <div class="mb-3">
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" id="${frontId}_use_custom_facilities">
                        <label class="form-check-label" for="${frontId}_use_custom_facilities">
                            Use custom medical facilities for this front
                        </label>
                    </div>
                </div>
                
                <div class="collapse" id="${frontId}_custom_facilities">
                    ${this.renderCustomFacilities(frontId)}
                </div>
            </div>
        `;
    }

    renderCustomFacilities(frontId) {
        return `
            <div class="facility-card">
                <h6><i class="bi bi-hospital"></i> Medical Care Chain</h6>
                <div class="facility-grid">
                    ${this.renderFacilityCard(frontId, 'point_of_injury', 'Point of Injury')}
                    ${this.renderFacilityCard(frontId, 'role_1', 'Role 1 (Battalion Aid)')}
                    ${this.renderFacilityCard(frontId, 'role_2', 'Role 2 (Forward Hospital)')}
                    ${this.renderFacilityCard(frontId, 'role_3', 'Role 3 (Combat Hospital)')}
                    ${this.renderFacilityCard(frontId, 'role_4', 'Role 4 (CONUS Hospital)')}
                </div>
            </div>
        `;
    }

    renderFacilityCard(frontId, facilityType, facilityName) {
        return `
            <div class="facility-card">
                <h6>${facilityName}</h6>
                <div class="mb-2">
                    <label class="form-label small">Capacity</label>
                    <div class="input-group input-group-sm">
                        <input type="number" class="form-control" 
                               id="${frontId}_${facilityType}_capacity" min="0" value="0">
                        <span class="input-group-text">beds</span>
                    </div>
                </div>
                <div class="mb-2">
                    <label class="form-label small">KIA Rate</label>
                    <div class="input-group input-group-sm">
                        <input type="number" class="form-control" 
                               id="${frontId}_${facilityType}_kia_rate" 
                               min="0" max="100" step="0.1" value="0">
                        <span class="input-group-text">%</span>
                    </div>
                </div>
                <div class="mb-2">
                    <label class="form-label small">RTD Rate</label>
                    <div class="input-group input-group-sm">
                        <input type="number" class="form-control" 
                               id="${frontId}_${facilityType}_rtd_rate" 
                               min="0" max="100" step="0.1" value="0">
                        <span class="input-group-text">%</span>
                    </div>
                </div>
            </div>
        `;
    }

    setupFrontEventListeners(frontId) {
        // Custom facilities toggle
        const customCheckbox = document.getElementById(`${frontId}_use_custom_facilities`);
        const customFacilities = document.getElementById(`${frontId}_custom_facilities`);
        
        customCheckbox.addEventListener('change', (e) => {
            if (e.target.checked) {
                customFacilities.classList.add('show');
            } else {
                customFacilities.classList.remove('show');
            }
        });
        
        // Make functions available globally
        window.removeFront = (id) => this.removeFront(id);
        window.addNationality = (id) => this.addNationality(id);
    }

    removeFront(frontId) {
        if (this.fronts.size <= 1) {
            alert('At least one front is required');
            return;
        }
        
        const frontElement = document.getElementById(frontId);
        frontElement.remove();
        this.fronts.delete(frontId);
        
        // Renumber remaining fronts
        this.renumberFronts();
        
        document.dispatchEvent(new CustomEvent('front-removed', { detail: { frontId } }));
    }

    renumberFronts() {
        let index = 0;
        this.fronts.forEach((front, frontId) => {
            const numberElement = document.querySelector(`#${frontId} .front-number`);
            if (numberElement) {
                numberElement.textContent = `Front ${index + 1}`;
            }
            index++;
        });
    }

    addNationality(frontId) {
        const container = document.getElementById(`${frontId}_nationalities`);
        const nationalityItem = document.createElement('div');
        nationalityItem.className = 'nationality-item';
        
        const options = this.nationalityOptions.map(nat => 
            `<option value="${nat}">${nat}</option>`
        ).join('');
        
        nationalityItem.innerHTML = `
            <select class="form-select nationality-select">${options}</select>
            <input type="number" class="form-control" min="0" max="100" value="0">
            <span>%</span>
            <button class="btn btn-sm btn-outline-danger btn-remove" 
                    onclick="this.parentElement.remove(); window.dispatchEvent(new Event('config-changed'));">
                <i class="bi bi-x"></i>
            </button>
        `;
        
        container.appendChild(nationalityItem);
        document.dispatchEvent(new Event('config-changed'));
    }

    renderInjuryDistribution(containerId) {
        const container = document.getElementById(containerId);
        container.innerHTML = `
            <h6><i class="bi bi-activity"></i>Injury Distribution</h6>
            <div class="injury-distribution-container">
                <div class="injury-slider">
                    <label>Disease</label>
                    <input type="range" class="form-range" id="injury_disease" 
                           min="0" max="100" value="50">
                    <span class="percentage-display">50%</span>
                </div>
                <div class="injury-slider">
                    <label>Non-Battle Injury</label>
                    <input type="range" class="form-range" id="injury_nonbattle" 
                           min="0" max="100" value="40">
                    <span class="percentage-display">40%</span>
                </div>
                <div class="injury-slider">
                    <label>Battle Trauma</label>
                    <input type="range" class="form-range" id="injury_battle" 
                           min="0" max="100" value="10">
                    <span class="percentage-display">10%</span>
                </div>
            </div>
            <div class="mt-3">
                <div class="d-flex justify-content-between align-items-center">
                    <span>Total: <strong id="injuryTotal">100%</strong></span>
                    <div>
                        <button class="btn btn-sm btn-outline-secondary" onclick="window.autoBalanceInjuries()">
                            <i class="bi bi-sliders me-1"></i>Auto-Balance
                        </button>
                        <button class="btn btn-sm btn-outline-secondary" onclick="window.resetInjuries()">
                            <i class="bi bi-arrow-clockwise me-1"></i>Reset
                        </button>
                    </div>
                </div>
            </div>
            <div id="injuryValidation" class="validation-feedback mt-2"></div>
        `;
        
        // Set up event listeners
        this.setupInjuryDistributionListeners();
        
        // Make functions available globally
        window.autoBalanceInjuries = () => this.autoBalanceInjuries();
        window.resetInjuries = () => this.resetInjuries();
    }

    setupInjuryDistributionListeners() {
        const sliders = ['disease', 'nonbattle', 'battle'];
        
        sliders.forEach(type => {
            const slider = document.getElementById(`injury_${type}`);
            const display = slider.nextElementSibling;
            
            slider.addEventListener('input', (e) => {
                display.textContent = e.target.value + '%';
                this.updateInjuryTotal();
                document.dispatchEvent(new Event('config-changed'));
            });
        });
    }

    updateInjuryTotal() {
        const disease = parseInt(document.getElementById('injury_disease').value);
        const nonbattle = parseInt(document.getElementById('injury_nonbattle').value);
        const battle = parseInt(document.getElementById('injury_battle').value);
        
        const total = disease + nonbattle + battle;
        const totalElement = document.getElementById('injuryTotal');
        const validationElement = document.getElementById('injuryValidation');
        
        totalElement.textContent = total + '%';
        
        if (total === 100) {
            totalElement.className = 'text-success';
            validationElement.textContent = '✓ Distribution is valid';
            validationElement.className = 'validation-feedback text-success';
        } else {
            totalElement.className = 'text-danger';
            validationElement.textContent = `✗ Distribution must equal 100% (currently ${total}%)`;
            validationElement.className = 'validation-feedback text-danger';
        }
    }

    autoBalanceInjuries() {
        // Try to maintain relative proportions while summing to 100
        const disease = parseInt(document.getElementById('injury_disease').value);
        const nonbattle = parseInt(document.getElementById('injury_nonbattle').value);
        const battle = parseInt(document.getElementById('injury_battle').value);
        
        const total = disease + nonbattle + battle;
        if (total === 0) {
            // Reset to defaults
            this.resetInjuries();
            return;
        }
        
        // Calculate proportional values
        const diseaseNew = Math.round((disease / total) * 100);
        const nonbattleNew = Math.round((nonbattle / total) * 100);
        const battleNew = 100 - diseaseNew - nonbattleNew;
        
        // Update sliders
        document.getElementById('injury_disease').value = diseaseNew;
        document.getElementById('injury_nonbattle').value = nonbattleNew;
        document.getElementById('injury_battle').value = battleNew;
        
        // Update displays
        document.querySelector('#injury_disease + .percentage-display').textContent = diseaseNew + '%';
        document.querySelector('#injury_nonbattle + .percentage-display').textContent = nonbattleNew + '%';
        document.querySelector('#injury_battle + .percentage-display').textContent = battleNew + '%';
        
        this.updateInjuryTotal();
        document.dispatchEvent(new Event('config-changed'));
    }

    resetInjuries() {
        const defaults = { disease: 50, nonbattle: 40, battle: 10 };
        
        Object.entries(defaults).forEach(([type, value]) => {
            document.getElementById(`injury_${type}`).value = value;
            document.querySelector(`#injury_${type} + .percentage-display`).textContent = value + '%';
        });
        
        this.updateInjuryTotal();
        document.dispatchEvent(new Event('config-changed'));
    }

    renderOutputConfiguration(containerId) {
        const container = document.getElementById(containerId);
        container.innerHTML = `
            <h6><i class="bi bi-download"></i>Output Formats</h6>
            <div class="row">
                <div class="col-md-6">
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" id="format_json" checked>
                        <label class="form-check-label" for="format_json">JSON</label>
                    </div>
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" id="format_xml" checked>
                        <label class="form-check-label" for="format_xml">XML</label>
                    </div>
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" id="format_csv">
                        <label class="form-check-label" for="format_csv">CSV</label>
                    </div>
                </div>
                <div class="col-md-6">
                    <h6 class="small text-secondary">Additional Options</h6>
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" id="use_compression" checked>
                        <label class="form-check-label" for="use_compression">
                            Generate compressed (gzip) files
                        </label>
                    </div>
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" id="use_encryption" checked>
                        <label class="form-check-label" for="use_encryption">
                            Generate encrypted (AES-256-GCM) files
                        </label>
                    </div>
                </div>
            </div>
            <div class="mt-3">
                <label for="encryption_password" class="form-label">Encryption Password (Optional)</label>
                <input type="password" class="form-control" id="encryption_password" 
                       placeholder="Leave blank for random key">
                <div class="form-text">If left blank, a random encryption key will be generated and included in the download.</div>
            </div>
        `;
        
        this.addConfigChangeListeners(container);
    }

    renderTemplateSystem(containerId) {
        const container = document.getElementById(containerId);
        container.innerHTML = `
            <h6><i class="bi bi-bookmark"></i>Configuration Templates</h6>
            <div class="d-flex gap-2">
                <select class="form-select" id="templateSelect">
                    <option value="">Select a template...</option>
                </select>
                <button class="btn btn-primary" id="loadTemplateBtn">
                    <i class="bi bi-folder-open"></i> Load
                </button>
                <button class="btn btn-success" id="saveTemplateBtn">
                    <i class="bi bi-save"></i> Save as Template
                </button>
            </div>
            <div class="mt-2">
                <div class="btn-group" role="group">
                    <button class="btn btn-sm btn-outline-secondary template-quick" data-template="nato">
                        NATO Exercise
                    </button>
                    <button class="btn btn-sm btn-outline-secondary template-quick" data-template="training">
                        Training
                    </button>
                    <button class="btn btn-sm btn-outline-secondary template-quick" data-template="humanitarian">
                        Humanitarian
                    </button>
                    <button class="btn btn-sm btn-outline-secondary template-quick" data-template="large">
                        Large Scale
                    </button>
                </div>
            </div>
        `;
        
        // Event listeners
        document.getElementById('loadTemplateBtn').addEventListener('click', () => {
            const templateId = document.getElementById('templateSelect').value;
            if (templateId) {
                document.dispatchEvent(new CustomEvent('template-selected', { detail: { templateId } }));
            }
        });
        
        document.getElementById('saveTemplateBtn').addEventListener('click', () => {
            const name = prompt('Enter template name:');
            if (name) {
                document.dispatchEvent(new CustomEvent('template-save', { detail: { name } }));
            }
        });
        
        // Quick template buttons
        document.querySelectorAll('.template-quick').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const template = e.target.dataset.template;
                document.dispatchEvent(new CustomEvent('template-selected', { detail: { templateId: template } }));
            });
        });
    }

    renderJobsPanel(containerId, jobs) {
        const container = document.getElementById(containerId);
        
        if (!jobs || jobs.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted py-5">
                    <i class="bi bi-arrow-repeat fs-1"></i>
                    <p class="mt-2">No jobs yet.<br>Configure and start a generation job.</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = jobs.map(job => this.createJobCard(job)).join('');
    }

    createJobCard(job) {
        const statusClass = {
            'pending': 'warning',
            'running': 'info',
            'completed': 'success',
            'failed': 'danger',
            'cancelled': 'secondary'
        }[job.status] || 'secondary';
        
        const statusIcon = {
            'pending': 'clock',
            'running': 'arrow-repeat',
            'completed': 'check-circle',
            'failed': 'x-circle',
            'cancelled': 'slash-circle'
        }[job.status] || 'question-circle';
        
        const progress = Math.round((job.progress || 0) * 100);
        const showProgress = ['pending', 'running'].includes(job.status);
        
        return `
            <div class="job-card" id="job-${job.job_id}">
                <div class="job-header">
                    <span class="job-id">Job #${job.job_id.substring(0, 8)}</span>
                    <span class="badge bg-${statusClass} status-badge">
                        <i class="bi bi-${statusIcon}"></i> ${job.status}
                    </span>
                </div>
                
                ${showProgress ? `
                    <div class="progress job-progress">
                        <div class="progress-bar progress-bar-striped progress-bar-animated bg-${statusClass}" 
                             style="width: ${progress}%">${progress}%</div>
                    </div>
                ` : ''}
                
                <div class="job-details">
                    <div>Patients: ${job.processed_patients || 0}/${job.total_patients || 0}</div>
                    ${job.started_at ? `<div>Started: ${new Date(job.started_at).toLocaleTimeString()}</div>` : ''}
                    ${job.completed_at ? `<div>Completed: ${new Date(job.completed_at).toLocaleTimeString()}</div>` : ''}
                    ${job.estimated_completion ? `<div>ETA: ${new Date(job.estimated_completion).toLocaleTimeString()}</div>` : ''}
                </div>
                
                <div class="job-actions">
                    ${job.status === 'running' ? `
                        <button class="btn btn-sm btn-warning" onclick="window.cancelJob('${job.job_id}')">
                            <i class="bi bi-pause"></i> Cancel
                        </button>
                    ` : ''}
                    
                    ${job.status === 'completed' ? `
                        <button class="btn btn-sm btn-primary" onclick="window.downloadJob('${job.job_id}')">
                            <i class="bi bi-download"></i> Download
                        </button>
                        <button class="btn btn-sm btn-info" onclick="window.viewJob('${job.job_id}')">
                            <i class="bi bi-eye"></i> View
                        </button>
                    ` : ''}
                    
                    ${['completed', 'failed', 'cancelled'].includes(job.status) ? `
                        <button class="btn btn-sm btn-danger" onclick="window.deleteJob('${job.job_id}')">
                            <i class="bi bi-trash"></i> Delete
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
    }

    addConfigChangeListeners(container) {
        // Add change event listeners to all form controls
        container.querySelectorAll('input, select, textarea').forEach(element => {
            element.addEventListener('change', () => {
                document.dispatchEvent(new Event('config-changed'));
            });
        });
    }

    collectConfiguration() {
        const config = {
            // Basic settings
            total_patients: parseInt(document.getElementById('totalPatients').value),
            exercise_name: document.getElementById('exerciseName').value,
            exercise_base_date: document.getElementById('exerciseBaseDate').value,
            description: document.getElementById('description').value,
            
            // Medical facility defaults
            medical_facility_defaults: this.collectFacilityDefaults(),
            
            // Fronts
            fronts: this.collectFronts(),
            
            // Injury distribution
            injury_distribution: {
                'Disease': parseInt(document.getElementById('injury_disease').value),
                'Non-Battle Injury': parseInt(document.getElementById('injury_nonbattle').value),
                'Battle Trauma': parseInt(document.getElementById('injury_battle').value)
            },
            
            // Output configuration
            output_formats: this.collectOutputFormats(),
            use_compression: document.getElementById('use_compression').checked,
            use_encryption: document.getElementById('use_encryption').checked,
            encryption_password: document.getElementById('encryption_password').value
        };
        
        return config;
    }

    collectFacilityDefaults() {
        const facilities = ['point_of_injury', 'role_1', 'role_2', 'role_3', 'role_4'];
        const defaults = {};
        
        facilities.forEach(facility => {
            defaults[facility] = {
                name: this.getFacilityName(facility),
                capacity: parseInt(document.getElementById(`default_${facility}_capacity`).value),
                kia_rate: parseFloat(document.getElementById(`default_${facility}_kia_rate`).value) / 100,
                rtd_rate: parseFloat(document.getElementById(`default_${facility}_rtd_rate`).value) / 100,
                description: ''
            };
        });
        
        return defaults;
    }

    getFacilityName(facilityId) {
        const names = {
            'point_of_injury': 'Point of Injury',
            'role_1': 'Role 1 (Battalion Aid)',
            'role_2': 'Role 2 (Forward Hospital)',
            'role_3': 'Role 3 (Combat Hospital)',
            'role_4': 'Role 4 (CONUS Hospital)'
        };
        return names[facilityId] || facilityId;
    }

    collectFronts() {
        const fronts = [];
        
        this.fronts.forEach((front, frontId) => {
            const frontData = {
                id: frontId,
                name: document.getElementById(`${frontId}_name`).value,
                type: document.getElementById(`${frontId}_type`).value,
                casualty_rate: parseFloat(document.getElementById(`${frontId}_casualty_rate`).value) / 100,
                nationality_distribution: this.collectNationalities(frontId),
                medical_facilities: null
            };
            
            // Check if using custom facilities
            if (document.getElementById(`${frontId}_use_custom_facilities`).checked) {
                frontData.medical_facilities = this.collectCustomFacilities(frontId);
            }
            
            fronts.push(frontData);
        });
        
        return fronts;
    }

    collectNationalities(frontId) {
        const distribution = {};
        const container = document.getElementById(`${frontId}_nationalities`);
        
        container.querySelectorAll('.nationality-item').forEach(item => {
            const nationality = item.querySelector('select').value;
            const percentage = parseInt(item.querySelector('input').value);
            distribution[nationality] = percentage;
        });
        
        return distribution;
    }

    collectCustomFacilities(frontId) {
        const facilities = ['point_of_injury', 'role_1', 'role_2', 'role_3', 'role_4'];
        const customFacilities = {};
        
        facilities.forEach(facility => {
            customFacilities[facility] = {
                name: this.getFacilityName(facility),
                capacity: parseInt(document.getElementById(`${frontId}_${facility}_capacity`).value),
                kia_rate: parseFloat(document.getElementById(`${frontId}_${facility}_kia_rate`).value) / 100,
                rtd_rate: parseFloat(document.getElementById(`${frontId}_${facility}_rtd_rate`).value) / 100,
                description: ''
            };
        });
        
        return customFacilities;
    }

    collectOutputFormats() {
        const formats = [];
        if (document.getElementById('format_json').checked) formats.push('json');
        if (document.getElementById('format_xml').checked) formats.push('xml');
        if (document.getElementById('format_csv').checked) formats.push('csv');
        return formats;
    }

    loadConfiguration(config) {
        // Basic settings
        document.getElementById('totalPatients').value = config.total_patients || 200;
        document.getElementById('exerciseName').value = config.exercise_name || '';
        document.getElementById('exerciseBaseDate').value = config.exercise_base_date || new Date().toISOString().split('T')[0];
        document.getElementById('description').value = config.description || '';
        
        // Medical facility defaults
        if (config.medical_facility_defaults) {
            this.loadFacilityDefaults(config.medical_facility_defaults);
        }
        
        // Clear existing fronts
        document.getElementById('frontsList').innerHTML = '';
        this.fronts.clear();
        this.frontCounter = 0;
        
        // Load fronts
        if (config.fronts && config.fronts.length > 0) {
            config.fronts.forEach((front, index) => {
                this.addFront(index);
                this.loadFront(Array.from(this.fronts.keys())[index], front);
            });
        } else {
            this.addFront(0);
        }
        
        // Injury distribution
        if (config.injury_distribution) {
            document.getElementById('injury_disease').value = config.injury_distribution['Disease'] || 50;
            document.getElementById('injury_nonbattle').value = config.injury_distribution['Non-Battle Injury'] || 40;
            document.getElementById('injury_battle').value = config.injury_distribution['Battle Trauma'] || 10;
            
            // Update displays
            document.querySelector('#injury_disease + .percentage-display').textContent = (config.injury_distribution['Disease'] || 50) + '%';
            document.querySelector('#injury_nonbattle + .percentage-display').textContent = (config.injury_distribution['Non-Battle Injury'] || 40) + '%';
            document.querySelector('#injury_battle + .percentage-display').textContent = (config.injury_distribution['Battle Trauma'] || 10) + '%';
            
            this.updateInjuryTotal();
        }
        
        // Output configuration
        document.getElementById('format_json').checked = config.output_formats?.includes('json') ?? true;
        document.getElementById('format_xml').checked = config.output_formats?.includes('xml') ?? true;
        document.getElementById('format_csv').checked = config.output_formats?.includes('csv') ?? false;
        document.getElementById('use_compression').checked = config.use_compression ?? true;
        document.getElementById('use_encryption').checked = config.use_encryption ?? true;
        document.getElementById('encryption_password').value = config.encryption_password || '';
    }

    loadFacilityDefaults(defaults) {
        Object.entries(defaults).forEach(([facility, data]) => {
            document.getElementById(`default_${facility}_capacity`).value = data.capacity || 0;
            document.getElementById(`default_${facility}_kia_rate`).value = (data.kia_rate * 100) || 0;
            document.getElementById(`default_${facility}_rtd_rate`).value = (data.rtd_rate * 100) || 0;
        });
    }

    loadFront(frontId, frontData) {
        document.getElementById(`${frontId}_name`).value = frontData.name || '';
        document.getElementById(`${frontId}_type`).value = frontData.type || 'Training';
        document.getElementById(`${frontId}_casualty_rate`).value = (frontData.casualty_rate * 100) || 100;
        
        // Load nationality distribution
        const container = document.getElementById(`${frontId}_nationalities`);
        container.innerHTML = '';
        
        Object.entries(frontData.nationality_distribution || {}).forEach(([nationality, percentage]) => {
            this.addNationality(frontId);
            const lastItem = container.lastElementChild;
            lastItem.querySelector('select').value = nationality;
            lastItem.querySelector('input').value = percentage;
        });
        
        // Load custom facilities if present
        if (frontData.medical_facilities) {
            document.getElementById(`${frontId}_use_custom_facilities`).checked = true;
            document.getElementById(`${frontId}_custom_facilities`).classList.add('show');
            
            Object.entries(frontData.medical_facilities).forEach(([facility, data]) => {
                document.getElementById(`${frontId}_${facility}_capacity`).value = data.capacity || 0;
                document.getElementById(`${frontId}_${facility}_kia_rate`).value = (data.kia_rate * 100) || 0;
                document.getElementById(`${frontId}_${facility}_rtd_rate`).value = (data.rtd_rate * 100) || 0;
            });
        }
    }

    updateValidationState(validation) {
        // Clear previous validation states
        document.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
        document.querySelectorAll('.invalid-feedback').forEach(el => el.remove());
        
        if (!validation.isValid) {
            validation.errors.forEach(error => {
                // Find the field and mark it as invalid
                const field = this.findFieldByPath(error.field);
                if (field) {
                    field.classList.add('is-invalid');
                    
                    // Add error message
                    const feedback = document.createElement('div');
                    feedback.className = 'invalid-feedback';
                    feedback.textContent = error.message;
                    field.parentElement.appendChild(feedback);
                }
            });
        }
        
        // Update generate button state
        const generateBtn = document.getElementById('generateBtn');
        generateBtn.disabled = !validation.isValid;
    }

    findFieldByPath(path) {
        // Map field paths to element IDs
        const fieldMap = {
            'total_patients': 'totalPatients',
            'exercise_base_date': 'exerciseBaseDate',
            // Add more mappings as needed
        };
        
        return document.getElementById(fieldMap[path]);
    }

    resetFacilityDefaults() {
        const defaults = {
            point_of_injury: { capacity: 0, kia: 2.5, rtd: 10.0 },
            role_1: { capacity: 10, kia: 1.0, rtd: 15.0 },
            role_2: { capacity: 50, kia: 0.5, rtd: 30.0 },
            role_3: { capacity: 200, kia: 0.2, rtd: 25.0 },
            role_4: { capacity: 500, kia: 0.1, rtd: 40.0 }
        };
        
        Object.entries(defaults).forEach(([facility, values]) => {
            document.getElementById(`default_${facility}_capacity`).value = values.capacity;
            document.getElementById(`default_${facility}_kia_rate`).value = values.kia;
            document.getElementById(`default_${facility}_rtd_rate`).value = values.rtd;
        });
        
        document.dispatchEvent(new Event('config-changed'));
    }

    updateTemplateList(templates) {
        const select = document.getElementById('templateSelect');
        select.innerHTML = '<option value="">Select a template...</option>';
        
        templates.forEach(template => {
            const option = document.createElement('option');
            option.value = template.id;
            option.textContent = template.name;
            select.appendChild(option);
        });
    }

    getFronts() {
        return Array.from(this.fronts.values());
    }
}