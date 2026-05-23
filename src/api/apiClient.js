import axios from 'axios';
import { readDemoMode, getSessionUserId } from '../lib/environment';

class APIClient {
  constructor() {
    this.baseURL = import.meta.env.VITE_BACKEND_API_URL || '';
    this.wsBaseURL = import.meta.env.VITE_BACKEND_WS_URL || '';
    this.wsConnections = new Map();
    this.eventListeners = new Map();

    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('authToken');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        config.headers['X-Priv-Demo-Mode'] = readDemoMode() ? 'true' : 'false';
        const uid = getSessionUserId();
        if (uid) {
          config.headers['X-User-Id'] = uid;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

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

  normalizeEndpoint(endpoint) {
    if (!endpoint) return '/';
    return endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  }

  async request(method, endpoint, data = {}, config = {}) {
    const normalizedEndpoint = this.normalizeEndpoint(endpoint);
    const requestConfig = {
      method: method.toLowerCase(),
      url: normalizedEndpoint,
      ...config,
    };

    if (['get', 'delete'].includes(method.toLowerCase())) {
      const normalizedParams = data && typeof data === 'object' && data.params && typeof data.params === 'object'
        ? data.params
        : data;
      requestConfig.params = normalizedParams;
    } else {
      requestConfig.data = data;
    }

    try {
      const response = await this.client.request(requestConfig);
      return response.data;
    } catch (error) {
      console.error(`${method.toUpperCase()} ${normalizedEndpoint} failed:`, error);
      throw error;
    }
  }

  async get(endpoint, params = {}, config = {}) {
    return this.request('GET', endpoint, params, config);
  }

  async post(endpoint, data = {}, config = {}) {
    return this.request('POST', endpoint, data, config);
  }

  async put(endpoint, data = {}, config = {}) {
    return this.request('PUT', endpoint, data, config);
  }

  async delete(endpoint, params = {}, config = {}) {
    return this.request('DELETE', endpoint, params, config);
  }

  async postBlob(endpoint, data = {}, config = {}) {
    const mergedConfig = {
      responseType: 'blob',
      ...config,
    };
    return this.request('POST', endpoint, data, mergedConfig);
  }

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

  connectWebSocket(endpoint, onMessage, onError = null, onClose = null) {
    const wsUrl = this.wsBaseURL
      ? `${this.wsBaseURL}${endpoint}`
      : this.baseURL
      ? `${this.baseURL.replace(/^http/, 'ws')}${endpoint}`
      : endpoint;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log(`WebSocket connected: ${endpoint}`);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const normalizedData = data?.type === 'update' && data?.data
          ? { type: 'system_update', payload: data.data }
          : data;
        onMessage(normalizedData);
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

  async sendChatMessage(message, conversationId = null) {
    return this.post('/api/v1/chat', {
      message,
      conversation_id: conversationId,
      timestamp: new Date().toISOString(),
    });
  }

  async analyzeEmotion(imageBase64) {
    return this.post('/api/v1/vision/analyze-frame', {
      image_base64: imageBase64,
    });
  }

  async getUserProfile() {
    return this.get('/api/v1/profile');
  }

  async updateUserProfile(profileData) {
    return this.put('/api/v1/profile', profileData);
  }

  async getTradeAlerts() {
    return this.get('/api/v1/trading/alerts');
  }

  async getRiskAnalysis() {
    return this.get('/api/v1/risk');
  }

  async getPortfolioPositions() {
    const response = await this.get('/api/v1/portfolio/positions');
    if (response && response.data) {
      return {
        totalValue: response.data.summary?.total_market_value || 0,
        dailyChange: response.data.summary?.total_unrealized_pnl || 0,
        dailyChangePercent: response.data.summary?.total_unrealized_pnl_pct || 0,
        positions: response.data.positions || [],
      };
    }
    return {
      totalValue: 0,
      dailyChange: 0,
      dailyChangePercent: 0,
      positions: [],
    };
  }

  async getMarketData(symbols = []) {
    const response = await this.get('/api/v1/market/data', { symbols: symbols.join(',') });
    if (response && response.data) {
      return {
        indices: response.data.indices || [],
        quotes: response.data.quotes || [],
        alerts: response.data.alerts || [],
        sentiment: response.data.sentiment || 'neutral',
      };
    }
    return {
      indices: [],
      quotes: [],
      alerts: [],
      sentiment: 'neutral',
    };
  }

  async getSystemHealth() {
    const response = await this.get('/api/v1/system/health');
    if (response && response.data) {
      return {
        health: response.data.status || 'good',
        uptime: response.data.uptime_seconds || 0,
        threats: response.data.system_metrics?.disk_usage_pct > 95 ? 1 : 0,
        performance: response.data.system_metrics?.cpu_usage_pct || 0,
      };
    }
    return {
      health: 'good',
      uptime: 0,
      threats: 0,
      performance: 0,
    };
  }

  async getAgentStatus() {
    const response = await this.get('/api/v1/agents/status');
    if (response && response.data) {
      const agents = response.data.agents || [];
      const activeAgents = agents.filter((a) => a.status === 'active').length;
      const avgSuccessRate = agents.length > 0
        ? agents.reduce((sum, a) => sum + (a.success_rate || a.performance?.accuracy || 0), 0) / agents.length
        : 0;
      const decisions = agents.slice(0, 5).map((agent) => ({
        agent: agent.name,
        action: agent.status === 'active' ? 'ACTIVE' : 'IDLE',
        symbol: agent.type?.toUpperCase?.() || 'SYSTEM',
        confidence: (agent.performance?.accuracy || agent.success_rate || 0) / 100,
        timestamp: agent.last_activity || new Date().toISOString(),
      }));

      return {
        active: activeAgents,
        total: agents.length,
        performance: avgSuccessRate / 100,
        decisions,
        agents,
      };
    }
    return {
      active: 0,
      total: 0,
      performance: 0,
      decisions: [],
      agents: [],
    };
  }

  async getSupportedTaxCountries() {
    const response = await this.get('/api/v1/tax/supported_countries');
    if (response && response.data) return response.data;
    return [];
  }

  async calculateTax(payload) {
    const response = await this.post('/api/v1/tax/calculate', payload);
    if (response && response.data) return response.data;
    return null;
  }

  async generateTaxReport(payload) {
    const response = await this.post('/api/v1/tax/report', payload);
    if (response && response.data) return response.data;
    return null;
  }

  async submitTaxReport(payload) {
    const response = await this.post('/api/v1/tax/submit', payload);
    if (response && response.data) return response.data;
    return null;
  }

  async submitKYCDocument(file, documentType = 'passport') {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);
    const response = await this.client.post('/api/v1/kyc/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  }

  async getKycStatus() {
    return this.get('/api/v1/kyc/status');
  }

  async getKycRecord() {
    return this.get('/api/v1/kyc/');
  }

  async saveKycDraft(payload) {
    return this.put('/api/v1/kyc/draft', payload);
  }

  async submitKyc(payload) {
    return this.post('/api/v1/kyc/submit', payload);
  }

  async getOAuthBrokers() {
    return this.get('/api/v1/auth/brokers');
  }

  async getOAuthConnections() {
    return this.get('/api/v1/auth/connections');
  }

  getOAuthLoginUrl(broker, accountType = 'demo') {
    const base = this.baseURL || '';
    const uid = getSessionUserId();
    const params = new URLSearchParams();
    if (accountType) params.set('account_type', accountType);
    if (uid) params.set('user_id', uid);
    const q = params.toString() ? `?${params.toString()}` : '';
    return `${base}/api/v1/auth/${broker}/login${q}`;
  }

  async disconnectOAuthBroker(broker, accountType = 'live') {
    return this.delete(`/api/v1/auth/connections/${broker}`, { account_type: accountType });
  }

  async getAgiStatus() {
    return this.get('/api/v1/agi/status');
  }

  async updateAgiEmotionalParams(params) {
    return this.put('/api/v1/agi/emotional-params', params);
  }

  async runAgiTask(taskType, params = {}) {
    return this.post('/api/v1/agi/task', { task_type: taskType, params });
  }

  async connectBroker(brokerData) {
    return this.post('/api/v1/connections/save-broker-keys', brokerData);
  }

  async getBrokerConnections() {
    return this.get('/api/v1/connections/brokers');
  }

  cleanup() {
    this.wsConnections.forEach((ws) => ws.close());
    this.wsConnections.clear();
    this.eventListeners.forEach((eventSource) => eventSource.close());
    this.eventListeners.clear();
  }
}

const apiClientInstance = new APIClient();

const apiClient = async (endpoint, method = 'GET', data = {}, config = {}) =>
  apiClientInstance.request(method, endpoint, data, config);

apiClient.request = apiClientInstance.request.bind(apiClientInstance);
apiClient.get = apiClientInstance.get.bind(apiClientInstance);
apiClient.post = apiClientInstance.post.bind(apiClientInstance);
apiClient.put = apiClientInstance.put.bind(apiClientInstance);
apiClient.delete = apiClientInstance.delete.bind(apiClientInstance);
apiClient.postBlob = apiClientInstance.postBlob.bind(apiClientInstance);
apiClient.uploadFile = apiClientInstance.uploadFile.bind(apiClientInstance);
apiClient.connectWebSocket = apiClientInstance.connectWebSocket.bind(apiClientInstance);
apiClient.disconnectWebSocket = apiClientInstance.disconnectWebSocket.bind(apiClientInstance);
apiClient.connectSSE = apiClientInstance.connectSSE.bind(apiClientInstance);
apiClient.disconnectSSE = apiClientInstance.disconnectSSE.bind(apiClientInstance);
apiClient.sendChatMessage = apiClientInstance.sendChatMessage.bind(apiClientInstance);
apiClient.analyzeEmotion = apiClientInstance.analyzeEmotion.bind(apiClientInstance);
apiClient.getUserProfile = apiClientInstance.getUserProfile.bind(apiClientInstance);
apiClient.updateUserProfile = apiClientInstance.updateUserProfile.bind(apiClientInstance);
apiClient.getTradeAlerts = apiClientInstance.getTradeAlerts.bind(apiClientInstance);
apiClient.getRiskAnalysis = apiClientInstance.getRiskAnalysis.bind(apiClientInstance);
apiClient.getPortfolioPositions = apiClientInstance.getPortfolioPositions.bind(apiClientInstance);
apiClient.getMarketData = apiClientInstance.getMarketData.bind(apiClientInstance);
apiClient.getSystemHealth = apiClientInstance.getSystemHealth.bind(apiClientInstance);
apiClient.getAgentStatus = apiClientInstance.getAgentStatus.bind(apiClientInstance);
apiClient.getSupportedTaxCountries = apiClientInstance.getSupportedTaxCountries.bind(apiClientInstance);
apiClient.calculateTax = apiClientInstance.calculateTax.bind(apiClientInstance);
apiClient.generateTaxReport = apiClientInstance.generateTaxReport.bind(apiClientInstance);
apiClient.submitTaxReport = apiClientInstance.submitTaxReport.bind(apiClientInstance);
apiClient.submitKYCDocument = apiClientInstance.submitKYCDocument.bind(apiClientInstance);
apiClient.getKycStatus = apiClientInstance.getKycStatus.bind(apiClientInstance);
apiClient.getKycRecord = apiClientInstance.getKycRecord.bind(apiClientInstance);
apiClient.saveKycDraft = apiClientInstance.saveKycDraft.bind(apiClientInstance);
apiClient.submitKyc = apiClientInstance.submitKyc.bind(apiClientInstance);
apiClient.getOAuthBrokers = apiClientInstance.getOAuthBrokers.bind(apiClientInstance);
apiClient.getOAuthConnections = apiClientInstance.getOAuthConnections.bind(apiClientInstance);
apiClient.getOAuthLoginUrl = apiClientInstance.getOAuthLoginUrl.bind(apiClientInstance);
apiClient.disconnectOAuthBroker = apiClientInstance.disconnectOAuthBroker.bind(apiClientInstance);
apiClient.getAgiStatus = apiClientInstance.getAgiStatus.bind(apiClientInstance);
apiClient.updateAgiEmotionalParams = apiClientInstance.updateAgiEmotionalParams.bind(apiClientInstance);
apiClient.runAgiTask = apiClientInstance.runAgiTask.bind(apiClientInstance);
apiClient.connectBroker = apiClientInstance.connectBroker.bind(apiClientInstance);
apiClient.getBrokerConnections = apiClientInstance.getBrokerConnections.bind(apiClientInstance);

export default apiClient;
