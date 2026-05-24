# backend/communication/notification_manager.py

import os
from typing import Dict, Any, Optional

# In a real application, you would use actual client libraries for these services.
# For this file, we will simulate their behavior with print statements.
# Example libraries you might use:
# - Email: smtplib, sendgrid-python
# - SMS: twilio
# - WhatsApp: twilio, a dedicated WhatsApp Business API client

class NotificationManager:
    """
    A centralized manager for handling all outgoing user notifications.
    This class can be extended to support various communication channels like
    email, SMS, WhatsApp, and more.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initializes the NotificationManager with necessary configurations.

        Args:
            config (Optional[Dict[str, Any]]): A dictionary containing API keys and settings
                                              for various notification services (e.g., SendGrid, Twilio).
        """
        self.config = config or {}
        # Extract API keys from environment variables or a config object for security
        self.sendgrid_api_key = os.getenv('SENDGRID_API_KEY', self.config.get('sendgrid_api_key'))
        self.twilio_sid = os.getenv('TWILIO_ACCOUNT_SID', self.config.get('twilio_sid'))
        self.twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN', self.config.get('twilio_auth_token'))
        self.whatsapp_from_number = os.getenv('TWILIO_WHATSAPP_NUMBER', self.config.get('whatsapp_from'))
        
        print("NotificationManager initialized.")
        if not self.sendgrid_api_key:
            print("  - Warning: SendGrid API key not found. Email notifications will be simulated.")
        if not self.twilio_sid:
            print("  - Warning: Twilio credentials not found. SMS and WhatsApp notifications will be simulated.")

    def _format_message(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Formats a message using a simple template system.

        Args:
            template_name (str): The name of the message template (e.g., 'trade_alert', 'risk_warning').
            context (Dict[str, Any]): A dictionary of values to insert into the template.

        Returns:
            str: The formatted message string.
        """
        templates = {
            'trade_alert': "PRIV Trade Alert: {action} {quantity} of {symbol} at {price}. Reason: {reason}",
            'risk_warning': "PRIV Risk Warning: {warning_type}. Current VaR at {var_level}%. Please review your portfolio.",
            'account_update': "Your account has a new update: {message}",
        }
        template = templates.get(template_name, "Notification: {message}")
        return template.format(**context)

    def send_email(self, recipient: str, subject: str, body: str):
        """
        Sends an email notification.

        Args:
            recipient (str): The recipient's email address.
            subject (str): The subject of the email.
            body (str): The HTML or text body of the email.
        """
        print(f"\n--- SIMULATING EMAIL ---")
        print(f"To: {recipient}")
        print(f"Subject: {subject}")
        print(f"Body: {body}")
        if self.sendgrid_api_key:
            print("Status: Would be sent via SendGrid.")
            # In a real implementation:
            # from sendgrid import SendGridAPIClient
            # from sendgrid.helpers.mail import Mail
            # message = Mail(...)
            # sg = SendGridAPIClient(self.sendgrid_api_key)
            # response = sg.send(message)
            # print(f"SendGrid Status Code: {response.status_code}")
        else:
            print("Status: Simulated (no API key).")
        print("------------------------")


    def send_sms(self, recipient_phone: str, body: str):
        """
        Sends an SMS notification.

        Args:
            recipient_phone (str): The recipient's phone number in E.164 format.
            body (str): The text message.
        """
        print(f"\n--- SIMULATING SMS ---")
        print(f"To: {recipient_phone}")
        print(f"Body: {body}")
        if self.twilio_sid:
            print("Status: Would be sent via Twilio SMS.")
            # In a real implementation:
            # from twilio.rest import Client
            # client = Client(self.twilio_sid, self.twilio_auth_token)
            # message = client.messages.create(...)
            # print(f"Twilio SMS SID: {message.sid}")
        else:
            print("Status: Simulated (no Twilio credentials).")
        print("--------------------")

    def send_whatsapp(self, recipient_phone: str, body: str):
        """
        Sends a WhatsApp notification.

        Args:
            recipient_phone (str): The recipient's phone number in E.164 format (prefixed with 'whatsapp:').
            body (str): The WhatsApp message.
        """
        print(f"\n--- SIMULATING WHATSAPP ---")
        print(f"To: whatsapp:{recipient_phone}")
        print(f"From: {self.whatsapp_from_number or 'simulated_whatsapp_sender'}")
        print(f"Body: {body}")
        if self.twilio_sid:
            print("Status: Would be sent via Twilio WhatsApp.")
            # In a real implementation:
            # from twilio.rest import Client
            # client = Client(self.twilio_sid, self.twilio_auth_token)
            # message = client.messages.create(...)
            # print(f"Twilio WhatsApp SID: {message.sid}")
        else:
            print("Status: Simulated (no Twilio credentials).")
        print("-------------------------")


    def send_notification(
        self,
        recipient: str,
        method: str,
        template: str,
        context: Dict[str, Any],
        subject: str = "Notification from PRIV"
    ):
        """
        Sends a notification through the specified channel.

        Args:
            recipient (str): The recipient's identifier (email address or phone number).
            method (str): The delivery method ('email', 'sms', 'whatsapp').
            template (str): The name of the message template to use.
            context (Dict[str, Any]): Data to populate the template.
            subject (str, optional): The subject line for email notifications. Defaults to "Notification from PRIV".
        """
        message_body = self._format_message(template, context)

        if method == 'email':
            self.send_email(recipient, subject, message_body)
        elif method == 'sms':
            self.send_sms(recipient, message_body)
        elif method == 'whatsapp':
            self.send_whatsapp(recipient, message_body)
        else:
            print(f"Error: Notification method '{method}' is not supported.")

# Example Usage:
if __name__ == '__main__':
    # Initialize the manager (without real keys for this demo)
    notification_mgr = NotificationManager()

    # --- Example 1: Send a trade alert via Email ---
    trade_context = {
        "action": "BUY",
        "quantity": "2.5 lots",
        "symbol": "EUR/USD",
        "price": 1.0850,
        "reason": "Sentiment Spike Detected"
    }
    notification_mgr.send_notification(
        recipient="hello@sansmercantile.com",
        method="email",
        template="trade_alert",
        context=trade_context,
        subject="PRIV Trade Execution Alert: EUR/USD"
    )

    # --- Example 2: Send a risk warning via SMS ---
    risk_context = {
        "warning_type": "High Market Volatility",
        "var_level": "3.1"
    }
    notification_mgr.send_notification(
        recipient="+27663496137",
        method="sms",
        template="risk_warning",
        context=risk_context
    )
    
    # --- Example 3: Send a general update via WhatsApp ---
    update_context = {
        "message": "Your weekly performance report is now available on the dashboard."
    }
    notification_mgr.send_notification(
        recipient="+27663496137",
        method="whatsapp",
        template="account_update",
        context=update_context
    )
