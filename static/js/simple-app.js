/**
 * Simple Military Patient Generator Application
 */

const API_URL = '';  // Use relative URLs for same-origin requests
const API_KEY = 'your_secret_api_key_here';

// Default configuration based on JSON files
const DEFAULT_CONFIG = {
    name: "Patient Generation",
    description: "Generated using JSON configuration files",
    total_patients: 1440,  // From injuries.json
    injury_distribution: {
        "Disease": 0.52,
        "Non-Battle Injury": 0.33,
        "Battle Injury": 0.15
    },
    front_configs: [
        {
            id: "poland",
            name: "Poland",
            casualty_rate: 0.6,
            nationality_distribution: [
                { nationality_code: "POL", percentage: 50.0 },
                { nationality_code: "LTU", percentage: 25.0 },
                { nationality_code: "NLD", percentage: 20.0 },
                { nationality_code: "ESP", percentage: 5.0 }
            ]
        },
        {
            id: "estonia",
            name: "Estonia",
            casualty_rate: 0.3,
            nationality_distribution: [
                { nationality_code: "EST", percentage: 50.0 },
                { nationality_code: "GBR", percentage: 50.0 }
            ]
        },
        {
            id: "finland",
            name: "Finland",
            casualty_rate: 0.1,
            nationality_distribution: [
                { nationality_code: "FIN", percentage: 50.0 },
                { nationality_code: "USA", percentage: 50.0 }
            ]
        }
    ],
    facility_configs: [
        {
            id: "role2_poland",
            name: "Role 2 Poland",
            capacity: 500,
            role: "Role 2",
            nationality: "POL",
            front_id: "poland",
            kia_rate: 0.05,
            rtd_rate: 0.85
        },
        {
            id: "role2_estonia",
            name: "Role 2 Estonia",
            capacity: 300,
            role: "Role 2",
            nationality: "EST",
            front_id: "estonia",
            kia_rate: 0.05,
            rtd_rate: 0.85
        },
        {
            id: "role2_finland",
            name: "Role 2 Finland",
            capacity: 100,
            role: "Role 2",
            nationality: "FIN",
            front_id: "finland",
            kia_rate: 0.05,
            rtd_rate: 0.85
        }
    ]
};

// DOM elements
let generateBtn;
let statusBox;
let statusMessage;
let progressBar;
let progressContainer;
let downloadContainer;

// Current job ID
let currentJobId = null;
let pollInterval = null;

/**
 * Initialize the application
 */
function init() {
    // Get DOM elements
    generateBtn = document.getElementById('generateBtn');
    statusBox = document.getElementById('statusBox');
    statusMessage = document.getElementById('statusMessage');
    progressBar = document.getElementById('progressBar');
    progressContainer = document.getElementById('progressContainer');
    downloadContainer = document.getElementById('downloadContainer');

    // Set up event listeners
    generateBtn.addEventListener('click', handleGenerate);
}

/**
 * Handle generate button click
 */
async function handleGenerate() {
    try {
        // Disable button
        generateBtn.disabled = true;
        generateBtn.textContent = 'Generating...';

        // Clear previous status
        statusBox.classList.add('show');
        statusMessage.innerHTML = '<p>Starting patient generation...</p>';
        progressContainer.style.display = 'none';
        downloadContainer.innerHTML = '';

        // Make API request
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': API_KEY
            },
            body: JSON.stringify({
                configuration: DEFAULT_CONFIG,
                output_formats: ['json']
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to start generation');
        }

        const data = await response.json();
        currentJobId = data.job_id;
        
        statusMessage.innerHTML = `<p class="success">✓ Generation started</p><p>Job ID: ${currentJobId}</p>`;
        
        // Start polling for status
        pollJobStatus();

    } catch (error) {
        statusMessage.innerHTML = `<p class="error">✗ Error: ${error.message}</p>`;
        generateBtn.disabled = false;
        generateBtn.textContent = 'Generate Patients';
    }
}

/**
 * Poll for job status
 */
function pollJobStatus() {
    pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/jobs/${currentJobId}`, {
                headers: {
                    'X-API-Key': API_KEY
                }
            });

            if (!response.ok) {
                throw new Error('Failed to get job status');
            }

            const data = await response.json();
            updateJobStatus(data);

            // Stop polling if job is complete
            if (data.status === 'completed' || data.status === 'failed') {
                clearInterval(pollInterval);
                generateBtn.disabled = false;
                generateBtn.textContent = 'Generate Patients';
            }

        } catch (error) {
            statusMessage.innerHTML += `<p class="error">✗ Error checking status: ${error.message}</p>`;
            clearInterval(pollInterval);
            generateBtn.disabled = false;
            generateBtn.textContent = 'Generate Patients';
        }
    }, 1000); // Poll every second
}

/**
 * Update job status display
 */
function updateJobStatus(jobData) {
    if (jobData.status === 'running') {
        progressContainer.style.display = 'block';
        progressBar.style.width = `${jobData.progress}%`;
        statusMessage.innerHTML = `
            <p>Status: <strong>${jobData.status}</strong></p>
            <p>${jobData.message || 'Processing...'}</p>
            <p>Progress: ${jobData.progress}%</p>
        `;
    } else if (jobData.status === 'completed') {
        progressContainer.style.display = 'block';
        progressBar.style.width = '100%';
        statusMessage.innerHTML = `
            <p class="success">✓ Generation completed successfully!</p>
            <p>Total patients generated: ${jobData.result?.total_patients || 'Unknown'}</p>
        `;
        
        // Show download link
        downloadContainer.innerHTML = `
            <h4>Download Results</h4>
            <p>Your generated patient data is ready for download:</p>
            <a href="/api/download/${currentJobId}" class="download-link" download>
                Download Patient Data (ZIP)
            </a>
            <p><small>Files are saved in: output/job_${currentJobId}/</small></p>
        `;
    } else if (jobData.status === 'failed') {
        statusMessage.innerHTML = `
            <p class="error">✗ Generation failed</p>
            <p>Error: ${jobData.error || 'Unknown error'}</p>
        `;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', init);