/**
 * Risk Service
 * Handles risk analysis and metrics
 */

import apiClient from '../api/apiClient';

export const riskService = {
  /**
   * Get portfolio risk analysis
   */
  async getPortfolioRisk(portfolioId = null) {
    try {
      const response = await apiClient.get('/api/v1/risk/portfolio', {
        params: portfolioId ? { portfolio_id: portfolioId } : {}
      });
      return response.data || {};
    } catch (error) {
      console.error('Error fetching portfolio risk:', error);
      throw error;
    }
  },

  /**
   * Start risk analysis workflow
   */
  async startRiskWorkflow(symbols, portfolioId = null) {
    try {
      const response = await apiClient.post(
        '/api/v1/orchestration/orchestration/risk-workflow',
        { symbols, portfolio_id: portfolioId }
      );
      return response.data;
    } catch (error) {
      console.error('Error starting risk workflow:', error);
      throw error;
    }
  },

  /**
   * Get value at risk (VaR)
   */
  async getValueAtRisk(confidence = 0.95) {
    try {
      const response = await apiClient.get('/api/v1/risk/var', {
        params: { confidence }
      });
      return response.data || {};
    } catch (error) {
      console.error('Error fetching VaR:', error);
      throw error;
    }
  },

  /**
   * Get maximum drawdown
   */
  async getMaxDrawdown() {
    try {
      const response = await apiClient.get('/api/v1/risk/max-drawdown');
      return response.data || {};
    } catch (error) {
      console.error('Error fetching max drawdown:', error);
      throw error;
    }
  },

  /**
   * Get risk by position
   */
  async getRiskByPosition() {
    try {
      const response = await apiClient.get('/api/v1/risk/positions');
      return response.data || [];
    } catch (error) {
      console.error('Error fetching position risk:', error);
      throw error;
    }
  },

  /**
   * Analyze specific position risk
   */
  async analyzePositionRisk(symbol, quantity, entryPrice) {
    try {
      const response = await apiClient.post('/api/v1/risk/analyze-position', {
        symbol,
        quantity,
        entry_price: entryPrice
      });
      return response.data || {};
    } catch (error) {
      console.error('Error analyzing position risk:', error);
      throw error;
    }
  },

  /**
   * Get risk alerts
   */
  async getRiskAlerts() {
    try {
      const response = await apiClient.get('/api/v1/risk/alerts');
      return response.data || [];
    } catch (error) {
      console.error('Error fetching risk alerts:', error);
      throw error;
    }
  },

  /**
   * Get correlation matrix
   */
  async getCorrelationMatrix(symbols) {
    try {
      const response = await apiClient.post('/api/v1/risk/correlation', {
        symbols
      });
      return response.data || {};
    } catch (error) {
      console.error('Error fetching correlation matrix:', error);
      throw error;
    }
  }
};
