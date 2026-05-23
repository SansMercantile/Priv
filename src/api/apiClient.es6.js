const axios = require('axios').default;

class APIClient {
  constructor() {
    this.baseURL = process.env.REACT_APP_BACKEND_API_URL || '';
    this.wsConnections = new Map();
    this.eventListeners = new Map();
    
    // Create axios instance with interceptors
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor for auth
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('authToken');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          this.handleAuthError();
        }
        return Promise.reject(error);
      }
    );
  }

  handleAuthError() {
    localStorage.removeItem('authToken');
    window.location.href = '/login';
  }

  // Standard HTTP methods
  async get(endpoint, params = {}) {
    try {
      const response = await this.client.get(endpoint, { params });
      return response.data;
    } catch (error) {
      console.error(`GET ${endpoint} failed:`, error);
      throw error;
    }
  }

  async post(endpoint, data = {}) {
    try {
      const response = await this.client.post(endpoint, data);
      return response.data;
    } catch (error) {
      console.error(`POST ${endpoint} failed:`, error);
      throw error;
    }
  }

  async put(endpoint, data = {}) {
    try {
      const response = await this.client.put(endpoint, data);
      return response.data;
    } catch (error) {
      console.error(`PUT ${endpoint} failed:`, error);
      throw error;
    }
  }

  async delete(endpoint) {
    try {
      const response = await this.client.delete(endpoint);
      return response.data;
    } catch (error) {
      console.error(`DELETE ${endpoint} failed:`, error);
      throw error;
    }
  }

  // File upload with progress
  async uploadFile(endpoint, file, onProgress = null) {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await this.client.post(endpoint, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (onProgress) {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            onProgress(percentCompleted);
          }
        },
      });
      return response.data;
    } catch (error) {
      console.error(`File upload to ${endpoint} failed:`, error);
      throw error;
    }
  }

  // WebSocket connection management
  connectWebSocket(endpoint, onMessage, onError = null, onClose = null) {
    const wsUrl = this.baseURL ? this.baseURL.replace('http', 'ws') + endpoint : endpoint;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log(`WebSocket connected: ${endpoint}`);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (error) {
        console.error('WebSocket message parsing error:', error);
      }
    };

    ws.onerror = (error) => {
      console.error(`WebSocket error on ${endpoint}:`, error);
      if (onError) onError(error);
    };

    ws.onclose = () => {
      console.log(`WebSocket closed: ${endpoint}`);
      if (onClose) onClose();
      
      // Auto-reconnect after 5 seconds
      setTimeout(() => {
        if (this.wsConnections.has(endpoint)) {
          this.connectWebSocket(endpoint, onMessage, onError, onClose);
        }
      }, 5000);
    };

    this.wsConnections.set(endpoint, ws);
    return ws;
  }

  disconnectWebSocket(endpoint) {
    const ws = this.wsConnections.get(endpoint);
    if (ws) {
      ws.close();
      this.wsConnections.delete(endpoint);
    }
  }

  // Server-Sent Events
  connectSSE(endpoint, onMessage, onError = null) {
    const sseUrl = `${this.baseURL}${endpoint}`;
    const eventSource = new EventSource(sseUrl);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (error) {
        console.error('SSE message parsing error:', error);
      }
    };

    eventSource.onerror = (error) => {
      console.error(`SSE error on ${endpoint}:`, error);
      if (onError) onError(error);
    };

    this.eventListeners.set(endpoint, eventSource);
    return eventSource;
  }

  disconnectSSE(endpoint) {
    const eventSource = this.eventListeners.get(endpoint);
    if (eventSource) {
      eventSource.close();
      this.eventListeners.delete(endpoint);
    }
  }

  // Specialized API methods
  async sendChatMessage(message, conversationId = null) {
    return this.post('/api/v1/chat', {
      message,
      conversation_id: conversationId,
      timestamp: new Date().toISOString()
    });
  }

  async analyzeEmotion(imageBase64) {
    return this.post('/api/v1/vision/analyze-frame', {
      image_base64: imageBase64
    });
  }

  async getUserProfile() {
    return this.get('/api/v1/profile');
  }

  async updateUserProfile(profileData) {
    return this.put('/api/v1/profile', profileData);
  }

  async getTradeAlerts() {
    return this.get('/api/v1/alerts');
  }

  async getRiskAnalysis() {
    return this.get('/api/v1/risk');
  }

  async getPortfolioPositions() {
    return this.get('/api/v1/portfolio/positions');
  }

  async getMarketData(symbols = []) {
    return this.get('/api/v1/market/data', { symbols: symbols.join(',') });
  }

  async getSystemHealth() {
    return this.get('/api/v1/system/health');
  }

  async getAgentStatus() {
    return this.get('/api/v1/agents/status');
  }

  async submitKYCDocument(file, documentType) {
    return this.uploadFile('/api/v1/kyc/upload', file);
  }

  async connectBroker(brokerData) {
    return this.post('/api/v1/brokers/connect', brokerData);
  }

  async getBrokerConnections() {
    return this.get('/api/v1/brokers/connections');
  }

  // Cleanup method
  cleanup() {
    // Close all WebSocket connections
    this.wsConnections.forEach((ws) => ws.close());
    this.wsConnections.clear();

    // Close all SSE connections
    this.eventListeners.forEach((eventSource) => eventSource.close());
    this.eventListeners.clear();
  }
}

module.exports = apiClient;
