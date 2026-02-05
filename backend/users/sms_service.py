"""
SMS Service for sending OTP via Twilio.
Falls back to console logging in development mode.
"""

from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Placeholder values that indicate Twilio is not configured
PLACEHOLDER_VALUES = {"", "your_sid", "your_token", "your_phone", "changeme", "xxx"}


def _is_twilio_configured() -> bool:
    """Check if Twilio is properly configured with real credentials."""
    sid = getattr(settings, "TWILIO_ACCOUNT_SID", "") or ""
    token = getattr(settings, "TWILIO_AUTH_TOKEN", "") or ""
    phone = getattr(settings, "TWILIO_PHONE_NUMBER", "") or ""

    # Check if any value is empty or a known placeholder
    if sid.lower() in PLACEHOLDER_VALUES:
        return False
    if token.lower() in PLACEHOLDER_VALUES:
        return False
    if phone.lower() in PLACEHOLDER_VALUES:
        return False

    # Valid Twilio SIDs start with "AC"
    if not sid.startswith("AC"):
        return False

    return True


def send_otp_sms(phone_number: str, otp: str) -> bool:
    """
    Send OTP via SMS using Twilio.
    Falls back to console logging if Twilio is not configured.
    """
    if not _is_twilio_configured():
        # Development mode: log OTP to console
        logger.warning(f"[DEV MODE] SMS not configured. OTP for {phone_number}: {otp}")
        print(f"\n{'='*50}")
        print(f"[DEV MODE] OTP for {phone_number}: {otp}")
        print(f"{'='*50}\n", flush=True)
        return True

    try:
        from twilio.rest import Client

        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=f"Your verification code is: {otp}. Valid for 5 minutes.",
            from_=settings.TWILIO_PHONE_NUMBER,
            to=str(phone_number),
        )
        logger.info(f"SMS sent to {phone_number}, SID: {message.sid}")
        return message.sid is not None
    except Exception as e:
        logger.error(f"Failed to send SMS to {phone_number}: {e}")
        return False
