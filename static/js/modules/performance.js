/**
 * Performance Monitoring Module
 * Tracks and reports application performance metrics
 */

export class PerformanceMonitor {
    constructor() {
        this.metrics = new Map();
        this.enabled = true;
    }

    /**
     * Start timing an operation
     * @param {string} name - Operation name
     */
    startTimer(name) {
        if (!this.enabled) return;
        
        this.metrics.set(name, {
            start: performance.now(),
            end: null,
            duration: null
        });
    }

    /**
     * End timing an operation
     * @param {string} name - Operation name
     * @returns {number} Duration in milliseconds
     */
    endTimer(name) {
        if (!this.enabled) return 0;
        
        const metric = this.metrics.get(name);
        if (!metric || metric.end !== null) return 0;
        
        metric.end = performance.now();
        metric.duration = metric.end - metric.start;
        
        console.debug(`[Performance] ${name}: ${metric.duration.toFixed(2)}ms`);
        
        return metric.duration;
    }

    /**
     * Measure async operation
     * @param {string} name - Operation name
     * @param {Function} asyncFn - Async function to measure
     * @returns {Promise} Result of the async function
     */
    async measureAsync(name, asyncFn) {
        this.startTimer(name);
        try {
            const result = await asyncFn();
            this.endTimer(name);
            return result;
        } catch (error) {
            this.endTimer(name);
            throw error;
        }
    }

    /**
     * Get all metrics
     * @returns {Object} All performance metrics
     */
    getMetrics() {
        const result = {};
        
        this.metrics.forEach((value, key) => {
            if (value.duration !== null) {
                result[key] = {
                    duration: value.duration,
                    timestamp: value.start
                };
            }
        });
        
        return result;
    }

    /**
     * Get memory usage information
     * @returns {Object} Memory usage stats
     */
    getMemoryUsage() {
        if (!performance.memory) {
            return {
                available: false,
                message: 'Memory API not available'
            };
        }
        
        return {
            available: true,
            usedJSHeapSize: performance.memory.usedJSHeapSize,
            totalJSHeapSize: performance.memory.totalJSHeapSize,
            jsHeapSizeLimit: performance.memory.jsHeapSizeLimit,
            percentUsed: (performance.memory.usedJSHeapSize / performance.memory.jsHeapSizeLimit) * 100
        };
    }

    /**
     * Monitor long tasks
     * @param {number} threshold - Threshold in milliseconds
     */
    monitorLongTasks(threshold = 50) {
        if (!('PerformanceObserver' in window)) {
            console.warn('PerformanceObserver not supported');
            return;
        }
        
        try {
            const observer = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    if (entry.duration > threshold) {
                        console.warn(`[Performance] Long task detected: ${entry.duration.toFixed(2)}ms`);
                    }
                }
            });
            
            observer.observe({ entryTypes: ['longtask'] });
        } catch (error) {
            console.warn('Failed to setup long task monitoring:', error);
        }
    }

    /**
     * Get page load metrics
     * @returns {Object} Page load performance metrics
     */
    getPageLoadMetrics() {
        const navigation = performance.getEntriesByType('navigation')[0];
        
        if (!navigation) {
            return { available: false };
        }
        
        return {
            available: true,
            domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
            domComplete: navigation.domComplete - navigation.domInteractive,
            loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
            firstPaint: this.getFirstPaintTime(),
            totalLoadTime: navigation.loadEventEnd - navigation.fetchStart
        };
    }

    /**
     * Get first paint time
     * @returns {number|null} First paint time in milliseconds
     */
    getFirstPaintTime() {
        const paintEntries = performance.getEntriesByType('paint');
        const firstPaint = paintEntries.find(entry => entry.name === 'first-paint');
        
        return firstPaint ? firstPaint.startTime : null;
    }

    /**
     * Log performance summary
     */
    logSummary() {
        console.group('[Performance Summary]');
        
        // Log metrics
        const metrics = this.getMetrics();
        console.table(metrics);
        
        // Log memory usage
        const memory = this.getMemoryUsage();
        if (memory.available) {
            console.log('Memory Usage:', {
                used: `${(memory.usedJSHeapSize / 1024 / 1024).toFixed(2)} MB`,
                total: `${(memory.totalJSHeapSize / 1024 / 1024).toFixed(2)} MB`,
                limit: `${(memory.jsHeapSizeLimit / 1024 / 1024).toFixed(2)} MB`,
                percentUsed: `${memory.percentUsed.toFixed(2)}%`
            });
        }
        
        // Log page load metrics
        const pageLoad = this.getPageLoadMetrics();
        if (pageLoad.available) {
            console.log('Page Load:', pageLoad);
        }
        
        console.groupEnd();
    }

    /**
     * Clear all metrics
     */
    clear() {
        this.metrics.clear();
    }

    /**
     * Enable/disable monitoring
     * @param {boolean} enabled - Whether to enable monitoring
     */
    setEnabled(enabled) {
        this.enabled = enabled;
    }
}

// Export singleton instance
export const performanceMonitor = new PerformanceMonitor();

// Auto-start long task monitoring
if (typeof window !== 'undefined') {
    performanceMonitor.monitorLongTasks();
}