// Global functions for UI interactions
// These functions are called from onclick handlers in the HTML

// Job management functions
window.cancelJob = async function(jobId) {
    try {
        const response = await fetch(`/api/jobs/${jobId}/cancel`, {
            method: 'POST',
            headers: {
                'X-API-Key': 'your_secret_api_key_here'
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to cancel job');
        }
        
        // Dispatch event to update UI
        document.dispatchEvent(new CustomEvent('job-cancel', { detail: { jobId } }));
    } catch (error) {
        console.error('Error canceling job:', error);
        alert('Failed to cancel job: ' + error.message);
    }
};

window.downloadJob = async function(jobId) {
    try {
        const url = `/api/downloads/job/${jobId}`;
        window.location.href = url;
        
        // Dispatch event
        document.dispatchEvent(new CustomEvent('job-download', { detail: { jobId } }));
    } catch (error) {
        console.error('Error downloading job:', error);
        alert('Failed to download job results: ' + error.message);
    }
};

window.viewJob = function(jobId) {
    // Open job details in a new tab or modal
    const url = `/static/visualizations.html?job=${jobId}`;
    window.open(url, '_blank');
};

window.deleteJob = async function(jobId) {
    if (!confirm('Are you sure you want to delete this job? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/jobs/${jobId}`, {
            method: 'DELETE',
            headers: {
                'X-API-Key': 'your_secret_api_key_here'
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete job');
        }
        
        // Remove job card from UI
        const jobCard = document.getElementById(`job-${jobId}`);
        if (jobCard) {
            jobCard.remove();
        }
        
        alert('Job deleted successfully');
    } catch (error) {
        console.error('Error deleting job:', error);
        alert('Failed to delete job: ' + error.message);
    }
};

// Utility functions
window.formatFileSize = function(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

window.formatDuration = function(milliseconds) {
    const seconds = Math.floor(milliseconds / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
        return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
    } else if (minutes > 0) {
        return `${minutes}m ${seconds % 60}s`;
    } else {
        return `${seconds}s`;
    }
};

window.copyToClipboard = async function(text) {
    try {
        await navigator.clipboard.writeText(text);
        // Show temporary success message
        const toast = document.createElement('div');
        toast.className = 'alert alert-success position-fixed top-0 start-50 translate-middle-x mt-3';
        toast.style.zIndex = '9999';
        toast.textContent = 'Copied to clipboard!';
        document.body.appendChild(toast);
        
        setTimeout(() => toast.remove(), 2000);
    } catch (error) {
        console.error('Failed to copy to clipboard:', error);
    }
};

// Theme management
window.toggleTheme = function() {
    const currentTheme = document.documentElement.getAttribute('data-bs-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-bs-theme', newTheme);
    localStorage.setItem('theme', newTheme);
};

// Initialize theme on load
document.addEventListener('DOMContentLoaded', function() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-bs-theme', savedTheme);
});

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl+Enter or Cmd+Enter to generate
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        const generateBtn = document.getElementById('generateBtn');
        if (generateBtn && !generateBtn.disabled) {
            generateBtn.click();
        }
    }
    
    // Escape to close modals
    if (e.key === 'Escape') {
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            const modalInstance = bootstrap.Modal.getInstance(modal);
            if (modalInstance) {
                modalInstance.hide();
            }
        });
    }
});

// Auto-save configuration to localStorage
let autoSaveTimeout;
document.addEventListener('config-changed', function() {
    clearTimeout(autoSaveTimeout);
    autoSaveTimeout = setTimeout(() => {
        try {
            // Get current configuration from the app
            if (window.app && window.app.getCurrentConfiguration) {
                const config = window.app.getCurrentConfiguration();
                localStorage.setItem('autosave-config', JSON.stringify(config));
                console.log('Configuration auto-saved');
            }
        } catch (error) {
            console.warn('Failed to auto-save configuration:', error);
        }
    }, 1000);
});

// Load auto-saved configuration on startup
window.loadAutoSavedConfiguration = function() {
    try {
        const saved = localStorage.getItem('autosave-config');
        if (saved) {
            return JSON.parse(saved);
        }
    } catch (error) {
        console.warn('Failed to load auto-saved configuration:', error);
    }
    return null;
};

// Export/Import configuration
window.exportConfiguration = function() {
    try {
        if (window.app && window.app.getCurrentConfiguration) {
            const config = window.app.getCurrentConfiguration();
            const exportData = {
                configuration: config,
                exported_at: new Date().toISOString(),
                version: '1.0'
            };
            
            const blob = new Blob([JSON.stringify(exportData, null, 2)], {
                type: 'application/json'
            });
            
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `patient-generator-config-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }
    } catch (error) {
        console.error('Failed to export configuration:', error);
        alert('Failed to export configuration: ' + error.message);
    }
};

window.importConfiguration = function() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    
    input.onchange = function(e) {
        const file = e.target.files[0];
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = function(e) {
            try {
                const data = JSON.parse(e.target.result);
                
                if (data.configuration && window.app && window.app.loadConfiguration) {
                    window.app.loadConfiguration(data.configuration);
                    alert('Configuration imported successfully');
                } else {
                    throw new Error('Invalid configuration file format');
                }
            } catch (error) {
                console.error('Failed to import configuration:', error);
                alert('Failed to import configuration: ' + error.message);
            }
        };
        reader.readAsText(file);
    };
    
    input.click();
};

// Print support
window.printConfiguration = function() {
    window.print();
};

// Accessibility helpers
window.announceToScreenReader = function(message) {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'polite');
    announcement.className = 'visually-hidden';
    announcement.textContent = message;
    
    document.body.appendChild(announcement);
    setTimeout(() => announcement.remove(), 1000);
};

// Focus management for modals
document.addEventListener('shown.bs.modal', function(e) {
    const modal = e.target;
    const focusableElements = modal.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    if (focusableElements.length > 0) {
        focusableElements[0].focus();
    }
});