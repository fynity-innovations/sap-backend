import logging
from django.conf import settings
from twilio.rest import Client

logger = logging.getLogger(__name__)


class WhatsAppService:
    """
    WhatsApp OTP service using Twilio
    """

    def __init__(self):
        self.client = None

        if all([
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN,
            settings.TWILIO_WHATSAPP_NUMBER
        ]):
            try:
                self.client = Client(
                    settings.TWILIO_ACCOUNT_SID,
                    settings.TWILIO_AUTH_TOKEN
                )
                logger.info("WhatsApp client initialized")
            except Exception as e:
                logger.error(f"WhatsApp init failed: {e}")
        else:
            logger.warning("WhatsApp credentials missing")

    def send_otp(self, phone, otp_code):
        message_body = (
            f"Your verification code is: {otp_code}\n"
            f"Valid for {settings.OTP_EXPIRE_MINUTES} minutes."
        )

        if self.client:
            try:
                message = self.client.messages.create(
                    body=message_body,
                    # from_=f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}",
                    from_="whatsapp:+14155238886",
                    to=f"whatsapp:{phone}"
                )

                logger.info(f"WhatsApp OTP sent to {phone}. SID: {message.sid}")

                return {
                    "success": True,
                    "sid": message.sid
                }

            except Exception as e:
                logger.error(f"WhatsApp send failed: {e}")
                return {
                    "success": False,
                    "error": str(e)
                }

        else:
            logger.info(f"DEV MODE WhatsApp OTP for {phone}: {otp_code}")
            return {
                "success": True,
                "otp_code": otp_code
            }

    def is_configured(self):
        return self.client is not None
