"""
News API endpoints for PRIV backend.
Provides news articles, sentiment analysis, and market intelligence.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging


logger = logging.getLogger(__name__)

router = APIRouter()


class SentimentRequest(BaseModel):
    symbols: List[str] = []


@router.get("/articles")

async def get_news_articles(limit: int = 50, hours: int = 24) -> Dict[str, Any]:
    """
    Get recent news articles from RSS feeds and GDELT.
    
    Args:
        limit: Maximum number of articles to return
        hours: Number of hours to look back
    
    Returns:
        Dictionary containing articles and metadata
    """
    try:
        from backend.data_sourcing.global_news_ingestor import GlobalNewsIngestor
        
        ingestor = GlobalNewsIngestor()
        
        # Fetch from RSS feeds
        articles = await ingestor.fetch_all_rss_articles()
        
        # Sort by date (most recent first)
        articles.sort(key=lambda x: x.get('published', ''), reverse=True)
        
        # Limit results
        articles = articles[:limit]
        
        # Get sentiment distribution
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        for article in articles:
            sentiment = article.get('sentiment', 'neutral')
            if sentiment in sentiment_counts:
                sentiment_counts[sentiment] += 1
        
        return {
            "articles": articles,
            "total": len(articles),
            "sentiment_distribution": sentiment_counts,
            "sources": len(set(article.get('source', 'Unknown') for article in articles)),
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching news articles: {e}", exc_info=True)
        return {
            "articles": [],
            "total": 0,
            "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0},
            "sources": 0,
            "last_updated": datetime.utcnow().isoformat(),
            "error": str(e)
        }


@router.get("/sentiment")
async def get_market_sentiment() -> Dict[str, Any]:
    """
    Get overall market sentiment analysis from news sources.
    
    Returns:
        Dictionary containing sentiment metrics
    """
    try:
        articles = await get_news_articles(limit=100, hours=24)
        
        sentiment_dist = articles['sentiment_distribution']
        total = sum(sentiment_dist.values())
        
        if total == 0:
            sentiment_score = 0.0
        else:
            # Calculate weighted sentiment score (-1 to +1)
            sentiment_score = (
                (sentiment_dist['positive'] - sentiment_dist['negative']) / total
            )
        
        # Determine overall sentiment
        if sentiment_score > 0.2:
            overall = "bullish"
        elif sentiment_score < -0.2:
            overall = "bearish"
        else:
            overall = "neutral"
        
        return {
            "overall_sentiment": overall,
            "sentiment_score": round(sentiment_score, 3),
            "distribution": sentiment_dist,
            "total_articles": total,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error calculating market sentiment: {e}", exc_info=True)
        return {
            "overall_sentiment": "neutral",
            "sentiment_score": 0.0,
            "distribution": {"positive": 0, "negative": 0, "neutral": 0},
            "total_articles": 0,
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


@router.get("/sources")
async def get_news_sources() -> Dict[str, Any]:
    """
    Get list of active news sources and their status.
    
    Returns:
        Dictionary containing source information
    """
    from backend.data_sourcing.global_news_ingestor import RSS_FEED_CONFIG
    
    sources = []
    for name, url in RSS_FEED_CONFIG.items():
        sources.append({
            "name": name.replace("_", " "),
            "url": url,
            "status": "active",
            "type": "RSS"
        })
    
    # Add GDELT
    sources.append({
        "name": "GDELT Global Database",
        "url": "https://www.gdeltproject.org/",
        "status": "active",
        "type": "Database"
    })
    
    return {
        "sources": sources,
        "total": len(sources),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/search")
async def search_news(q: Optional[str] = None, symbols: Optional[str] = None, limit: int = 20, timeframe: str = "1d") -> Dict[str, Any]:
    """Frontend-friendly search alias over the article feed."""
    base = await get_news_articles(limit=limit, hours=24)
    terms = [term.strip().lower() for term in (q or symbols or "").split(',') if term.strip()]
    if not terms:
        return base

    filtered = [
        article for article in base.get("articles", [])
        if any(
            term in (article.get("title", "") + " " + article.get("content", "") + " " + article.get("summary", "")).lower()
            for term in terms
        )
    ]
    return {
        **base,
        "articles": filtered[:limit],
        "total": len(filtered[:limit]),
        "query": q or symbols,
        "timeframe": timeframe,
    }


@router.get("/feed")
async def get_news_feed(page: int = 1, page_size: int = 20) -> Dict[str, Any]:
    """Paginated feed alias for the frontend news page."""
    base = await get_news_articles(limit=max(page * page_size, page_size), hours=24)
    start = max((page - 1) * page_size, 0)
    end = start + page_size
    articles = base.get("articles", [])[start:end]
    return {
        "articles": articles,
        "total": base.get("total", 0),
        "page": page,
        "page_size": page_size,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/market")
async def get_market_news(category: str = "general", limit: int = 10) -> Dict[str, Any]:
    base = await get_news_articles(limit=limit, hours=24)
    return {
        "category": category,
        "articles": base.get("articles", []),
        "total": len(base.get("articles", [])),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/symbols")
async def get_news_for_symbols(symbols: str, limit: int = 10) -> Dict[str, Any]:
    return await search_news(symbols=symbols, limit=limit)


@router.post("/sentiment")
async def get_symbol_sentiment(payload: SentimentRequest) -> Dict[str, Any]:
    sentiment = await get_market_sentiment()
    sentiment["symbols"] = payload.symbols
    return sentiment


@router.get("/trending")
async def get_trending_topics(limit: int = 10) -> Dict[str, Any]:
    base = await get_news_articles(limit=max(limit, 20), hours=24)
    articles = base.get("articles", [])
    keywords: dict[str, int] = {}
    for article in articles:
        title = article.get("title", "")
        for token in title.split():
            cleaned = ''.join(ch for ch in token if ch.isalnum()).upper()
            if len(cleaned) >= 3:
                keywords[cleaned] = keywords.get(cleaned, 0) + 1
    topics = [
        {"topic": topic, "mentions": mentions}
        for topic, mentions in sorted(keywords.items(), key=lambda item: item[1], reverse=True)[:limit]
    ]
    return {"topics": topics, "timestamp": datetime.utcnow().isoformat()}


@router.get("/category/{category}")
async def get_news_by_category(category: str, limit: int = 10) -> Dict[str, Any]:
    result = await get_market_news(category=category, limit=limit)
    result["category"] = category
    return result

