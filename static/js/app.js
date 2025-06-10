/**
 * Medical Patients Generator - Main Application
 * Modern frontend with v1 API integration and accordion interface
 */

class PatientGeneratorApp {
    constructor() {
        this.apiClient = window.apiClient;
        this.accordion = null;
        this.currentJobId = null;
        this.pollingPromise = null;
        
        // DOM elements
        this.generateBtn = null;
        this.statusBox = null;
        this.statusMessage = null;
        this.progressBar = null;
        this.progressContainer = null;
        this.downloadContainer = null;
        
        // Progress messages for fun UX
        this.progressMessages = [
            "Rolling dice for combat injuries...",
            "Consulting field medics for realistic injuries...",
            "Distributing casualties across battle fronts...",
            "Assigning triage categories...",
            "Creating believable medical histories...",
            "Randomizing arrival patterns...",
            "Double-checking NATO personnel IDs...",
            "Simulating evacuation priorities...",
            "Adding battlefield dust for authenticity...",
            "Generating convincing vital signs...",
            "Cross-referencing injury patterns..."
        ];
        
        this.currentMessageIndex = 0;
        this.messageInterval = null;
    }
    
    async init() {
        console.log('🚀 Initializing Patient Generator App...');
        
        // Get DOM elements
        this.getDOMElements();
        
        // Set up event listeners
        this.bindEvents();
        
        // Wait for accordion to be ready
        this.waitForAccordion();
        
        // Load initial data
        await this.loadInitialData();
        
        console.log('✅ Patient Generator App initialized');
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
        });
        
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
                console.log('🎵 Accordion connected to app');
                // Wait a bit more for initial validation to complete
                setTimeout(() => {
                    this.updateGenerateButtonState();
                    console.log('🔄 Initial button state update after accordion connection');
                }, 50);
            } else {
                setTimeout(checkAccordion, 100);
            }
        };
        checkAccordion();
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
            
            console.log('📡 API connection established');
        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.showError(`Failed to connect to API: ${error.message}`);
        }
    }
    
    async loadNationalityData() {
        try {
            const nationalities = await this.apiClient.getNationalities();
            this.validNationalityCodes = new Set(nationalities.map(n => n.code));
            console.log(`📊 Loaded ${nationalities.length} nationality codes`);
        } catch (error) {
            console.warn('Could not load nationality data:', error.message);
            // Fallback to common NATO codes
            this.validNationalityCodes = new Set([
                'USA', 'GBR', 'CAN', 'FRA', 'DEU', 'ITA', 'ESP', 'NLD', 
                'BEL', 'PRT', 'NOR', 'DNK', 'ISL', 'LUX', 'GRC', 'TUR',
                'POL', 'CZE', 'HUN', 'SVK', 'SVN', 'EST', 'LVA', 'LTU',
                'BGR', 'ROU', 'HRV', 'ALB', 'MNE', 'MKD'
            ]);
        }
    }
    
    updateGenerateButtonState() {
        if (!this.accordion || !this.generateBtn) {
            console.log('🔴 Missing accordion or generate button');
            return;
        }
        
        const isValid = this.accordion.isAllValid();
        console.log('🎯 Button state update - isValid:', isValid, 'currentJobId:', this.currentJobId);
        
        this.generateBtn.disabled = !isValid || this.currentJobId !== null;
        
        if (!isValid) {
            this.generateBtn.textContent = 'Fix Configuration First';
            this.generateBtn.title = 'Please fix validation errors in the configuration sections';
        } else if (this.currentJobId) {
            this.generateBtn.textContent = 'Generating...';
            this.generateBtn.title = 'Generation in progress';
        } else {
            this.generateBtn.textContent = 'Generate Patients';
            this.generateBtn.title = 'Start patient generation with current configuration';
        }
    }
    
    async handleGenerate() {
        if (!this.accordion || !this.accordion.isAllValid()) {
            this.showError('Please fix all configuration errors before generating patients.');
            return;
        }
        
        try {
            // Disable UI
            this.currentJobId = 'pending';
            this.updateGenerateButtonState();
            
            // Show initial status
            this.showStatus();
            this.setStatusMessage('🚀 Starting patient generation...');
            
            // Build configuration from accordion
            const configuration = this.buildConfiguration();
            
            // Validate configuration
            this.validateConfiguration(configuration);
            
            // Start generation
            const response = await this.apiClient.generatePatients({
                configuration,
                output_formats: ['json', 'csv']
            });
            
            this.currentJobId = response.job_id;
            this.setStatusMessage(`✅ Generation started<br>Job ID: <code>${this.currentJobId}</code>`);
            
            // Start polling with fun progress messages
            await this.pollJobWithProgress();
            
        } catch (error) {
            console.error('Generation failed:', error);
            this.showError(`Generation failed: ${error.message}`);
            this.resetUI();
        }
    }
    
    buildConfiguration() {
        const [frontsJson, injuriesJson] = this.accordion.getAllContent();
        
        const fronts = JSON.parse(frontsJson);
        const injuries = JSON.parse(injuriesJson);
        
        return {
            name: `Patient Generation ${new Date().toLocaleString()}`,
            description: 'Generated from web interface',
            total_patients: injuries.total_patients || 1440,
            injury_distribution: injuries.injury_distribution,
            front_configs: fronts.front_configs,
            facility_configs: this.generateFacilityConfigs(fronts.front_configs)
            // Demographics are loaded automatically from the backend's demographics.json
        };
    }
    
    generateFacilityConfigs(frontConfigs) {
        // Auto-generate facility configs based on fronts
        return frontConfigs.map(front => ({
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
        for (const front of config.front_configs) {
            for (const natDist of front.nationality_distribution) {
                if (!this.validNationalityCodes.has(natDist.nationality_code)) {
                    console.warn(`Unknown nationality code: ${natDist.nationality_code}`);
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
        const percentage = job.progress || 0;
        
        if (this.progressBar) {
            this.progressBar.style.width = `${percentage}%`;
        }
        
        if (this.progressContainer) {
            this.progressContainer.style.display = 'block';
        }
        
        let phase = 'Processing...';
        if (percentage < 15) phase = 'Validating configurations...';
        else if (percentage < 30) phase = 'Initializing patient generator...';
        else if (percentage < 85) phase = `Generating patients... (${percentage}%)`;
        else if (percentage < 95) phase = 'Finalizing medical records...';
        else phase = 'Creating downloadable archives...';
        
        this.setStatusMessage(`
            <strong>Status:</strong> ${job.status}<br>
            <strong>Phase:</strong> ${phase}<br>
            <strong>Progress:</strong> ${percentage}%
        `);
    }
    
    handleJobComplete(job) {
        this.setStatusMessage(`
            <div class="success">
                ✅ <strong>Generation completed successfully!</strong><br>
                📊 Total patients generated: <strong>${job.result?.total_patients || 'Unknown'}</strong><br>
                ⏱️ Generation time: <strong>${this.formatDuration(job.duration)}</strong>
            </div>
        `);
        
        this.showDownloadOptions(job);
        this.resetUI();
    }
    
    showDownloadOptions(job) {
        if (!this.downloadContainer) return;
        
        const fileSize = job.result?.file_size ? this.formatFileSize(job.result.file_size) : 'Unknown size';
        
        this.downloadContainer.innerHTML = `
            <div class="download-section">
                <h4>📁 Download Results</h4>
                <p>Your generated patient data is ready for download:</p>
                <button onclick="app.downloadResults('${this.currentJobId}')" class="download-link">
                    📥 Download Patient Data (ZIP)
                </button>
                <p class="download-info">
                    <small>
                        💾 File size: ${fileSize}<br>
                        📂 Job ID: ${this.currentJobId}
                    </small>
                </p>
            </div>
        `;
    }
    
    async downloadResults(jobId) {
        try {
            this.setStatusMessage('📥 Preparing download...');
            
            const blob = await this.apiClient.downloadJobResults(jobId);
            
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
    
    showStatus() {
        if (this.statusBox) {
            this.statusBox.classList.add('show');
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
        this.updateGenerateButtonState();
        this.stopProgressMessages();
    }
    
    formatDuration(seconds) {
        if (!seconds) return 'Unknown';
        
        if (seconds < 60) return `${seconds}s`;
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
        
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

console.log('🔧 Patient Generator App loaded');