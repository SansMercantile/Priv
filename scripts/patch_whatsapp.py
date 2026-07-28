import re

# --- Patch 1: whatsapp_notifier.py — add a real send_generic_alert method ---
p1 = "/home/mpeti/workspace/constellation/priv/backend/communication/whatsapp_notifier.py"
with open(p1, "r", encoding="utf-8") as f:
    content = f.read()

marker = '''# Example Usage (for testing WhatsAppNotifier in isolation)
async def main_whatsapp_notifier_test():'''

new_method = '''    async def send_generic_alert(self, recipient_number: str, message: str) -> bool:
        """
        Sends a plain-text alert to WhatsApp via the real Meta WhatsApp Cloud
        API. Added because send_trade_opportunity() only handles the
        structured trade-opportunity format; critical alerts (legal,
        compliance, risk) need a generic text sender instead.

        Requires WHATSAPP_PHONE_NUMBER_ID and WHATSAPP_ACCESS_TOKEN to be set
        to real values (from the Meta WhatsApp Business Platform / Cloud API
        dashboard) - falls back to a clearly-labeled mock and returns False
        if they are still placeholders, rather than silently no-op'ing.
        """
        if self.phone_number_id.startswith("your_") or self.access_token.startswith("your_"):
            logger.warning(
                f"Priv WhatsApp: send_generic_alert MOCKED for {recipient_number} "
                f"(WHATSAPP_PHONE_NUMBER_ID / WHATSAPP_ACCESS_TOKEN not configured). "
                f"Message NOT delivered: {message[:120]}"
            )
            return False

        try:
            import httpx
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }
            payload = {
                "messaging_product": "whatsapp",
                "to": recipient_number,
                "type": "text",
                "text": {"body": message},
            }
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"https://graph.facebook.com/v19.0/{self.phone_number_id}/messages",
                    headers=headers,
                    json=payload,
                )
            if response.status_code == 200:
                logger.info(f"Priv WhatsApp: Alert successfully sent to {recipient_number}.")
                return True
            logger.error(
                f"Priv WhatsApp: Failed to send alert. Status: {response.status_code}, "
                f"Response: {response.text}"
            )
            return False
        except Exception as e:
            logger.error(f"Priv WhatsApp: Error sending alert via API: {e}", exc_info=True)
            return False


''' + marker

if marker not in content:
    raise SystemExit("PATCH1_MARKER_NOT_FOUND")
if "send_generic_alert" in content:
    print("PATCH1_ALREADY_APPLIED_SKIPPING")
else:
    content = content.replace(marker, new_method, 1)
    with open(p1, "w", encoding="utf-8") as f:
        f.write(content)
    print("PATCH1_OK")

# --- Patch 2: priv_legal_agent.py — real number + actually call the sender ---
p2 = "/home/mpeti/workspace/constellation/priv/backend/multi_agent/priv_legal_agent.py"
with open(p2, "r", encoding="utf-8") as f:
    content2 = f.read()

old_block = '''        if severity == "CRITICAL":
            critical_alert_recipient = getattr(settings, 'CRITICAL_ALERT_WHATSAPP_NUMBER', '+1234567890')
            try:
                whatsapp_message = f"\\U0001f6a8 CRITICAL LEGAL ALERT! \\U0001f6a8\\nType: {alert_type}\\nMessage: {message}\\nDetails: {details}"
                # You might need a generic send_alert method in WhatsAppNotifier
                # For now, we'll log its conceptual sending.
                # await self.whatsapp_notifier.send_generic_alert(critical_alert_recipient, whatsapp_message)
                logger.info(f"Legal Agent: Conceptually sent critical WhatsApp alert to {critical_alert_recipient}.")
            except Exception as e:
                logger.error(f"Legal Agent: Failed to send WhatsApp alert: {e}", exc_info=True)'''

new_block = '''        if severity == "CRITICAL":
            critical_alert_recipient = getattr(settings, 'CRITICAL_ALERT_WHATSAPP_NUMBER', '+27645149389')
            try:
                whatsapp_message = f"\\U0001f6a8 CRITICAL LEGAL ALERT! \\U0001f6a8\\nType: {alert_type}\\nMessage: {message}\\nDetails: {details}"
                sent = await self.whatsapp_notifier.send_generic_alert(critical_alert_recipient, whatsapp_message)
                if sent:
                    logger.info(f"Legal Agent: Critical WhatsApp alert sent to {critical_alert_recipient}.")
                else:
                    logger.warning(f"Legal Agent: Critical WhatsApp alert to {critical_alert_recipient} was NOT delivered (see WhatsAppNotifier log).")
            except Exception as e:
                logger.error(f"Legal Agent: Failed to send WhatsApp alert: {e}", exc_info=True)'''

if old_block not in content2:
    raise SystemExit("PATCH2_MARKER_NOT_FOUND")
content2 = content2.replace(old_block, new_block, 1)
content2 = content2.replace(
    '''    if not hasattr(settings, 'CRITICAL_ALERT_WHATSAPP_NUMBER'):
        settings.CRITICAL_ALERT_WHATSAPP_NUMBER = "+1234567890" # Dummy number''',
    '''    if not hasattr(settings, 'CRITICAL_ALERT_WHATSAPP_NUMBER'):
        settings.CRITICAL_ALERT_WHATSAPP_NUMBER = "+27645149389"'''
)
with open(p2, "w", encoding="utf-8") as f:
    f.write(content2)
print("PATCH2_OK")
