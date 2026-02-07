const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

type RequestOptions = RequestInit & {
  auth?: boolean;
};

class ApiService {
  private token: string | null = null;

  constructor() {
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('authToken');
    }
  }

  setToken(token: string) {
    this.token = token;
    if (typeof window !== 'undefined') {
      if (token) {
        localStorage.setItem('authToken', token);
      } else {
        localStorage.removeItem('authToken');
      }
    }
  }

  getToken() {
    return this.token;
  }

  logout() {
    this.setToken('');
    if (typeof window !== 'undefined') {
      localStorage.removeItem('user');
      localStorage.removeItem('userRole');
    }
  }

  private getHeaders(includeAuth = true): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    if (includeAuth && this.token) {
      headers['Authorization'] = `Token ${this.token}`;
    }
    return headers;
  }

  async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const config: RequestInit = {
      ...options,
      headers: {
        ...this.getHeaders(options.auth !== false),
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);
      if (!response.ok) {
        const responseText = await response.text();
        console.error('Raw API Error Response:', responseText);
        
        let errorData: any = {};
        try {
            errorData = JSON.parse(responseText);
        } catch (e) {
            // Not JSON
        }
        
        // Handle DRF-style errors { field: ["error1", "error2"] }
        let errorMessage = errorData.detail || errorData.error || `HTTP ${response.status}`;
        
        if (!errorMessage && typeof errorData === 'object') {
            // Flatten field errors into a single string
            errorMessage = Object.entries(errorData)
                .map(([key, value]) => {
                    const messages = Array.isArray(value) ? value.join(', ') : String(value);
                    return `${key}: ${messages}`;
                })
                .join(' | ');
        }
        
        throw new Error(errorMessage || 'An unknown error occurred');
      }
      if (response.status === 204) {
        return {} as T;
      }
      return await response.json();
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }

  // Auth - Step 1: Send credentials, get session token + OTP sent
  async loginStep1(credentials: { email: string; password: string }) {
    return this.request<{ session_token: string; message: string }>('/users/login/', {
      method: 'POST',
      body: JSON.stringify(credentials),
      auth: false,
    });
  }

  // Auth - Step 2: Verify OTP, get access token
  async loginStep2(data: { session_token: string; otp: string }) {
    const response = await this.request<{ 
      access: string; 
      refresh: string; 
      user_data: any 
    }>('/users/login/verify/', {
      method: 'POST',
      body: JSON.stringify(data),
      auth: false,
    });

    if (response.access) {
      this.setToken(response.access);
      if (typeof window !== 'undefined') {
          // Store user data if needed
          localStorage.setItem('user', JSON.stringify(response.user_data));
          localStorage.setItem('userRole', response.user_data?.type || 'staff');
      }
    }
    return response;
  }

  // Menu (Public/Manager)
  async getMenuItems(params: any = {}) {
    const searchParams = new URLSearchParams();
    if (params.page) searchParams.append('page', params.page.toString());
    if (params.page_size) searchParams.append('page_size', params.page_size.toString());
    if (params.search) searchParams.append('search', params.search);
    if (params.category) searchParams.append('category', params.category);
    if (params.section) searchParams.append('section', params.section);
    if (params.is_active !== undefined) searchParams.append('is_active', params.is_active.toString());
    
    // Check if pagination is requested (page or search is present) to expect distinct response type
    // Ideally we should have a separate type for paginated response
    return this.request<any>(`/menu/items/?${searchParams.toString()}`, { auth: false });
  }

  async getMenuStats() {
      return this.request<any>('/menu/items/stats/');
  }

  async getPublicMenu() {
    return this.request<any>('/menu/public/', { auth: false });
  }

  async createMenuItem(data: any) {
    return this.request<any>('/menu/items/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateMenuItem(id: string, data: any) {
    return this.request<any>(`/menu/items/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async deleteMenuItem(id: string) {
    return this.request<any>(`/menu/items/${id}/`, {
      method: 'DELETE',
    });
  }

  // Orders (Staff)
  async createOrder(data: any) {
    return this.request<any>('/menu/orders/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getOrders() {
    return this.request<any[]>('/menu/orders/');
  }

  // AI & Reports (Manager)
  async getSalesSuggestions(itemId?: string) {
     // If itemId passed, get specific suggestions, else general
     const url = itemId ? `/menu/ai/sales-suggestions/?item_id=${itemId}` : '/menu/ai/sales-suggestions/';
     return this.request<any>(url, { auth: false });
  }

  async getOwnerReport(period = 'weekly') {
    return this.request<any>('/menu/ai/owner-report/', {
      method: 'POST',
      body: JSON.stringify({ period }),
    });
  }

  async getMenuAnalysis() {
    return this.request<any>('/menu/ai/menu-analysis/', { method: 'GET' });
  }
  
  async getRecommendations() {
      return this.request<any>('/menu/recommendations/');
  }
}

export const apiService = new ApiService();
