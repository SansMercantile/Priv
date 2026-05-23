/**
 * Portfolio Service
 * Handles all portfolio-related API calls
 */

import apiClient from '../api/apiClient';

export const portfolioService = {
  /**
   * Get all portfolio positions
   */
  async getPositions() {
    try {
      const response = await apiClient.get('/api/v1/portfolio/positions');
      return response.data || [];
    } catch (error) {
      console.error('Error fetching positions:', error);
      throw error;
    }
  },

  /**
   * Get portfolio performance metrics
   */
  async getPerformance() {
    try {
      const response = await apiClient.get('/api/v1/portfolio/performance');
      return response.data || {};
    } catch (error) {
      console.error('Error fetching performance:', error);
      throw error;
    }
  },

  /**
   * Get complete portfolio summary
   */
  async getPortfolioSummary() {
    try {
      const [positions, performance] = await Promise.all([
        this.getPositions(),
        this.getPerformance()
      ]);
      
      return {
        positions,
        performance,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      console.error('Error fetching portfolio summary:', error);
      throw error;
    }
  },

  /**
   * Get portfolio allocation by sector
   */
  async getAllocation() {
    try {
      const positions = await this.getPositions();
      const allocation = {};
      
      positions.forEach(position => {
        const sector = position.sector || 'Other';
        allocation[sector] = (allocation[sector] || 0) + position.market_value;
      });
      
      return allocation;
    } catch (error) {
      console.error('Error calculating allocation:', error);
      throw error;
    }
  },

  /**
   * Get portfolio risk metrics
   */
  async getRiskMetrics() {
    try {
      const response = await apiClient.get('/api/v1/risk/portfolio');
      return response.data || {};
    } catch (error) {
      console.error('Error fetching risk metrics:', error);
      throw error;
    }
  }
};
