// API Configuration
// This file should be generated or replaced during deployment
// to inject the correct API key and other settings

window.API_CONFIG = {
    // In production, this should be injected during build/deployment
    // For development, it uses the default value
    API_KEY: 'your_secret_api_key_here',
    API_BASE_URL: window.location.origin,
    
    // Helper function to get headers with API key
    getHeaders: function() {
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-API-KEY': this.API_KEY
        };
    }
};