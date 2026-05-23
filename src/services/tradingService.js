/**
 * Trading Service
 * Handles trade execution and workflow coordination
 */

import apiClient from '../api/apiClient';

export const tradingService = {
  /**
   * Start a trading workflow
   */
  async startTradeWorkflow(symbols, strategy = 'default') {
    try {
      const response = await apiClient.post(
        '/api/v1/orchestration/orchestration/trade-workflow',
        { symbols, strategy }
      );
      return response.data;
    } catch (error) {
      console.error('Error starting trade workflow:', error);
      throw error;
    }
  },

  /**
   * Get trade workflow status
   */
  async getWorkflowStatus(workflowId) {
    try {
      const response = await apiClient.get(
        `/api/v1/orchestration/orchestration/workflows/${workflowId}`
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching workflow status:', error);
      throw error;
    }
  },

  /**
   * List all active workflows
   */
  async listWorkflows() {
    try {
      const response = await apiClient.get(
        '/api/v1/orchestration/orchestration/workflows'
      );
      return response.data.workflows || [];
    } catch (error) {
      console.error('Error listing workflows:', error);
      throw error;
    }
  },

  /**
   * Poll workflow status with interval
   */
  async pollWorkflowStatus(workflowId, interval = 5000, maxAttempts = 120) {
    return new Promise((resolve, reject) => {
      let attempts = 0;
      
      const pollInterval = setInterval(async () => {
        attempts++;
        
        try {
          const status = await this.getWorkflowStatus(workflowId);
          
          // Check if workflow is complete
          if (status.status === 'completed' || status.status === 'failed') {
            clearInterval(pollInterval);
            resolve(status);
            return;
          }
          
          // Check timeout
          if (attempts >= maxAttempts) {
            clearInterval(pollInterval);
            reject(new Error(`Workflow polling timeout after ${maxAttempts} attempts`));
            return;
          }
        } catch (error) {
          clearInterval(pollInterval);
          reject(error);
        }
      }, interval);
    });
  },

  /**
   * Get market data for symbols
   */
  async getMarketData(symbols) {
    try {
      const response = await apiClient.get('/api/v1/market/quotes', {
        params: { symbols: symbols.join(',') }
      });
      return response.data || [];
    } catch (error) {
      console.error('Error fetching market data:', error);
      throw error;
    }
  },

  /**
   * Get news for symbols
   */
  async getNews(symbols, limit = 10) {
    try {
      const response = await apiClient.get('/api/v1/news/search', {
        params: { symbols: symbols.join(','), limit }
      });
      return response.data || [];
    } catch (error) {
      console.error('Error fetching news:', error);
      throw error;
    }
  },

  /**
   * Get trading recommendations
   */
  async getRecommendations(symbols) {
    try {
      const response = await apiClient.post('/api/v1/orchestration/orchestration/trade-workflow', {
        symbols,
        strategy: 'analysis'
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching recommendations:', error);
      throw error;
    }
  }
};
