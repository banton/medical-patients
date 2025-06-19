/**
 * Medical Patients Generator - Main Application
 * Modern frontend with v1 API integration and accordion interface
 */

/* eslint no-console: "off" */

class PatientGeneratorApp {
    constructor() {
        this.apiClient = null; // Will be set when config is ready
        this.accordion = null;
        this.currentJobId = null;
        this.pollingPromise = null;

        // Generation metrics tracking
        this.generationStartTime = null;
        this.generationData = {
            patientCount: null,
            duration: null,
            fileSize: null
        };

        // Configuration history tracking
        this.configHistory = this.loadConfigHistory();

        // Progress animation state
        this.progressSimulation = null;
        this.simulatedProgress = 0;

        // DOM elements
        this.generateBtn = null;
        this.statusBox = null;
        this.statusMessage = null;
        this.progressBar = null;
        this.progressContainer = null;
        this.downloadContainer = null;

        // Progress messages for fun UX
        this.progressMessages = [
            'Rolling dice for combat injuries...',
            'Consulting field medics for realistic injuries...',
            'Distributing casualties across battle fronts...',
            'Generating realistic warfare patterns...',
            'Simulating artillery bombardment timing...',
            'Calculating environmental impact on casualties...',
            'Processing mass casualty event clusters...',
            'Assigning triage categories...',
            'Creating believable medical histories...',
            'Randomizing arrival patterns with timeline data...',
            'Double-checking NATO personnel IDs...',
            'Simulating evacuation priorities...',
            'Adding battlefield dust for authenticity...',
            'Modeling realistic operational patterns...',
            'Generating convincing vital signs...',
            'Cross-referencing warfare-specific injury patterns...',
            'Applying night operations modifiers...',
            'Synchronizing timeline viewer compatibility...'
        ];

        this.currentMessageIndex = 0;
        this.messageInterval = null;
    }

    async init() {
        // console.log('🚀 Initializing Patient Generator App...');

        // Get DOM elements
        this.getDOMElements();

        // Set up event listeners
        this.bindEvents();

        // Wait for accordion to be ready
        this.waitForAccordion();

        // Wait for API client to be ready
        await this.waitForApiClient();

        // Load initial data
        await this.loadInitialData();

        // Initialize configuration history display
        this.updateConfigHistoryDisplay();

        // console.log('✅ Patient Generator App initialized');
    }

    getDOMElements() {
        this.generateBtn = document.getElementById('generateBtn');
        this.statusBox = document.getElementById('statusBox');
        this.statusMessage = document.getElementById('statusMessage');
        this.progressBar = document.getElementById('progressBar');
        this.progressContainer = document.getElementById('progressContainer');
        this.downloadContainer = document.getElementById('downloadContainer');

        // Validate required elements
        const required = ['generateBtn', 'statusBox', 'statusMessage'];
        for (const elementName of required) {
            if (!this[elementName]) {
                console.error(`Required element not found: ${elementName}`);
            }
        }
    }

