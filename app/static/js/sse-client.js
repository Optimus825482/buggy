/**
 * SSE (Server-Sent Events) Client
 * Simple and reliable real-time notifications
 */

class SSEClient {
    constructor() {
        this.eventSource = null;
        this.reconnectDelay = 3000;
        this.maxReconnectDelay = 30000;
        this.reconnectAttempts = 0;
        this.handlers = {};
    }

    /**
     * Connect to SSE stream
     */
    connect(url = '/sse/stream') {
        if (this.eventSource) {
            console.log('[SSE] Already connected');
            return;
        }

        console.log('[SSE] Connecting to:', url);
        
        try {
            this.eventSource = new EventSource(url);
            
            // Connection opened
            this.eventSource.onopen = () => {
                console.log('✅ [SSE] Connected');
                this.reconnectAttempts = 0;
                this.reconnectDelay = 3000;
                this.trigger('connected', {});
            };
            
            // Default message handler
            this.eventSource.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log('[SSE] Message received:', data);
                    
                    if (data.event) {
                        this.trigger(data.event, data.data || data);
                    }
                } catch (error) {
                    console.error('[SSE] Error parsing message:', error);
                }
            };
            
            // Custom event listeners
            this.eventSource.addEventListener('new_request', (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log('🎉 [SSE] NEW REQUEST:', data);
                    this.trigger('new_request', data);
                } catch (error) {
                    console.error('[SSE] Error parsing new_request:', error);
                }
            });
            
            this.eventSource.addEventListener('request_taken', (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log('[SSE] Request taken:', data);
                    this.trigger('request_taken', data);
                } catch (error) {
                    console.error('[SSE] Error parsing request_taken:', error);
                }
            });
            
            // Error handler
            this.eventSource.onerror = (error) => {
                console.error('❌ [SSE] Connection error:', error);
                this.trigger('error', error);
                
                // Close and reconnect
                this.disconnect();
                this.scheduleReconnect();
            };
            
        } catch (error) {
            console.error('[SSE] Failed to create EventSource:', error);
            this.scheduleReconnect();
        }
    }

    /**
     * Disconnect from SSE stream
     */
    disconnect() {
        if (this.eventSource) {
            console.log('[SSE] Disconnecting...');
            this.eventSource.close();
            this.eventSource = null;
        }
    }

    /**
     * Schedule reconnection with exponential backoff
     */
    scheduleReconnect() {
        this.reconnectAttempts++;
        const delay = Math.min(
            this.reconnectDelay * Math.pow(1.5, this.reconnectAttempts - 1),
            this.maxReconnectDelay
        );
        
        console.log(`[SSE] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})...`);
        
        setTimeout(() => {
            this.connect();
        }, delay);
    }

    /**
     * Register event handler
     */
    on(event, handler) {
        if (!this.handlers[event]) {
            this.handlers[event] = [];
        }
        this.handlers[event].push(handler);
    }

    /**
     * Trigger event handlers
     */
    trigger(event, data) {
        if (this.handlers[event]) {
            this.handlers[event].forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`[SSE] Error in ${event} handler:`, error);
                }
            });
        }
    }

    /**
     * Check if connected
     */
    isConnected() {
        return this.eventSource && this.eventSource.readyState === EventSource.OPEN;
    }
}

// Create global instance
const sseClient = new SSEClient();

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = sseClient;
}

console.log('[SSE] Client loaded');
