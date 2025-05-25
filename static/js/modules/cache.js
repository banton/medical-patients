/**
 * Client-side Cache Module
 * Handles browser-based caching with localStorage
 */

export class ClientCache {
    constructor() {
        this.storagePrefix = 'patientGen_';
        this.defaultTTL = 3600000; // 1 hour in milliseconds
    }

    /**
     * Set item in cache with TTL
     * @param {string} key - Cache key
     * @param {*} value - Value to cache
     * @param {number} ttl - Time to live in milliseconds
     */
    set(key, value, ttl = this.defaultTTL) {
        try {
            const item = {
                value: value,
                expires: Date.now() + ttl,
                cached: Date.now()
            };
            
            localStorage.setItem(this.storagePrefix + key, JSON.stringify(item));
            return true;
        } catch (error) {
            console.warn('Failed to cache item:', error);
            return false;
        }
    }

    /**
     * Get item from cache
     * @param {string} key - Cache key
     * @returns {*} Cached value or null
     */
    get(key) {
        try {
            const itemStr = localStorage.getItem(this.storagePrefix + key);
            if (!itemStr) return null;
            
            const item = JSON.parse(itemStr);
            
            // Check if expired
            if (Date.now() > item.expires) {
                this.delete(key);
                return null;
            }
            
            return item.value;
        } catch (error) {
            console.warn('Failed to get cached item:', error);
            return null;
        }
    }

    /**
     * Delete item from cache
     * @param {string} key - Cache key
     */
    delete(key) {
        try {
            localStorage.removeItem(this.storagePrefix + key);
            return true;
        } catch (error) {
            console.warn('Failed to delete cached item:', error);
            return false;
        }
    }

    /**
     * Clear all cached items
     */
    clear() {
        try {
            const keys = Object.keys(localStorage);
            keys.forEach(key => {
                if (key.startsWith(this.storagePrefix)) {
                    localStorage.removeItem(key);
                }
            });
            return true;
        } catch (error) {
            console.warn('Failed to clear cache:', error);
            return false;
        }
    }

    /**
     * Get cache statistics
     * @returns {Object} Cache statistics
     */
    getStats() {
        const stats = {
            totalItems: 0,
            totalSize: 0,
            items: []
        };
        
        try {
            const keys = Object.keys(localStorage);
            keys.forEach(key => {
                if (key.startsWith(this.storagePrefix)) {
                    const itemStr = localStorage.getItem(key);
                    const item = JSON.parse(itemStr);
                    
                    stats.totalItems++;
                    stats.totalSize += itemStr.length;
                    
                    stats.items.push({
                        key: key.replace(this.storagePrefix, ''),
                        size: itemStr.length,
                        cached: new Date(item.cached),
                        expires: new Date(item.expires),
                        isExpired: Date.now() > item.expires
                    });
                }
            });
        } catch (error) {
            console.warn('Failed to get cache stats:', error);
        }
        
        return stats;
    }

    /**
     * Check if localStorage is available
     * @returns {boolean} Whether localStorage is available
     */
    isAvailable() {
        try {
            const testKey = this.storagePrefix + 'test';
            localStorage.setItem(testKey, 'test');
            localStorage.removeItem(testKey);
            return true;
        } catch (error) {
            return false;
        }
    }

    /**
     * Estimate available storage space
     * @returns {Object} Storage estimate
     */
    async getStorageEstimate() {
        if ('storage' in navigator && 'estimate' in navigator.storage) {
            try {
                const estimate = await navigator.storage.estimate();
                return {
                    usage: estimate.usage || 0,
                    quota: estimate.quota || 0,
                    percent: ((estimate.usage || 0) / (estimate.quota || 1)) * 100
                };
            } catch (error) {
                console.warn('Failed to estimate storage:', error);
            }
        }
        
        return {
            usage: 0,
            quota: 0,
            percent: 0
        };
    }
}

// Export singleton instance
export const clientCache = new ClientCache();