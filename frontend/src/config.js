/**
 * Configuration for the Political Network 3D Visualization
 */

// Set API URL based on environment
window.API_URL = window.API_URL || 'http://localhost:8080/api';

// Other configuration options
window.APP_CONFIG = {
    API_URL: window.API_URL,
    NETWORK_LIMITS: {
        politicians: 100,
        parties: 30,
        companies: 100,
        sanctions: 100,
        connections: 2000
    },
    VISUALIZATION: {
        defaultForceStrength: 30,
        defaultLinkDistance: 100,
        nodeColors: {
            politician: '#ff6b6b',
            party: '#4ecdc4',
            company: '#ffe66d',
            sanction: '#ff8b94'
        }
    }
};