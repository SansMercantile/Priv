import pytest
from datetime import datetime, timedelta
from backend.fundamental_analysis.news_sourcing.news_api_client import NewsAPIClient
import requests


def test_fetch_news_advanced_mock_mode_returns_articles():
    client = NewsAPIClient(use_mock=True)
    res = client.fetch_news_advanced(keywords=['inflation','EURUSD'], operator='OR', limit=5)
    assert isinstance(res, list)
    assert len(res) > 0
    assert all('title' in a and 'content' in a for a in res)


def test_fetch_news_handles_provider_errors(monkeypatch):
    # Simulate requests.get raising a RequestException for both providers
    def fake_get(*args, **kwargs):
        raise requests.exceptions.RequestException("Network failure")

    monkeypatch.setattr('requests.get', fake_get)

    client = NewsAPIClient(api_key_ai='DEMO', api_key_org='DEMO', use_mock=False)
    res = client.fetch_news(query='economy', limit=3)
    # On provider errors the client should gracefully return an empty list
    assert res == []
