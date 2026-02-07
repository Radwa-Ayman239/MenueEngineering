
const { apiService } = require('./src/lib/api');

// Mock localStorage for node environment
global.window = {};
global.localStorage = {
    getItem: () => null,
    setItem: () => {},
    removeItem: () => {},
};

// Mock fetch
global.fetch = async (url, options) => {
    console.log(`Fetching ${url}...`);
    try {
        const response = await import('node-fetch').then(({default: fetch}) => fetch(url, options));
        const text = await response.text();
        console.log('Status:', response.status);
        console.log('Response:', text);
        return {
            ok: response.ok,
            status: response.status,
            text: async () => text,
            json: async () => JSON.parse(text)
        };
    } catch (e) {
        console.error("Fetch error:", e);
        throw e;
    }
};

(async () => {
    try {
        console.log("Testing Sales Suggestions API...");
        // We can't use the ApiService class easily in raw JS without compilation if it's TS.
        // So I'll just use fetch directly.
        const response = await fetch('http://localhost:8000/api/menu/ai/sales-suggestions/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
    } catch (error) {
        console.error("Test failed:", error);
    }
})();
