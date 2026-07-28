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
    lines = f.readlines()

out = []
i = 0
found_default = False
found_call = False
found_dummy = False
while i < len(lines):
    line = lines[i]
    if "getattr(settings, 'CRITICAL_ALERT_WHATSAPP_NUMBER'" in line and "+1234567890" in line:
        line = line.replace("+1234567890", "+27645149389")
        found_default = True
        out.append(line)
        i += 1
        continue
    if "You might need a generic send_alert method" in line:
        indent = line[: len(line) - len(line.lstrip())]
        out.append(indent + "sent = await self.whatsapp_notifier.send_generic_alert(critical_alert_recipient, whatsapp_message)\n")
        out.append(indent + "if sent:\n")
        out.append(indent + "    logger.info(f\"Legal Agent: Critical WhatsApp alert sent to {critical_alert_recipient}.\")\n")
        out.append(indent + "else:\n")
        out.append(indent + "    logger.warning(f\"Legal Agent: Critical WhatsApp alert to {critical_alert_recipient} was NOT delivered (see WhatsAppNotifier log).\")\n")
        found_call = True
        i += 1
        while i < len(lines) and (
            lines[i].strip().startswith("#")
            or "Conceptually sent critical WhatsApp alert" in lines[i]
        ):
            i += 1
        continue
    if 'settings.CRITICAL_ALERT_WHATSAPP_NUMBER = "+1234567890"' in line:
        line = line.split("#")[0].rstrip() + "\n"
        line = line.replace("+1234567890", "+27645149389")
        found_dummy = True
        out.append(line)
        i += 1
        continue
    out.append(line)
    i += 1

if not (found_default and found_call and found_dummy):
    raise SystemExit("PATCH2_INCOMPLETE default=%s call=%s dummy=%s" % (found_default, found_call, found_dummy))

with open(p2, "w", encoding="utf-8") as f:
    f.writelines(out)
print("PATCH2_OK")
