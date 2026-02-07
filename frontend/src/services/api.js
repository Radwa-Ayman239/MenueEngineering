// API Service for Menu Engineering System
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/menu';

class ApiService {
  constructor() {
    this.token = localStorage.getItem('authToken');
  }

  setToken(token) {
    this.token = token;
    if (token) {
      localStorage.setItem('authToken', token);
    } else {
      localStorage.removeItem('authToken');
    }
  }

  getHeaders(includeAuth = true) {
    const headers = {
      'Content-Type': 'application/json',
    };
    if (includeAuth && this.token) {
      headers['Authorization'] = `Token ${this.token}`;
    }
    return headers;
  }

  async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const config = {
      ...options,
      headers: this.getHeaders(options.auth !== false),
    };

    try {
      const response = await fetch(url, config);
      if (!response.ok) {
        const error = await response.json().catch(() => ({ error: 'Request failed' }));
        throw new Error(error.error || `HTTP ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }

  // Public Menu APIs
  async getPublicMenu() {
    return this.request('/public/', { auth: false });
  }

  async getMenuSections() {
    return this.request('/sections/', { auth: false });
  }

  async getMenuItems(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request(`/items/${query ? '?' + query : ''}`, { auth: false });
  }

  async getMenuItem(id) {
    return this.request(`/items/${id}/`, { auth: false });
  }

  // Recommendation APIs (Public)
  async getRecommendations(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request(`/recommendations/${query ? '?' + query : ''}`, { auth: false });
  }

  async getCartRecommendations(itemIds, strategy = 'balanced') {
    return this.request('/recommendations/for-cart/', {
      method: 'POST',
      body: JSON.stringify({ item_ids: itemIds, strategy, limit: 5 }),
      auth: false,
    });
  }

  async getFrequentlyBoughtTogether(itemId, limit = 3) {
    return this.request(`/items/${itemId}/frequently-together/?limit=${limit}`, { auth: false });
  }

  // Manager APIs (Authenticated)
  async analyzeMenuItem(itemId) {
    return this.request(`/items/${itemId}/analyze/`, { method: 'POST' });
  }

  async bulkAnalyzeItems() {
    return this.request('/items/bulk_analyze/', { method: 'POST' });
  }

  async getItemStats() {
    return this.request('/items/stats/');
  }

  async getSalesSuggestions(itemId) {
    return this.request('/ai/sales-suggestions/', {
      method: 'POST',
      body: JSON.stringify({ item_id: itemId }),
    });
  }

  async getMenuAnalysis() {
    return this.request('/ai/menu-analysis/', { method: 'POST' });
  }

  async getOwnerReport(period = 'weekly') {
    return this.request('/ai/owner-report/', {
      method: 'POST',
      body: JSON.stringify({ period }),
    });
  }

  async createMenuItem(data) {
    return this.request('/items/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateMenuItem(id, data) {
    return this.request(`/items/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  // Customer Activity Tracking
  async logActivity(sessionId, eventType, menuItemId = null, metadata = {}) {
    return this.request('/activities/', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        event_type: eventType,
        menu_item: menuItemId,
        metadata,
      }),
      auth: false,
    });
  }
}

export default new ApiService();
