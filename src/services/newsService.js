/**
 * News Service
 * Handles news and sentiment analysis
 */

import apiClient from '../api/apiClient';

export const newsService = {
  /**
   * Search news
   */
  async searchNews(query, limit = 20, timeframe = '1d') {
    try {
      const response = await apiClient.get('/api/v1/news/search', {
        params: { q: query, limit, timeframe }
      });
      return response.data || [];
    } catch (error) {
      console.error('Error searching news:', error);
      throw error;
    }
  },

  /**
   * Get news for specific symbols
   */
  async getNewsForSymbols(symbols, limit = 10) {
    try {
      const response = await apiClient.get('/api/v1/news/symbols', {
        params: { symbols: symbols.join(','), limit }
      });
      return response.data || [];
    } catch (error) {
      console.error('Error fetching symbol news:', error);
      throw error;
    }
  },

  /**
   * Get news feed
   */
  async getNewsFeed(page = 1, pageSize = 20) {
    try {
      const response = await apiClient.get('/api/v1/news/feed', {
        params: { page, page_size: pageSize }
      });
      return response.data || { articles: [], total: 0 };
    } catch (error) {
      console.error('Error fetching news feed:', error);
      throw error;
    }
  },

  /**
   * Get market news
   */
  async getMarketNews(category = 'general', limit = 10) {
    try {
      const response = await apiClient.get('/api/v1/news/market', {
        params: { category, limit }
      });
      return response.data || [];
    } catch (error) {
      console.error('Error fetching market news:', error);
      throw error;
    }
  },

  /**
   * Start news analysis workflow
   */
  async startNewsWorkflow() {
    try {
      const response = await apiClient.post(
        '/api/v1/orchestration/orchestration/news-workflow',
        {}
      );
      return response.data;
    } catch (error) {
      console.error('Error starting news workflow:', error);
      throw error;
    }
  },

  /**
   * Get sentiment analysis
   */
  async getSentimentAnalysis(symbols) {
    try {
      const response = await apiClient.post('/api/v1/news/sentiment', {
        symbols
      });
      return response.data || {};
    } catch (error) {
      console.error('Error fetching sentiment analysis:', error);
      throw error;
    }
  },

  /**
   * Get trending topics
   */
  async getTrendingTopics(limit = 10) {
    try {
      const response = await apiClient.get('/api/v1/news/trending', {
        params: { limit }
      });
      return response.data || [];
    } catch (error) {
      console.error('Error fetching trending topics:', error);
      throw error;
    }
  },

  /**
   * Get news by category
   */
  async getNewsByCategory(category, limit = 10) {
    try {
      const response = await apiClient.get(`/api/v1/news/category/${category}`, {
        params: { limit }
      });
      return response.data || [];
    } catch (error) {
      console.error(`Error fetching ${category} news:`, error);
      throw error;
    }
  }
};
