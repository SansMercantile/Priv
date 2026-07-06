import test from 'node:test';
import assert from 'node:assert/strict';
import { buildFallbackChatResponse } from './privChatResponse.js';

test('buildFallbackChatResponse handles watchlist requests without hardcoded market commentary', () => {
  const reply = buildFallbackChatResponse('add AAPL to my watchlist', { provider: 'Google Gemini', errorDetail: 'service unavailable' });
  assert.match(reply, /watchlist/i);
  assert.doesNotMatch(reply, /forex|gold|stock market|weekend/i);
});

test('buildFallbackChatResponse gives a generic explanation when the AI service is unavailable', () => {
  const reply = buildFallbackChatResponse('summarize my portfolio', { provider: 'Google Gemini', errorDetail: 'service unavailable' });
  assert.match(reply, /service is unavailable|local fallback/i);
  assert.match(reply, /watchlist|chart|alerts/i);
});
