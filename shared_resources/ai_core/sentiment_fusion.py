# backend/ai_core/sentiment_fusion.py

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class SentimentFusion:
    """
    Fuses qualitative news sentiment with quantitative market sentiment indicators
    to produce a more robust, holistic sentiment score.
    """
    def __init__(self):
        self.weights = {"news_sentiment": 0.6, "market_sentiment": 0.4}
        logger.info("SentimentFusion service initialized.")

    def _normalize_news_sentiment(self, news_analysis: Dict[str, Any]) -> float:
        """Converts news sentiment to a numerical score [-1.5, 1.5] scaled by impact."""
        sentiment_map = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}
        impact_map = {"high": 1.5, "medium": 1.0, "low": 0.5, "none": 0.2}
        
        sentiment_score = sentiment_map.get(news_analysis.get("sentiment", "neutral"), 0.0)
        impact_multiplier = impact_map.get(news_analysis.get("market_impact", "none"), 1.0)
        
        return sentiment_score * impact_multiplier

    def _calculate_market_sentiment(self, indicators: Dict[str, Any]) -> float:
        """Calculates a market sentiment score [-1, 1] from quantitative indicators."""
        score = 0.0
        count = 0
        
        mfi = indicators.get('MFI', [])
        if mfi and mfi[-1] is not None:
            if mfi[-1] > 80: score -= 1.0
            elif mfi[-1] < 20: score += 1.0
            count += 1
            
        bulls = indicators.get('BULLS_POWER', [])
        bears = indicators.get('BEARS_POWER', [])
        if bulls and bears and bulls[-1] is not None and bears[-1] is not None:
            if bulls[-1] > 0 and bears[-1] < 0: score += 0.75
            elif bulls[-1] < 0 and bears[-1] > 0: score -= 0.75
            count += 1

        return score / count if count > 0 else 0.0

    def fuse_sentiments(self, news_analyses: List[Dict[str, Any]], analytics_results: Dict[str, Any]) -> Dict[str, Any]:
        """Performs the fusion of news and market sentiment data."""
        total_news_score = sum(self._normalize_news_sentiment(article) for article in news_analyses)
        avg_news_score = total_news_score / len(news_analyses) if news_analyses else 0.0

        market_indicators = analytics_results.get('standard_indicators', {})
        market_score = self._calculate_market_sentiment(market_indicators)

        fused_score = (avg_news_score * self.weights["news_sentiment"]) + (market_score * self.weights["market_sentiment"])
        fused_score = max(-1.5, min(fused_score, 1.5))

        if fused_score > 0.7: label = "Strongly Bullish"
        elif fused_score > 0.2: label = "Bullish"
        elif fused_score < -0.7: label = "Strongly Bearish"
        elif fused_score < -0.2: label = "Bearish"
        else: label = "Neutral"

        return {
            "fused_sentiment_score": fused_score,
            "fused_sentiment_label": label,
            "component_scores": {
                "average_news_score": avg_news_score,
                "market_sentiment_score": market_score
            }
        }