    bindEvents() {
        // Generate button
        if (this.generateBtn) {
            this.generateBtn.addEventListener('click', () => this.handleGenerate());
        }

        // Accordion events
        document.addEventListener('accordion:validate', (e) => {
            this.updateGenerateButtonState();
            this.updateConfigurationOverview();
        });

        // Also listen for accordion changes (when content is loaded)
        document.addEventListener('accordion:change', (e) => {
            this.updateConfigurationOverview();
        });

        // Periodic update as fallback for real-time editing
        setInterval(() => {
            this.updateConfigurationOverview();
        }, 1000);

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                this.handleGenerate();
            }
        });
    }

    waitForAccordion() {
        // Wait for accordion to be initialized
        const checkAccordion = () => {
            if (window.accordion) {
                this.accordion = window.accordion;
                // Wait a bit more for initial validation to complete
                setTimeout(() => {
                    this.updateGenerateButtonState();
                    this.updateConfigurationOverview();
                    this.setupDirectTextareaListeners();
                }, 50);
            } else {
                setTimeout(checkAccordion, 100);
            }
        };
        checkAccordion();
    }

    setupDirectTextareaListeners() {
        // Listen directly to textarea input events for immediate updates
        const textareas = document.querySelectorAll('.accordion__editor');
        textareas.forEach((textarea) => {
            textarea.addEventListener('input', () => {
                // Debounce the update to avoid excessive calls
                clearTimeout(this.updateTimeout);
                this.updateTimeout = setTimeout(() => {
                    this.updateConfigurationOverview();
                }, 300);
            });
        });
    }

    async waitForApiClient() {
        // Wait for API client to be initialized
        return new Promise((resolve) => {
            const checkApiClient = () => {
                if (window.apiClient) {
                    this.apiClient = window.apiClient;
                    resolve();
                } else {
                    setTimeout(checkApiClient, 100);
                }
            };
            checkApiClient();
        });
    }

    async loadInitialData() {
        try {
            // Test API connection
            const isHealthy = await this.apiClient.healthCheck();
            if (!isHealthy) {
                this.showError('⚠️ Backend API is not responding. Please check the server.');
                return;
            }

            // Load reference data for validation
            await this.loadNationalityData();

            // console.log('📡 API connection established');
        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.showError(`Failed to connect to API: ${error.message}`);
        }
    }

    async loadNationalityData() {
        try {
            const nationalities = await this.apiClient.getNationalities();
            this.validNationalityCodes = new Set(nationalities.map((n) => n.code));
            // console.log(`📊 Loaded ${nationalities.length} nationality codes`);
        } catch (error) {
            console.warn('Could not load nationality data:', error.message);
            // Fallback to common NATO codes
            this.validNationalityCodes = new Set([
                'USA',
                'GBR',
                'CAN',
                'FRA',
                'DEU',
                'ITA',
                'ESP',
                'NLD',
                'BEL',
                'PRT',
                'NOR',
                'DNK',
                'ISL',
                'LUX',
                'GRC',
                'TUR',
                'POL',
                'CZE',
                'HUN',
                'SVK',
                'SVN',
                'EST',
                'LVA',
                'LTU',
                'BGR',
                'ROU',
                'HRV',
                'ALB',
                'MNE',
                'MKD'
            ]);
        }
    }

    updateGenerateButtonState() {
        if (!this.accordion || !this.generateBtn) return;

        const isValid = this.accordion.isAllValid();
        const isGenerating = this.currentJobId !== null;

        this.generateBtn.disabled = !isValid || isGenerating;

        // Clear existing content and classes
        this.generateBtn.className = 'generate-button';

        if (!isValid) {
            this.generateBtn.innerHTML = `
                <div class="flex items-center justify-center">
                    <i class="fas fa-exclamation-triangle mr-2"></i>
                    <span>Fix Configuration First</span>
                </div>
            `;
            this.generateBtn.title = 'Please fix validation errors in the configuration sections';
            this.generateBtn.classList.add('button-error');
        } else if (isGenerating) {
            this.generateBtn.innerHTML = `
                <div class="flex items-center justify-center">
                    <i class="fas fa-spinner fa-spin mr-2"></i>
                    <span>Generating...</span>
                </div>
            `;
            this.generateBtn.title = 'Generation in progress';
            this.generateBtn.classList.add('button-loading');
        } else {
            this.generateBtn.innerHTML = `
                <div class="flex items-center justify-center">
                    <i class="fas fa-bolt mr-2"></i>
                    <span>Generate Patients</span>
                </div>
            `;
            this.generateBtn.title = 'Start patient generation with current configuration';
        }
    }

    updateConfigurationOverview() {
        if (!this.accordion) return;

        try {
            // Get current accordion content
            const [frontsJson, scenarioJson] = this.accordion.getAllContent();

            // Debug: Check if we're getting content
            // console.log('Updating config overview with:', { frontsJson: frontsJson?.substring(0, 50), scenarioJson: scenarioJson?.substring(0, 50) });

            // Parse JSON safely
            let fronts, scenario;
            try {
                fronts = JSON.parse(frontsJson || '{"front_configs": []}');
                scenario = JSON.parse(scenarioJson || '{"total_patients": 1440}');
            } catch (parseError) {
                // If JSON is invalid, use defaults
                this.setDefaultConfigurationOverview();
                return;
            }

            // Update Total Patients
            const totalPatientsEl = document.getElementById('totalPatients');
            if (totalPatientsEl) {
                const totalPatients = scenario.total_patients || 1440;
                totalPatientsEl.textContent = totalPatients.toLocaleString();
            }

            // Update Battle Fronts count
            const totalFrontsEl = document.getElementById('totalFronts');
            if (totalFrontsEl) {
                const frontCount = fronts.front_configs?.length || 0;
                totalFrontsEl.textContent = frontCount.toString();
            }

            // Update Nationalities list
            const nationalityListEl = document.getElementById('nationalityList');
            if (nationalityListEl) {
                const nationalities = this.extractNationalitiesFromFronts(fronts.front_configs || []);
                nationalityListEl.textContent = nationalities.length > 0 ? nationalities.join(', ') : 'None configured';
            }

            // Update Battle Duration
            const battleDurationEl = document.getElementById('battleDuration');
            if (battleDurationEl) {
                const days = scenario.days_of_fighting || 1;
                battleDurationEl.textContent = `${days} day${days !== 1 ? 's' : ''}`;
            }

            // Update Warfare Types
            const warfareTypesEl = document.getElementById('warfareTypes');
            if (warfareTypesEl) {
                this.updateWarfareTypesDisplay(warfareTypesEl, scenario.warfare_types || {});
            }
        } catch (error) {
            console.warn('Failed to update configuration overview:', error);
            this.setDefaultConfigurationOverview();
        }
    }

    extractNationalitiesFromFronts(frontConfigs) {
        const nationalitySet = new Set();
        frontConfigs.forEach((front) => {
            if (front.nationality_distribution) {
                front.nationality_distribution.forEach((natDist) => {
                    if (natDist.nationality_code) {
                        nationalitySet.add(natDist.nationality_code);
                    }
                });
            }
        });
        return Array.from(nationalitySet).sort();
    }

    updateWarfareTypesDisplay(container, warfareTypes) {
        // Define warfare type colors
        const warfareColors = {
            conventional: 'bg-red-100 text-red-700',
            artillery: 'bg-orange-100 text-orange-700',
            urban: 'bg-yellow-100 text-yellow-700',
            guerrilla: 'bg-green-100 text-green-700',
            drone: 'bg-blue-100 text-blue-700',
            naval: 'bg-indigo-100 text-indigo-700',
            cbrn: 'bg-purple-100 text-purple-700',
            peacekeeping: 'bg-pink-100 text-pink-700'
        };

        // Get enabled warfare types
        const enabledTypes = Object.keys(warfareTypes).filter((type) => warfareTypes[type]);

        if (enabledTypes.length === 0) {
            container.innerHTML = '<span class="text-slate-500 text-xs">None configured</span>';
            return;
        }

        // Create warfare type badges
        const badges = enabledTypes
            .map((type) => {
                const colorClass = warfareColors[type] || 'bg-slate-100 text-slate-700';
                const displayName = type.charAt(0).toUpperCase() + type.slice(1);
                return `<span class="${colorClass} px-2 py-1 rounded text-xs font-medium">${displayName}</span>`;
            })
            .join('');

        container.innerHTML = badges;
    }

    setDefaultConfigurationOverview() {
        // Set default values when configuration cannot be parsed
        const elements = {
            totalPatients: '1,440',
            totalFronts: '0',
            nationalityList: 'None configured',
            battleDuration: '1 day',
            warfareTypes: '<span class="text-slate-500 text-xs">None configured</span>'
        };

        Object.entries(elements).forEach(([id, defaultValue]) => {
            const element = document.getElementById(id);
            if (element) {
                if (id === 'warfareTypes') {
                    element.innerHTML = defaultValue;
                } else {
                    element.textContent = defaultValue;
                }
            }
        });
    }

    async handleGenerate() {
        if (!this.accordion || !this.accordion.isAllValid()) {
            this.showError('Please fix all configuration errors before generating patients.');
            return;
        }

        try {
            // Start generation timer
            this.generationStartTime = Date.now();

            // Disable UI and update button state
            this.currentJobId = 'pending';
            this.updateGenerateButtonState();

            // Show initial status and scroll into view
            this.showStatus();
            this.scrollToStatus();
            this.setStatusMessage('🚀 Starting patient generation...');

            // Build configuration from accordion
            const configuration = this.buildConfiguration();

            // Store expected patient count for later display
            this.generationData.patientCount = configuration.total_patients;

            // Validate configuration
            this.validateConfiguration(configuration);

            // Start simulated progress animation
            this.startProgressSimulation();

            // Start generation
            // The API expects configuration at the root level
            const response = await this.apiClient.generatePatients({
                configuration,
                output_formats: ['json', 'csv']
            });

            this.currentJobId = response.job_id;
            this.setStatusMessage(`✅ Generation started<br>Job ID: <code>${this.currentJobId}</code>`);

            // Save configuration to history
            this.addToConfigHistory(configuration);

            // Start polling with fun progress messages
            await this.pollJobWithProgress();
        } catch (error) {
            console.error('Generation failed:', error);
            this.showError(`Generation failed: ${error.message}`);
            this.stopProgressSimulation();
            this.resetUI();
        }
    }

    buildConfiguration() {
        const [frontsJson, temporalJson] = this.accordion.getAllContent();

        const fronts = JSON.parse(frontsJson);
        const temporal = JSON.parse(temporalJson);

        // Check if scenario format is being used
        if (temporal.warfare_types || temporal.environmental_conditions || temporal.special_events) {
            // New scenario configuration format
            return {
                name: `Patient Generation ${new Date().toLocaleString()}`,
                description: 'Generated from web interface with scenario patterns',
                total_patients: temporal.total_patients || 1440,
                days_of_fighting: temporal.days_of_fighting || 8,
                base_date: temporal.base_date || '2025-06-01',
                warfare_types: temporal.warfare_types || {},
                intensity: temporal.intensity || 'medium',
                tempo: temporal.tempo || 'sustained',
                special_events: temporal.special_events || {},
                environmental_conditions: temporal.environmental_conditions || {},
                injury_mix: temporal.injury_mix || temporal.injury_distribution,
                front_configs: fronts.front_configs,
                facility_configs: this.generateFacilityConfigs(fronts.front_configs)
            };
        } else {
            // Legacy configuration format (backward compatibility)
            return {
                name: `Patient Generation ${new Date().toLocaleString()}`,
                description: 'Generated from web interface',
                total_patients: temporal.total_patients || 1440,
                injury_distribution: temporal.injury_distribution,
                front_configs: fronts.front_configs,
                facility_configs: this.generateFacilityConfigs(fronts.front_configs)
            };
        }
    }

    generateFacilityConfigs(frontConfigs) {
        // Auto-generate facility configs based on fronts
        return frontConfigs.map((front) => ({
            id: `role2_${front.id}`,
            name: `Role 2 ${front.name}`,
            capacity: Math.floor(1000 * front.casualty_rate),
            role: 'Role 2',
            front_id: front.id,
            kia_rate: 0.05,
            rtd_rate: 0.85
        }));
    }

    validateConfiguration(config) {
        // Additional validation beyond accordion checks
        if (!config.total_patients || config.total_patients < 1) {
            throw new Error('Total patients must be at least 1');
        }

        if (!config.front_configs || config.front_configs.length === 0) {
            throw new Error('At least one battle front must be configured');
        }

        // Validate nationality codes against loaded data
        if (this.validNationalityCodes) {
            for (const front of config.front_configs) {
                for (const natDist of front.nationality_distribution) {
                    if (!this.validNationalityCodes.has(natDist.nationality_code)) {
                        console.warn(`Unknown nationality code: ${natDist.nationality_code}`);
                    }
                }
            }
        }

        // Temporal configuration validation
        if (config.warfare_types) {
            // Validate temporal-specific fields
            if (config.days_of_fighting && config.days_of_fighting < 1) {
                throw new Error('Days of fighting must be at least 1');
            }

            if (config.intensity && !['low', 'medium', 'high', 'extreme'].includes(config.intensity)) {
                throw new Error('Intensity must be one of: low, medium, high, extreme');
            }

            if (
                config.tempo &&
                !['sustained', 'escalating', 'surge', 'declining', 'intermittent'].includes(config.tempo)
            ) {
                throw new Error('Tempo must be one of: sustained, escalating, surge, declining, intermittent');
            }

            // Validate injury mix percentages sum to 1.0
            if (config.injury_mix) {
                const sum = Object.values(config.injury_mix).reduce((acc, val) => acc + val, 0);
                if (Math.abs(sum - 1.0) > 0.01) {
                    throw new Error('Injury mix percentages must sum to 1.0');
                }
            }
        }
    }

    async pollJobWithProgress() {
        this.startProgressMessages();

        try {
            const result = await this.apiClient.pollJobStatus(
                this.currentJobId,
                (job) => this.updateProgress(job),
                300000 // 5 minute timeout
            );

            this.stopProgressMessages();
            this.handleJobComplete(result);
        } catch (error) {
            this.stopProgressMessages();

            if (error.status === 408) {
                this.showError('⏱️ Generation timed out. The job may still be running on the server.');
            } else {
                this.showError(`Generation failed: ${error.message}`);
            }

            this.resetUI();
        }
    }

    updateProgress(job) {
        const percentage = job.progress || this.simulatedProgress;

        // Update progress bar
        if (this.progressBar) {
            this.progressBar.style.width = `${percentage}%`;
        }

        if (this.progressContainer) {
            this.progressContainer.style.display = 'block';
        }

        // Calculate current generation time
        const currentDuration = this.generationStartTime ? (Date.now() - this.generationStartTime) / 1000 : 0;

        let phase = 'Processing...';
        if (percentage < 15) phase = 'Validating configurations...';
        else if (percentage < 30) phase = 'Initializing patient generator...';
        else if (percentage < 85) phase = `Generating patients... (${Math.floor(percentage)}%)`;
        else if (percentage < 95) phase = 'Finalizing medical records...';
        else phase = 'Creating downloadable archives...';

        this.setStatusMessage(`
            <div class="status-details">
                <div class="status-row">
                    <strong>Status:</strong> ${job.status} 
                    <i class="fas fa-spinner fa-spin text-cyan-600 ml-2"></i>
                </div>
                <div class="status-row">
                    <strong>Phase:</strong> ${phase}
                </div>
                <div class="status-row">
                    <strong>Progress:</strong> ${Math.floor(percentage)}%
                </div>
                <div class="status-row">
                    <strong>Expected Patients:</strong> ${this.generationData.patientCount?.toLocaleString() || 'Unknown'}
                </div>
                <div class="status-row">
                    <strong>Generation Time:</strong> ${this.formatDuration(currentDuration)}
                </div>
            </div>
        `);
    }

    handleJobComplete(job) {
        // Stop progress simulation and calculate final metrics
        this.stopProgressSimulation();

        // Calculate final generation time
        const finalDuration = this.generationStartTime ? (Date.now() - this.generationStartTime) / 1000 : job.duration;
        this.generationData.duration = finalDuration;

        // Extract patient count from job result or use expected count
        const totalPatients =
            job.result?.total_patients || job.result?.patient_count || this.generationData.patientCount || 'Unknown';

        // Extract file size if available
        this.generationData.fileSize = job.result?.file_size || null;

        // Ensure progress bar shows 100%
        if (this.progressBar) {
            this.progressBar.style.width = '100%';
        }

        // Show success animation
        this.setStatusMessage(`
            <div class="success">
                <div class="success-icon">
                    <i class="fas fa-check-circle text-emerald-500 mr-2 animate-pulse"></i>
                    <strong>Generation completed successfully!</strong>
                </div>
                <div class="completion-stats">
                    <div class="stat-item">
                        <strong>📊 Total Patients:</strong> ${typeof totalPatients === 'number' ? totalPatients.toLocaleString() : totalPatients}
                    </div>
                    <div class="stat-item">
                        <strong>⏱️ Generation Time:</strong> ${this.formatDuration(finalDuration)}
                    </div>
                    <div class="stat-item">
                        <strong>💾 File Size:</strong> ${this.generationData.fileSize ? this.formatFileSize(this.generationData.fileSize) : 'Calculating...'}
                    </div>
                </div>
            </div>
        `);

        this.showDownloadOptions(job);
        this.resetUI();
    }

    showDownloadOptions(job) {
        if (!this.downloadContainer) return;

        // Try to get file size from multiple sources
        let fileSize = job.result?.file_size || job.result?.size || this.generationData.fileSize;
        const fileSizeDisplay = fileSize ? this.formatFileSize(fileSize) : 'File ready for download';

        this.downloadContainer.innerHTML = `
            <div class="download-section">
                <h4>
                    <i class="fas fa-download text-emerald-600 mr-2"></i>
                    Download Results
                </h4>
                <p>Your generated patient data is ready for download:</p>
                <button onclick="app.downloadResults('${this.currentJobId}')" class="download-link">
                    <i class="fas fa-download mr-2"></i>
                    Download Patient Data (ZIP)
                </button>
                <div class="download-info">
                    <div class="info-item">
                        <i class="fas fa-hdd text-slate-500 mr-1"></i>
                        <strong>File Size:</strong> ${fileSizeDisplay}
                    </div>
                    <div class="info-item">
                        <i class="fas fa-tag text-slate-500 mr-1"></i>
                        <strong>Job ID:</strong> <code>${this.currentJobId}</code>
                    </div>
                    <div class="info-item">
                        <i class="fas fa-file-archive text-slate-500 mr-1"></i>
                        <strong>Formats:</strong> JSON, CSV
                    </div>
                </div>
            </div>
        `;
    }

    async downloadResults(jobId) {
        try {
            this.setStatusMessage('📥 Preparing download...');

            const blob = await this.apiClient.downloadJobResults(jobId);

            // Store file size if not already captured
            if (!this.generationData.fileSize && blob.size) {
                this.generationData.fileSize = blob.size;

                // Update the file size display in the download section
                const fileSizeElement = document.querySelector('.download-info .info-item:first-child');
                if (fileSizeElement) {
                    fileSizeElement.innerHTML = `
                        <i class="fas fa-hdd text-slate-500 mr-1"></i>
                        <strong>File Size:</strong> ${this.formatFileSize(blob.size)}
                    `;
                }
            }

            // Create download
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `patient_data_${jobId}.zip`;

            document.body.appendChild(a);
            a.click();

            // Cleanup
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            this.setStatusMessage('✅ Download started successfully!');
        } catch (error) {
            console.error('Download failed:', error);
            this.showError(`Download failed: ${error.message}`);
        }
    }

    startProgressMessages() {
        this.currentMessageIndex = 0;
        this.messageInterval = setInterval(() => {
            const message = this.progressMessages[this.currentMessageIndex];
            const funMessageElement = document.getElementById('funMessage');

            if (funMessageElement) {
                funMessageElement.textContent = message;
            } else {
                // Add fun message to status if element doesn't exist
                const currentStatus = this.statusMessage.innerHTML;
                const updatedStatus = currentStatus.replace(
                    /<div class="fun-message">.*?<\/div>/,
                    `<div class="fun-message">💭 ${message}</div>`
                );

                if (updatedStatus === currentStatus) {
                    this.statusMessage.innerHTML += `<div class="fun-message">💭 ${message}</div>`;
                } else {
                    this.statusMessage.innerHTML = updatedStatus;
                }
            }

            this.currentMessageIndex = (this.currentMessageIndex + 1) % this.progressMessages.length;
        }, 3000); // Change message every 3 seconds
    }

    stopProgressMessages() {
        if (this.messageInterval) {
            clearInterval(this.messageInterval);
            this.messageInterval = null;
        }
    }

    startProgressSimulation() {
        // Start with fast progress, then slow down, then speed up near end
        this.simulatedProgress = 0;

        this.progressSimulation = setInterval(() => {
            if (this.simulatedProgress < 20) {
                // Fast start (0-20%)
                this.simulatedProgress += Math.random() * 3 + 1;
            } else if (this.simulatedProgress < 80) {
                // Slow middle (20-80%)
                this.simulatedProgress += Math.random() * 0.8 + 0.2;
            } else if (this.simulatedProgress < 95) {
                // Speed up near end (80-95%)
                this.simulatedProgress += Math.random() * 2 + 0.5;
            } else {
                // Hold at 95% until real completion
                this.simulatedProgress = 95;
            }

            // Cap at 95% to wait for real completion
            this.simulatedProgress = Math.min(this.simulatedProgress, 95);

            // Update progress bar if no real progress available
            if (this.progressBar && this.simulatedProgress < 95) {
                this.progressBar.style.width = `${this.simulatedProgress}%`;
            }
        }, 800); // Update every 800ms for smooth animation
    }

    stopProgressSimulation() {
        if (this.progressSimulation) {
            clearInterval(this.progressSimulation);
            this.progressSimulation = null;
        }
    }

    showStatus() {
        if (this.statusBox) {
            this.statusBox.classList.add('show');
        }
    }

    scrollToStatus() {
        if (this.statusBox) {
            // Small delay to ensure the status box is visible before scrolling
            setTimeout(() => {
                this.statusBox.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start',
                    inline: 'nearest'
                });
            }, 100);
        }
    }

    setStatusMessage(message) {
        if (this.statusMessage) {
            this.statusMessage.innerHTML = message;
        }
    }

    showError(message) {
        this.setStatusMessage(`<div class="error">❌ ${message}</div>`);
        this.showStatus();
    }

    resetUI() {
        this.currentJobId = null;
        this.stopProgressSimulation();
        this.stopProgressMessages();
        this.updateGenerateButtonState();

        // Reset generation metrics
        this.generationStartTime = null;
        this.generationData = {
            patientCount: null,
            duration: null,
            fileSize: null
        };
    }

    formatDuration(seconds) {
        if (!seconds || seconds < 0) return '0.0s';

        if (seconds < 60) {
            return `${seconds.toFixed(1)}s`;
        }

        if (seconds < 3600) {
            const minutes = Math.floor(seconds / 60);
            const remainingSeconds = Math.floor(seconds % 60);
            return `${minutes}m ${remainingSeconds}s`;
        }

        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${minutes}m`;
    }

    formatFileSize(bytes) {
        if (!bytes) return 'Unknown';

        const sizes = ['B', 'KB', 'MB', 'GB'];
        let i = 0;

        while (bytes >= 1024 && i < sizes.length - 1) {
            bytes /= 1024;
            i++;
        }

        return `${bytes.toFixed(1)} ${sizes[i]}`;
    }

    // Configuration history management
    loadConfigHistory() {
        try {
            const stored = localStorage.getItem('medpatgen_config_history');
            return stored ? JSON.parse(stored) : [];
        } catch (error) {
            console.warn('Failed to load configuration history:', error);
            return [];
        }
    }

    saveConfigHistory() {
        try {
            localStorage.setItem('medpatgen_config_history', JSON.stringify(this.configHistory));
        } catch (error) {
            console.warn('Failed to save configuration history:', error);
        }
    }

    addToConfigHistory(configuration) {
        // Create configuration signature for uniqueness check
        const configSignature = this.createConfigurationSignature(configuration);

        // Check if this configuration already exists
        const existingIndex = this.configHistory.findIndex(
            (item) => this.createConfigurationSignature(item.configuration) === configSignature
        );

        const historyItem = {
            id: Date.now().toString(),
            timestamp: new Date().toISOString(),
            name: configuration.name || `Configuration ${new Date().toLocaleString()}`,
            totalPatients: configuration.total_patients,
            frontCount: configuration.front_configs?.length || 0,
            nationalities: this.extractNationalities(configuration.front_configs || []),
            isTemporal: !!(
                configuration.warfare_types ||
                configuration.environmental_conditions ||
                configuration.special_events
            ),
            warfareTypes: configuration.warfare_types
                ? Object.keys(configuration.warfare_types).filter((k) => configuration.warfare_types[k])
                : [],
            intensity: configuration.intensity,
            tempo: configuration.tempo,
            daysOfFighting: configuration.days_of_fighting,
            configuration: configuration
        };

        if (existingIndex !== -1) {
            // Remove existing duplicate and add updated version at the beginning
            this.configHistory.splice(existingIndex, 1);
            this.configHistory.unshift(historyItem);
            // console.log('📝 Updated existing configuration in history');
        } else {
            // Add new configuration to beginning of array
            this.configHistory.unshift(historyItem);
            // console.log('📝 Added new configuration to history');
        }

        // Keep only last 3 unique configurations
        this.configHistory = this.configHistory.slice(0, 3);

        // Save to localStorage
        this.saveConfigHistory();

        // Update UI
        this.updateConfigHistoryDisplay();
    }

    createConfigurationSignature(configuration) {
        // Create a unique signature based on the meaningful content of the configuration
        // This helps identify truly unique configurations vs just timestamp differences
        const signature = {
            total_patients: configuration.total_patients,
            injury_distribution: configuration.injury_distribution,
            injury_mix: configuration.injury_mix,
            warfare_types: configuration.warfare_types,
            intensity: configuration.intensity,
            tempo: configuration.tempo,
            special_events: configuration.special_events,
            environmental_conditions: configuration.environmental_conditions,
            days_of_fighting: configuration.days_of_fighting,
            front_configs: configuration.front_configs
                ?.map((front) => ({
                    id: front.id,
                    name: front.name,
                    casualty_rate: front.casualty_rate,
                    nationality_distribution: front.nationality_distribution?.sort((a, b) =>
                        a.nationality_code.localeCompare(b.nationality_code)
                    )
                }))
                .sort((a, b) => a.id.localeCompare(b.id))
        };

        // Return JSON string as signature (normalized and sorted for consistency)
        return JSON.stringify(signature);
    }

    extractNationalities(frontConfigs) {
        const nationalitySet = new Set();
        frontConfigs.forEach((front) => {
            if (front.nationality_distribution) {
                front.nationality_distribution.forEach((natDist) => {
                    nationalitySet.add(natDist.nationality_code);
                });
            }
        });
        return Array.from(nationalitySet).sort();
    }

    loadConfiguration(historyId) {
        const historyItem = this.configHistory.find((item) => item.id === historyId);
        if (!historyItem || !this.accordion) {
            console.warn('Configuration not found or accordion not ready');
            return;
        }

        try {
            const config = historyItem.configuration;

            // Extract front configs and temporal/injury configuration
            const frontsJson = JSON.stringify(
                {
                    front_configs: config.front_configs
                },
                null,
                2
            );

            // Check if this is scenario or legacy configuration
            let configJson;
            if (config.warfare_types || config.environmental_conditions || config.special_events) {
                // Scenario configuration format
                configJson = JSON.stringify(
                    {
                        total_patients: config.total_patients,
                        days_of_fighting: config.days_of_fighting,
                        base_date: config.base_date,
                        warfare_types: config.warfare_types,
                        intensity: config.intensity,
                        tempo: config.tempo,
                        special_events: config.special_events,
                        environmental_conditions: config.environmental_conditions,
                        injury_mix: config.injury_mix
                    },
                    null,
                    2
                );
            } else {
                // Legacy configuration format
                configJson = JSON.stringify(
                    {
                        injury_distribution: config.injury_distribution,
                        total_patients: config.total_patients
                    },
                    null,
                    2
                );
            }

            // Set accordion content
            this.accordion.setContent(0, frontsJson); // Battle Fronts
            this.accordion.setContent(1, configJson); // Scenario/Injury Configuration

            // Trigger validation
            setTimeout(() => {
                this.accordion.validateAllItems();
            }, 100);

            // console.log(`✅ Loaded configuration: ${historyItem.name}`);
        } catch (error) {
            console.error('Failed to load configuration:', error);
            this.showError(`Failed to load configuration: ${error.message}`);
        }
    }

    updateConfigHistoryDisplay() {
        const configPanel = document.getElementById('configHistoryPanel');
        if (!configPanel) return;

        if (this.configHistory.length === 0) {
            configPanel.innerHTML = `
                <div class="text-center text-slate-500 py-6">
                    <i class="fas fa-history text-2xl mb-2 opacity-50"></i>
                    <p class="text-sm">No configurations generated yet. Try your first one!</p>
                </div>
            `;
            return;
        }

        const historyHTML = this.configHistory
            .map((item) => {
                const timeAgo = this.formatTimeAgo(new Date(item.timestamp));
                const nationalitiesDisplay =
                    item.nationalities.slice(0, 3).join(', ') +
                    (item.nationalities.length > 3 ? ` +${item.nationalities.length - 3}` : '');

                // Create scenario or legacy indicator
                const typeIndicator = item.isTemporal
                    ? `<span class="bg-cyan-100 text-cyan-700 px-2 py-1 rounded text-xs font-medium mr-2">Scenario</span>`
                    : `<span class="bg-slate-100 text-slate-700 px-2 py-1 rounded text-xs font-medium mr-2">Legacy</span>`;

                // Create warfare types display for scenario configs
                const warfareDisplay =
                    item.isTemporal && item.warfareTypes.length > 0
                        ? item.warfareTypes.slice(0, 2).join(', ') +
                          (item.warfareTypes.length > 2 ? ` +${item.warfareTypes.length - 2}` : '')
                        : '';

                return `
                <div class="config-history-item">
                    <div class="config-history-header">
                        <div class="config-history-title">
                            <i class="fas fa-${item.isTemporal ? 'clock' : 'cog'} text-cyan-600 mr-2"></i>
                            <span class="font-medium text-slate-800">${this.escapeHtml(item.name)}</span>
                        </div>
                        <div class="config-history-time">
                            ${typeIndicator}
                            <i class="fas fa-clock text-slate-400 mr-1"></i>
                            <span class="text-xs text-slate-500">${timeAgo}</span>
                        </div>
                    </div>
                    <div class="config-history-stats">
                        <div class="stat">
                            <i class="fas fa-map-marked-alt text-slate-500"></i>
                            <span>${item.frontCount} front${item.frontCount !== 1 ? 's' : ''}</span>
                        </div>
                        <div class="stat">
                            <i class="fas fa-flag text-slate-500"></i>
                            <span title="${item.nationalities.join(', ')}">${nationalitiesDisplay}</span>
                        </div>
                        <div class="stat">
                            <i class="fas fa-users text-slate-500"></i>
                            <span>${item.totalPatients?.toLocaleString() || 'Unknown'} patients</span>
                        </div>
                        ${
                            item.isTemporal
                                ? `
                        <div class="stat">
                            <i class="fas fa-crosshairs text-slate-500"></i>
                            <span title="${item.warfareTypes.join(', ')}">${warfareDisplay || 'No warfare'}</span>
                        </div>
                        <div class="stat">
                            <i class="fas fa-calendar text-slate-500"></i>
                            <span>${item.daysOfFighting || 1}d ${item.intensity || 'med'}</span>
                        </div>
                        `
                                : ''
                        }
                    </div>
                    <button 
                        onclick="app.loadConfiguration('${item.id}')" 
                        class="config-load-btn"
                        title="Load this configuration"
                    >
                        <i class="fas fa-download mr-2"></i>
                        Load Configuration
                    </button>
                </div>
            `;
            })
            .join('');

        configPanel.innerHTML = historyHTML;
    }

    formatTimeAgo(date) {
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / (1000 * 60));
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        return date.toLocaleDateString();
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize app when DOM is ready
let app;
document.addEventListener('DOMContentLoaded', async () => {
    app = new PatientGeneratorApp();
    await app.init();
});

// Make app globally available for debugging and download function
if (typeof window !== 'undefined') {
    window.app = app;
}

// console.log('🔧 Patient Generator App loaded');
