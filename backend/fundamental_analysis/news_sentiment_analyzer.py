import openai
from openai import OpenAI, APIError
from typing import Dict, Any, Tuple, List, Optional
import logging
import os
import json

logger = logging.getLogger(__name__)

class NewsSentimentAnalyzer:
    """
    Analyzes news article titles and content to determine sentiment and market impact
    using OpenAI's Large Language Models (LLMs).
    """
    def __init__(self, openai_api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        """
        Initializes the NewsSentimentAnalyzer.

        Args:
            openai_api_key (Optional[str]): The OpenAI API key. Defaults to OPENAI_API_KEY env var.
            model (str): The OpenAI LLM model to use for analysis.
        """
        api_key = openai_api_key if openai_api_key else os.getenv("OPENAI_API_KEY")
        if not api_key or "sk-" not in api_key:
            logger.warning("OPENAI_API_KEY not available. NewsSentimentAnalyzer will use fallback analysis.")
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)
            logger.info(f"NewsSentimentAnalyzer initialized with OpenAI model: {model}.")
        self.model = model

    def analyze_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes a single news article for sentiment and market impact.

        Args:
            article (Dict[str, Any]): A dictionary representing a news article, expected to
                                      contain 'title' and 'content' (or 'full_content').

        Returns:
            Dict[str, Any]: A dictionary containing 'sentiment' ('positive', 'negative', 'neutral'),
                            'market_impact' ('high', 'medium', 'low', 'none'), and 'reasoning'.
                            Returns default neutral/none if analysis fails.
        """
        title = article.get("title", "")
        content = article.get("content", "") or article.get("full_content", "") # Prefer full_content if available

        if not title and not content:
            logger.warning("Article has no title or content. Cannot perform sentiment analysis.")
            return {"sentiment": "neutral", "market_impact": "none", "reasoning": "No content to analyze."}
        
        # Fallback if OpenAI client not available
        if not self.client:
            logger.debug("OpenAI client not available, using fallback neutral sentiment.")
            return {"sentiment": "neutral", "market_impact": "low", "reasoning": "OpenAI API not configured - using fallback analysis."}

        # Construct the prompt for the LLM
        prompt_messages = [
            {"role": "system", "content": (
                "You are an expert financial news analyst. Your task is to analyze news articles "
                "and determine their sentiment towards financial markets/specific assets, "
                "and their potential market impact. "
                "Provide the sentiment as 'positive', 'negative', or 'neutral'. "
                "Provide the market impact as 'high', 'medium', 'low', or 'none'. "
                "Also, extract up to 3 most relevant financial symbols mentioned or implied (e.g., EURUSD, BTCUSD, AAPL). "
                "If the article implies a currency, specify it (e.g., 'USD'). If it's a general market trend, use 'GENERAL'."
                "Respond in a strict JSON format with keys: 'sentiment', 'market_impact', 'symbols', 'reasoning'. "
                "The reasoning should be concise, explaining why you assigned the sentiment and impact."
            )},
            {"role": "user", "content": f"Title: {title}\n\nContent: {content}\n\nStrict JSON Response:"}
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=prompt_messages,
                max_tokens=200, # Adjust max_tokens to allow for reasoning
                response_format={"type": "json_object"} # Ensure JSON output
            )
            
            analysis_output = json.loads(response.choices[0].message.content)
            
            # Validate and sanitize output
            sentiment = analysis_output.get("sentiment", "neutral").lower()
            market_impact = analysis_output.get("market_impact", "none").lower()
            symbols = analysis_output.get("symbols", [])
            reasoning = analysis_output.get("reasoning", "Analysis based on article content.")

            if sentiment not in ["positive", "negative", "neutral"]:
                sentiment = "neutral"
            if market_impact not in ["high", "medium", "low", "none"]:
                market_impact = "none"
            
            # Ensure symbols is a list of strings (handle None case)
            if symbols is None:
                symbols = []
            elif isinstance(symbols, str):
                symbols = [symbols.upper()]
            else:
                symbols = [str(s).upper() for s in symbols if s and isinstance(s, (str, int))]

            logger.info(f"Analyzed article '{title[:50]}...'. Sentiment: {sentiment}, Impact: {market_impact}, Symbols: {symbols}")
            return {
                "sentiment": sentiment,
                "market_impact": market_impact,
                "symbols": symbols,
                "reasoning": reasoning
            }

        except APIError as e:
            logger.error(f"OpenAI API Error during news sentiment analysis: {e}")
            return {"sentiment": "neutral", "market_impact": "none", "symbols": [], "reasoning": f"API Error: {e}"}
        except json.JSONDecodeError as e:
            logger.error(f"JSON Decode Error from LLM response: {e}. Raw response: {response.choices[0].message.content}")
            return {"sentiment": "neutral", "market_impact": "none", "symbols": [], "reasoning": f"LLM output format error: {e}"}
        except Exception as e:
            logger.error(f"Unexpected error during news sentiment analysis: {e}", exc_info=True)
            return {"sentiment": "neutral", "market_impact": "none", "symbols": [], "reasoning": f"Unexpected error: {e}"}

# Example Usage:
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Mock OpenAI API key for testing purposes if not in env
    # os.environ["OPENAI_API_KEY"] = "sk-..." 

    analyzer = NewsSentimentAnalyzer()

    mock_article_positive = {
        "title": "Major Tech Company Beats Earnings by Wide Margin, Stock Soars",
        "content": "Shares of AlphaTech Inc. surged 15% today after the company reported record-breaking quarterly earnings, driven by strong growth in its AI and cloud computing divisions. Analysts raised price targets significantly.",
    }
    mock_article_negative = {
        "title": "Unexpected Inflation Surge Rattles Markets, Central Bank Hints at Aggressive Hikes",
        "content": "Global markets took a severe hit as inflation figures came in much hotter than expected. The central bank's governor indicated a readiness for more aggressive interest rate increases, sparking recession fears. Bonds fell sharply.",
    }
    mock_article_neutral = {
        "title": "New Blockchain Protocol Aims to Improve Scalability",
        "content": "A research team announced a new consensus mechanism designed to enhance the transaction processing speed of decentralized networks, with initial test results showing promise. Adoption is yet to be seen.",
    }
    mock_article_geopolitical = {
        "title": "Geopolitical Tensions Rise in Eastern Europe, Impacting Commodity Prices",
        "content": "Escalating diplomatic disputes in the region have led to uncertainty. While direct economic sanctions are not yet in place, commodity prices, especially for natural gas and wheat, have seen upward pressure. Investors are watching closely.",
    }

    print("\n--- Analyzing Positive Article ---")
    result_positive = analyzer.analyze_article(mock_article_positive)
    print(f"Sentiment: {result_positive['sentiment']}, Impact: {result_positive['market_impact']}, Symbols: {result_positive['symbols']}\nReasoning: {result_positive['reasoning']}")

    print("\n--- Analyzing Negative Article ---")
    result_negative = analyzer.analyze_article(mock_article_negative)
    print(f"Sentiment: {result_negative['sentiment']}, Impact: {result_negative['market_impact']}, Symbols: {result_negative['symbols']}\nReasoning: {result_negative['reasoning']}")

    print("\n--- Analyzing Neutral Article ---")
    result_neutral = analyzer.analyze_article(mock_article_neutral)
    print(f"Sentiment: {result_neutral['sentiment']}, Impact: {result_neutral['market_impact']}, Symbols: {result_neutral['symbols']}\nReasoning: {result_neutral['reasoning']}")

    print("\n--- Analyzing Geopolitical Article ---")
    result_geopolitical = analyzer.analyze_article(mock_article_geopolitical)
    print(f"Sentiment: {result_geopolitical['sentiment']}, Impact: {result_geopolitical['market_impact']}, Symbols: {result_geopolitical['symbols']}\nReasoning: {result_geopolitical['reasoning']}")