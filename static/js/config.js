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

        // Initialize API key from backend
        this._initializeApiKey();

        console.log(`🔧 Frontend configured for ${this.environment} environment`);
    }

    async _initializeApiKey() {
        // Only fetch API key from backend in production
        if (this.environment === 'production') {
            try {
                const response = await fetch('/api/v1/config/frontend');
                if (response.ok) {
                    const backendConfig = await response.json();
                    this.config.apiKey = backendConfig.apiKey;
                    console.log('🔑 API key fetched from backend');

                    // Notify that config is ready
                    if (window.dispatchEvent) {
                        window.dispatchEvent(new CustomEvent('configReady'));
                    }
                } else {
                    console.warn('Failed to fetch API key from backend, using fallback');
                }
            } catch (error) {
                console.warn('Error fetching API key from backend:', error);
            }
        } else {
            // For non-production, immediately mark as ready
            setTimeout(() => {
                if (window.dispatchEvent) {
                    window.dispatchEvent(new CustomEvent('configReady'));
                }
            }, 100);
        }
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
                apiKey: 'dev_secret_key_27e9010dd17a442a1cda3a0490a95611',
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
                apiKey: 'fetching_from_backend', // Will be replaced by _initializeApiKey
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
