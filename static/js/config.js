/**
 * Frontend Configuration
 * Environment-specific settings for the Medical Patients Generator frontend
 */

/* eslint no-console: "off" */

class Config {
    constructor() {
        // Auto-detect environment based on hostname
        this.environment = this.detectEnvironment();
        
        // Environment-specific configuration
        this.config = this.getEnvironmentConfig();
        
        console.log(`🔧 Frontend configured for ${this.environment} environment`);
    }
    
    detectEnvironment() {
        const hostname = window.location.hostname;
        
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            return 'local';
        } else if (hostname.includes('staging') || hostname.includes('z9rms')) {
            return 'staging';
        } else if (hostname === 'milmed.tech') {
            return 'production';
        } else {
            console.warn(`Unknown hostname: ${hostname}, defaulting to local config`);
            return 'local';
        }
    }
    
    getEnvironmentConfig() {
        const configs = {
            local: {
                apiKey: 'your_secret_api_key_here',
                apiBaseUrl: '',
                debug: true,
                environment: 'local'
            },
            staging: {
                apiKey: 'staging_key_placeholder', // Set via deployment
                apiBaseUrl: '',
                debug: false,
                environment: 'staging'
            },
            production: {
                apiKey: 'W3NVoSISp8V1ljArEAhQxB6KIIFoXKweuftWacIuislueuuP',
                apiBaseUrl: '',
                debug: false,
                environment: 'production'
            }
        };
        
        return configs[this.environment] || configs.local;
    }
    
    // Getter methods for easy access
    get apiKey() {
        return this.config.apiKey;
    }
    
    get apiBaseUrl() {
        return this.config.apiBaseUrl;
    }
    
    get debug() {
        return this.config.debug;
    }
    
    get isProduction() {
        return this.environment === 'production';
    }
    
    get isStaging() {
        return this.environment === 'staging';
    }
    
    get isLocal() {
        return this.environment === 'local';
    }
}

// Create global config instance
const config = new Config();

// Export for modules and global use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { Config, config };
}

if (typeof window !== 'undefined') {
    window.Config = Config;
    window.config = config;
}

console.log('🔧 Frontend configuration loaded');