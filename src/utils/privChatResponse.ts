export interface PrivChatFallbackContext {
  provider?: string;
  errorDetail?: string;
  prompt?: string;
}

export function buildFallbackChatResponse(prompt: string, context: PrivChatFallbackContext = {}): string {
  const normalizedPrompt = (prompt || '').trim().toLowerCase();
  const provider = context.provider || 'AI provider';
  const errorDetail = context.errorDetail || 'service unavailable';

  if (normalizedPrompt.includes('watchlist')) {
    return `The watchlist update request was received, but the ${provider} service is currently unavailable (${errorDetail}). You can still manage your watchlist locally in the UI by adding or removing symbols.`;
  }

  if (normalizedPrompt.includes('chart') || normalizedPrompt.includes('graph')) {
    return `The chart request could not be completed because the ${provider} service is currently unavailable (${errorDetail}). You can still inspect the locally generated chart view or try again in a moment.`;
  }

  if (normalizedPrompt.includes('alert')) {
    return `The alert request could not be processed because the ${provider} service is unavailable (${errorDetail}). You can create alerts from the local interface and they will be stored for later sync.`;
  }

  if (normalizedPrompt.includes('portfolio') || normalizedPrompt.includes('balance') || normalizedPrompt.includes('position')) {
    return `The portfolio request could not be completed because the ${provider} service is unavailable (${errorDetail}). A local fallback is available for watchlist, chart, and alert actions.`;
  }

  return `The ${provider} service is currently unavailable (${errorDetail}), so this request is using a local fallback. Try a simpler request such as adding an item to your watchlist, creating an alert, or asking for a chart.`;
}
