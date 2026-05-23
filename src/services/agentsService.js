/**
 * Agents Service
 * Handles agent management and orchestration
 */

import apiClient from '../api/apiClient';

export const agentsService = {
  /**
   * Get all registered agents
   */
  async listAllAgents() {
    try {
      const response = await apiClient.get(
        '/api/v1/orchestration/registry/agents'
      );
      return response.data || { agents: [] };
    } catch (error) {
      console.error('Error listing agents:', error);
      throw error;
    }
  },

  /**
   * Get agents by type
   */
  async getAgentsByType(agentType) {
    try {
      const response = await apiClient.get(
        `/api/v1/orchestration/registry/agents/${agentType}`
      );
      return response.data || { agents: [] };
    } catch (error) {
      console.error(`Error fetching ${agentType} agents:`, error);
      throw error;
    }
  },

  /**
   * Get specific agent status
   */
  async getAgentStatus(agentId) {
    try {
      const response = await apiClient.get(
        `/api/v1/orchestration/registry/agents/${agentId}/status`
      );
      return response.data || {};
    } catch (error) {
      console.error(`Error fetching agent ${agentId} status:`, error);
      throw error;
    }
  },

  /**
   * Get registry status
   */
  async getRegistryStatus() {
    try {
      const response = await apiClient.get(
        '/api/v1/orchestration/registry/status'
      );
      return response.data || {};
    } catch (error) {
      console.error('Error fetching registry status:', error);
      throw error;
    }
  },

  /**
   * Get agent reputations
   */
  async getAgentReputations() {
    try {
      const response = await apiClient.get('/api/v1/agents/reputations');
      return response.data || {};
    } catch (error) {
      console.error('Error fetching agent reputations:', error);
      throw error;
    }
  },

  /**
   * Get agent status with reputation
   */
  async getAgentsWithReputation() {
    try {
      const response = await apiClient.get(
        '/api/v1/agents/status_with_reputation'
      );
      return response.data || { agents: [] };
    } catch (error) {
      console.error('Error fetching agents with reputation:', error);
      throw error;
    }
  },

  /**
   * Get agent metrics
   */
  async getAgentMetrics() {
    try {
      const response = await apiClient.get('/api/v1/agents/metrics');
      return response.data || {};
    } catch (error) {
      console.error('Error fetching agent metrics:', error);
      throw error;
    }
  },

  /**
   * Get agent activity log
   */
  async getActivityLog(limit = 50, offset = 0) {
    try {
      const response = await apiClient.get('/api/v1/agents/activity', {
        params: { limit, offset }
      });
      return response.data || { activities: [] };
    } catch (error) {
      console.error('Error fetching activity log:', error);
      throw error;
    }
  }
};
