# backend/support_ai/insight_synthesizer.py

import json
import os
from collections import Counter
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple

from backend.config import settings

def load_conversation_logs() -> List[Dict[str, Any]]:
    """Loads all conversation log entries from the specified JSONL file."""
    log_file_path = settings.CONVERSATION_LOG_PATH
    if not os.path.exists(log_file_path):
        return []
    
    logs: List[Dict[str, Any]] = []
    try:
        with open(log_file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    logs.append(json.loads(line))
        return logs
    except Exception as e:
        print(f"[ERROR] Failed to read or parse conversation logs from {log_file_path}: {e}")
        return []

def get_top_emotions(limit: int = 5) -> List[Tuple[str, int]]:
    """Analyzes logs to find the most frequent emotions."""
    logs = load_conversation_logs()
    if not logs:
        return []
    emotion_counts = Counter(log.get("emotion") for log in logs if log.get("emotion"))
    return emotion_counts.most_common(limit)

def get_frequent_phrases(limit: int = 10) -> List[Tuple[str, int]]:
    """Analyzes logs to find the most frequent user terms."""
    logs = load_conversation_logs()
    if not logs:
        return []
    
    # A simple list of common words to ignore
    stopwords = {'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'you', 'your', 'he', 'him', 'his', 'she', 'her', 'it', 'its', 'they', 'them', 'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'as', 'of', 'at', 'by', 'for', 'with', 'about', 'to', 'from'}
    
    word_counts = Counter()
    for log in logs:
        user_text = log.get("user", "")
        if user_text:
            words = user_text.lower().split()
            for word in words:
                clean_word = ''.join(filter(str.isalnum, word))
                if clean_word and clean_word not in stopwords:
                    word_counts[clean_word] += 1
    return word_counts.most_common(limit)


def synthesize_recent_insights(days: int = 7) -> str:
    """
    Synthesizes a summary of recent user interactions based on conversation logs.
    """
    now = datetime.now()
    cutoff = now - timedelta(days=days)
    all_logs = load_conversation_logs()
    
    recent_logs = [
        log for log in all_logs 
        if "timestamp" in log and datetime.fromisoformat(log["timestamp"]) >= cutoff
    ]
        
    if not recent_logs:
        return "No recent activity found for insight synthesis."

    top_emotion = get_top_emotions(limit=1)[0][0] if get_top_emotions(limit=1) else "None"
    top_word = get_frequent_phrases(limit=1)[0][0] if get_frequent_phrases(limit=1) else "None"

    summary = f"""
In the past {days} days:
- Most triggered emotion: **{top_emotion}**
- Most mentioned concern: “{top_word}”
- Total conversations: {len(recent_logs)}
Suggestion: Review your exposure to topics that trigger '{top_emotion}', and set guardrails for overtrading related to '{top_word}'.
"""
    return summary.strip()