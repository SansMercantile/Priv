/**
 * Orchestration Service — agent registry and workflow coordination.
 */

import apiClient from '../api/apiClient';

function unwrap(response) {
  if (response?.data !== undefined && response?.success !== undefined) {
    return response.data;
  }
  return response?.data ?? response;
}

export const orchestrationService = {
  async listRegistryAgents() {
    const response = await apiClient.get('/api/v1/orchestration/registry/agents');
    return unwrap(response);
  },

  async getRegistryStatus() {
    const response = await apiClient.get('/api/v1/orchestration/registry/status');
    return unwrap(response);
  },

  async startTradeWorkflow(symbols, strategy = 'default') {
    const response = await apiClient.post('/api/v1/orchestration/orchestration/trade-workflow', {
      symbols,
      strategy,
    });
    return unwrap(response);
  },

  async startRiskWorkflow(symbols, portfolioId = null) {
    const response = await apiClient.post('/api/v1/orchestration/orchestration/risk-workflow', {
      symbols,
      portfolio_id: portfolioId,
    });
    return unwrap(response);
  },

  async startNewsWorkflow() {
    const response = await apiClient.post('/api/v1/orchestration/orchestration/news-workflow', {});
    return unwrap(response);
  },

  async getWorkflowStatus(workflowId) {
    const response = await apiClient.get(`/api/v1/orchestration/orchestration/workflows/${workflowId}`);
    return unwrap(response);
  },

  async listWorkflows() {
    const response = await apiClient.get('/api/v1/orchestration/orchestration/workflows');
    return unwrap(response);
  },

  async publishMessage(topic, message) {
    const response = await apiClient.post('/api/v1/orchestration/broker/publish', { topic, message });
    return unwrap(response);
  },

  async getActiveTopics() {
    const response = await apiClient.get('/api/v1/orchestration/broker/topics');
    return unwrap(response);
  },
};
