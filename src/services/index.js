/**
 * Services Index
 * Central export for all services
 */

export { portfolioService } from './portfolioService';
export { tradingService } from './tradingService';
export { riskService } from './riskService';
export { newsService } from './newsService';
export { agentsService } from './agentsService';
export { orchestrationService } from './orchestrationService';

// Convenience object
export const services = {
  portfolio: require('./portfolioService').portfolioService,
  trading: require('./tradingService').tradingService,
  risk: require('./riskService').riskService,
  news: require('./newsService').newsService,
  agents: require('./agentsService').agentsService,
  orchestration: require('./orchestrationService').orchestrationService
};
