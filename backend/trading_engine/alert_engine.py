# backend/trading_engine/alert_engine.py

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import uuid
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Import Pydantic for position model for type checking and validation
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__) # Ensure logger is initialized after imports

# --- Configuration Constants for Alert Logic ---
# These can be made configurable via environment variables or a config file.
AGED_LOSS_HOURS_THRESHOLD: int = 6
LARGE_PNL_AMOUNT_THRESHOLD: float = 300.0

# Constants for TheMasterMind.mq4 alerting
# These parameters would ideally be configurable (e.g., via a config file or environment variables).
ALERT_REPEAT_COUNT: int = 3 # Number of times to repeat an alert
ALERT_PERIOD_SECONDS: int = 5 # Time in seconds between alert repetitions
ENABLE_SOUND_ALERT: bool = True # Control for sound alerts
ENABLE_EMAIL_ALERT: bool = True # Control for email alerts

# Email Configuration (PLACEHOLDERS - MUST BE CONFIGURED IN PRODUCTION)
# For security, these should be loaded from environment variables or a secure configuration system.
EMAIL_SENDER_ADDRESS: str = "your_email@example.com"
EMAIL_SENDER_PASSWORD: str = "your_email_password" # Use app-specific passwords or OAuth for security
EMAIL_RECEIVER_ADDRESS: str = "recipient_email@example.com"
EMAIL_SMTP_SERVER: str = "smtp.example.com" # e.g., "smtp.gmail.com"
EMAIL_SMTP_PORT: int = 587 # or 465 (SSL)


# Import Pydantic for position model for type checking and validation
try:
    from backend.trading_engine.positions import MockPosition as Position
except ImportError:
    # Fallback/placeholder if MockPosition cannot be imported directly
    class Position:
        def __init__(self, symbol: str, open_time: str, current_price: float, entry_price: float, volume: float, stop_loss: Optional[float] = None, **kwargs):
            self.symbol = symbol
            self.open_time = open_time
            self.current_price = current_price
            self.entry_price = entry_price
            self.volume = volume
            self.stop_loss = stop_loss

# --- Configuration Constants for Alert Logic ---
# These can be made configurable via environment variables or a config file.
AGED_LOSS_HOURS_THRESHOLD: int = 6
LARGE_PNL_AMOUNT_THRESHOLD: float = 300.0


