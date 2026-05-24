import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

# Import AccountState model for type hinting
from backend.trading_engine.state_monitor import AccountState # NEW IMPORT for type hinting

# --- Configuration Constants ---
JOURNAL_FILE: str = "logs/journal_entries.jsonl"
COOLDOWN_FILE: str = "logs/greed_cooldown.json"
GREED_COOLDOWN_MINUTES: int = 3
GREED_PROFIT_THRESHOLD: float = 300.0
GREED_FREE_MARGIN_THRESHOLD: float = 150.0

# FIX: Change state: Dict[str, Any] to state: AccountState
def check_greed_pattern(user_text: str, state: AccountState) -> bool:
    """
    Checks if user text or account state indicates a potential "greed" pattern.
    """
    greedy_phrases = ["easy win", "double down", "all in", "quick scalp", "100% setup"]
    if any(p in user_text.lower() for p in greedy_phrases):
        return True

    # FIX: Use dot notation for AccountState attributes
    profit_today = state.profit_today
    free_margin = state.free_margin

    if profit_today > GREED_PROFIT_THRESHOLD and free_margin < GREED_FREE_MARGIN_THRESHOLD:
        return True
    return False

def start_greed_cooldown(minutes: int = GREED_COOLDOWN_MINUTES) -> None:
    """
    Starts a cooldown period to prevent impulsive "greed" trades.
    """
    cooldown_until = datetime.now() + timedelta(minutes=minutes)
    os.makedirs(os.path.dirname(COOLDOWN_FILE), exist_ok=True)
    try:
        with open(COOLDOWN_FILE, "w", encoding="utf-8") as f:
            json.dump({"cooldown_until": cooldown_until.isoformat()}, f, indent=2)
    except IOError as e:
        print(f"[ERROR] Failed to write greed cooldown file to {COOLDOWN_FILE}: {e}")
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred while starting greed cooldown: {e}")

def is_in_greed_cooldown() -> bool:
    """
    Checks if the system is currently in a greed cooldown period.
    """
    if not os.path.exists(COOLDOWN_FILE):
        return False
    try:
        with open(COOLDOWN_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        cooldown_until_str = data.get("cooldown_until")
        if not cooldown_until_str:
            print(f"[WARNING] 'cooldown_until' key missing in {COOLDOWN_FILE}. Treating as not in cooldown.")
            return False

        cooldown_until = datetime.fromisoformat(cooldown_until_str)
        return datetime.now() < cooldown_until
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        print(f"[ERROR] Failed to read or parse greed cooldown file {COOLDOWN_FILE}: {e}. Treating as not in cooldown.")
        return False
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred while checking greed cooldown: {e}. Treating as not in cooldown.")
        return False

def write_journal_prompt(trigger_event: str) -> None:
    """
    Writes a journal prompt to a log file based on a triggered emotional event.
    """
    prompts = {
        "greed_alert": "What led to this feeling of overconfidence?",
        "margin_warning": "What caused your margin to become this tight?",
        "profit_surge": "How did your plan contribute to this win?",
        "drawdown": "What part of your plan failed here—and how will you adjust?"
    }

    entry = {
        "timestamp": datetime.now().isoformat(),
        "triggered_by": trigger_event,
        "prompt": prompts.get(trigger_event, "How are you feeling about this moment?"),
        "response": None  # User fills this in later via UI
    }

    os.makedirs(os.path.dirname(JOURNAL_FILE), exist_ok=True)
    try:
        with open(JOURNAL_FILE, "a", encoding="utf-8") as f:
            json.dump(entry, f)
            f.write("\n") # Add newline for jsonl format
    except IOError as e:
        print(f"[ERROR] Failed to write journal prompt to {JOURNAL_FILE}: {e}")
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred while writing journal prompt: {e}")