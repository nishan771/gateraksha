/**
 * GATE RAKSHA — API Client
 */

const ApiClient = {
    async getGates() {
        try {
            const response = await fetch('/api/gates');
            return await response.json();
        } catch (error) {
            console.error('Failed to fetch gates:', error);
            return [];
        }
    },

    async getLiveStatus() {
        try {
            const response = await fetch('/api/live-status');
            return await response.json();
        } catch (error) {
            console.error('Failed to fetch live status:', error);
            return {
                is_live_available: false,
                error: 'Network or API request failed.',
                disclaimer: 'Estimated gate status based on live train data',
                gates: []
            };
        }
    },

    async calculateRouteStatus(polylinePoints) {
        try {
            const response = await fetch('/api/route-status', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    polyline_points: polylinePoints
                })
            });
            return await response.json();
        } catch (error) {
            console.error('Failed to calculate route status:', error);
            return {
                is_live_available: false,
                error: 'Route calculation request failed.',
                disclaimer: 'Estimated gate status based on live train data',
                gates: []
            };
        }
    }
};
