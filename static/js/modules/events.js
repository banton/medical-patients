/**
 * Event Bus Module - Handles inter-module communication
 */
export class EventBus {
    constructor() {
        this.events = new Map();
    }

    /**
     * Subscribe to an event
     */
    on(event, callback) {
        if (!this.events.has(event)) {
            this.events.set(event, []);
        }
        this.events.get(event).push(callback);
        
        // Return unsubscribe function
        return () => this.off(event, callback);
    }

    /**
     * Unsubscribe from an event
     */
    off(event, callback) {
        if (!this.events.has(event)) return;
        
        const callbacks = this.events.get(event);
        const index = callbacks.indexOf(callback);
        if (index > -1) {
            callbacks.splice(index, 1);
        }
        
        if (callbacks.length === 0) {
            this.events.delete(event);
        }
    }

    /**
     * Emit an event
     */
    emit(event, data) {
        if (!this.events.has(event)) return;
        
        const callbacks = this.events.get(event);
        callbacks.forEach(callback => {
            try {
                callback(data);
            } catch (error) {
                console.error(`Error in event handler for ${event}:`, error);
            }
        });
    }

    /**
     * Subscribe to an event once
     */
    once(event, callback) {
        const wrapper = (data) => {
            callback(data);
            this.off(event, wrapper);
        };
        return this.on(event, wrapper);
    }

    /**
     * Clear all event handlers
     */
    clear() {
        this.events.clear();
    }

    /**
     * Get all registered events
     */
    getEvents() {
        return Array.from(this.events.keys());
    }
}

// Export singleton instance
export const eventBus = new EventBus();

// Define common events
export const Events = {
    // Front configuration events
    FRONT_ADDED: 'front:added',
    FRONT_REMOVED: 'front:removed',
    FRONT_UPDATED: 'front:updated',
    
    // Job events
    JOB_CREATED: 'job:created',
    JOB_UPDATED: 'job:updated',
    JOB_COMPLETED: 'job:completed',
    JOB_FAILED: 'job:failed',
    
    // Form events
    FORM_SUBMITTED: 'form:submitted',
    FORM_VALIDATED: 'form:validated',
    FORM_ERROR: 'form:error',
    
    // API events
    API_REQUEST_START: 'api:request:start',
    API_REQUEST_SUCCESS: 'api:request:success',
    API_REQUEST_ERROR: 'api:request:error',
    
    // UI events
    UI_LOADING_START: 'ui:loading:start',
    UI_LOADING_END: 'ui:loading:end',
    UI_ERROR_SHOW: 'ui:error:show',
    UI_ERROR_HIDE: 'ui:error:hide',
    
    // Persistence events
    CONFIG_SAVED: 'config:saved',
    CONFIG_LOADED: 'config:loaded',
    CONFIG_AUTOSAVED: 'config:autosaved',
    
    // Validation events
    VALIDATION_ERROR: 'validation:error',
    VALIDATION_SUCCESS: 'validation:success',
    
    // Generation events
    GENERATION_STARTED: 'generation:started',
    GENERATION_COMPLETED: 'generation:completed',
    
    // Nationality events
    NATIONALITY_ADDED: 'nationality:added',
    NATIONALITY_REMOVED: 'nationality:removed',
    NATIONALITY_UPDATED: 'nationality:updated'
};