class TradeAlert(BaseModel):
    """Represents a single trade alert."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique ID for the alert.")
    symbol: str = Field(..., description="The trading instrument symbol.")
    type: str = Field(..., description="The type of alert (e.g., 'aged_loss', 'no_stop', 'large_pnl').")
    message: str = Field(..., description="A descriptive message for the alert.")
    tone: str = Field("neutral", description="Optional tone for the alert (e.g., 'firm', 'urgent').")

def _send_email_alert(subject: str, body: str) -> bool:
    """
    Sends an email notification.
    Partially derived from SendMail concept in TheMasterMind.mq4. 
    """
    if not ENABLE_EMAIL_ALERT:
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER_ADDRESS
        msg['To'] = EMAIL_RECEIVER_ADDRESS
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT)
        server.starttls() # Secure the connection
        server.login(EMAIL_SENDER_ADDRESS, EMAIL_SENDER_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_SENDER_ADDRESS, EMAIL_RECEIVER_ADDRESS, text)
        server.quit()
        logger.info(f"Email alert sent: '{subject}' to {EMAIL_RECEIVER_ADDRESS}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email alert: {e}")
        return False

def check_alerts(positions: List[Position]) -> List[TradeAlert]:
    """
    Checks a list of trading positions for various alert conditions.

    Args:
        positions (List[Position]): A list of trading positions to evaluate.

    Returns:
        List[TradeAlert]: A list of generated TradeAlert objects.
    """
    alerts: List[TradeAlert] = []
    now = datetime.now()

    for pos in positions:
        try:
            # Convert open_time string to datetime object
            open_dt = datetime.fromisoformat(pos.open_time)
            duration = now - open_dt
            unrealized_pnl = (pos.current_price - pos.entry_price) * pos.volume

            # Aged Loss Alert
            if duration > timedelta(hours=AGED_LOSS_HOURS_THRESHOLD) and unrealized_pnl < 0:
                alerts.append(
                    TradeAlert(
                        symbol=pos.symbol,
                        type="aged_loss",
                        message=f"Trade has been losing for over {AGED_LOSS_HOURS_THRESHOLD} hours. Consider re-evaluating.",
                        tone="urgent" # Added a tone here
                    )
                )

            # No Stop Loss Alert
            if pos.stop_loss is None:
                alerts.append(
                    TradeAlert(
                        symbol=pos.symbol,
                        type="no_stop",
                        message="This trade has no stop loss set.",
                        tone="firm" # Added a tone here
                    )
                )
                
            # Large PnL Alert
            if abs(unrealized_pnl) > LARGE_PNL_AMOUNT_THRESHOLD:
                alerts.append(
                    TradeAlert(
                        symbol=pos.symbol,
                        type="large_pnl",
                        message=f"Unrealized PnL on {pos.symbol} is {unrealized_pnl:.2f}. Consider taking action!",
                        tone="urgent" if unrealized_pnl < 0 else "neutral" # Tone based on PnL sign
                    )
                )
        except Exception as e:
            # Log any errors encountered while processing a single position
            print(f"[ERROR] Error processing position {pos.symbol if hasattr(pos, 'symbol') else 'Unknown'}: {e}")
            alerts.append(
                TradeAlert(
                    symbol=pos.symbol if hasattr(pos, 'symbol') else "Unknown",
                    type="processing_error",
                    message=f"Error processing alert for this position: {e}",
                    tone="alert"
                )
            )

    return alerts

# Global variable to track last alert time for repetition 
_last_mastermind_alert_time: Dict[str, datetime] = {}
_mastermind_alert_repetition_count: Dict[str, int] = {}

def trigger_mastermind_alert(
    alert_type: str,
    message: str,
    symbol: str,
    signal_price: float = 0.0,
    stop_loss: float = 0.0,
    take_profit: float = 0.0,
    order_id: Optional[int] = None,
    use_alert: bool = True, # From UseAlert in TheMasterMind.mq4 
    send_email: bool = False # From SendEmail in TheMasterMind.mq4 
) -> None:
    """
    Triggers an alert similar to TheMasterMind.mq4's alerting system.
    This function handles repetition and integration with email/sound. 

    Args:
        alert_type (str): Type of alert (e.g., "BUY_SIGNAL", "SELL_SIGNAL", "CLOSE_BUY", "CLOSE_SELL").
        message (str): The primary message for the alert.
        symbol (str): The trading instrument symbol.
        signal_price (float): The price at which the signal occurred.
        stop_loss (float): The SL price related to the trade (if applicable).
        take_profit (float): The TP price related to the trade (if applicable).
        order_id (Optional[int]): The ID of the order/position related to the alert.
        use_alert (bool): Whether to use general alerts (e.g., console log, sound).
        send_email (bool): Whether to send an email for this alert.
    """
    alert_key = f"{symbol}_{alert_type}"
    current_time = datetime.now()

    last_alert_time = _last_mastermind_alert_time.get(alert_key)
    repetition_count = _mastermind_alert_repetition_count.get(alert_key, ALERT_REPEAT_COUNT) # Initialize with full count 

    if not use_alert:
        # Reset count if alert is explicitly disabled, otherwise it would decrement over time 
        _mastermind_alert_repetition_count[alert_key] = ALERT_REPEAT_COUNT
        _last_mastermind_alert_time[alert_key] = current_time # Reset time to prevent immediate re-trigger
        return

    if last_alert_time is None or (current_time - last_alert_time).total_seconds() >= ALERT_PERIOD_SECONDS:
        if repetition_count > 0:
            full_message = f"[{alert_type}] {symbol} @ {signal_price:.5f} - {message}"
            if order_id is not None:
                full_message += f" Order ID: {order_id}"
            if stop_loss > 0:
                full_message += f", SL: {stop_loss:.5f}"
            if take_profit > 0:
                full_message += f", TP: {take_profit:.5f}"
            
            logger.info(f"MasterMind Alert: {full_message}")

            # Sound Alert (MQL's PlaySound would be a direct file play)
            # In Python, this would usually involve a library like 'playsound' or a system command.
            # For now, a log indicates it.
            if ENABLE_SOUND_ALERT:
                logger.info(f"SOUND ALERT triggered for: {full_message}")
                # You would integrate a sound playing library here:
                # import playsound; playsound.playsound('path/to/alert.wav', False)

            # Email Alert
            if send_email and ENABLE_EMAIL_ALERT:
                subject = f"AI Trading Alert: {alert_type} on {symbol}"
                _send_email_alert(subject, full_message)
            
            _mastermind_alert_repetition_count[alert_key] = repetition_count - 1
            _last_mastermind_alert_time[alert_key] = current_time
        else:
            # All repetitions done, reset for next trigger cycle
            _mastermind_alert_repetition_count[alert_key] = ALERT_REPEAT_COUNT
            _last_mastermind_alert_time[alert_key] = current_time # Reset time to prevent immediate re-trigger
    else:
        # Log to indicate waiting for next repetition window
        logger.debug(f"Alert for {alert_key} on cooldown. Repetitions left: {repetition_count}")

# TheMasterMind.mq4's Alerts function includes a reset logic `if (_exitbuy==0 && _exitsell==0 && _buy==0 && _sell==0)` 
# We will assume that `use_alert=False` or specific "reset" alert_types will handle this reset,
# or a separate manager function is called when no active signals are present.
# For now, `use_alert=False` path resets.
# The following lines were problematic global code and have been removed/integrated:
# check_alerts()
# alerts.append({ ... })
# alert_context = "\n".join([...])