import logging
import json
from django.conf import settings
from twilio.rest import Client

logger = logging.getLogger(__name__)


class SMSService:
    """Service for sending SMS via Twilio with fallback for development"""
    
    def __init__(self):
        self.twilio_client = None
        if all([
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN,
            settings.TWILIO_PHONE_NUMBER
        ]):
            try:
                self.twilio_client = Client(
                    settings.TWILIO_ACCOUNT_SID,
                    settings.TWILIO_AUTH_TOKEN
                )
                logger.info("Twilio client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
        else:
            logger.warning("Twilio credentials not configured")
    
    def send_otp(self, phone, otp_code):
        """Send OTP via SMS"""
        message = f"Your verification code is: {otp_code}. Valid for {settings.OTP_EXPIRE_MINUTES} minutes."
        
        if self.twilio_client:
            try:
                message = self.twilio_client.messages.create(
                    body=message,
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=phone
                )
                logger.info(f"OTP sent to {phone}. SID: {message.sid}")
                return {
                    'success': True,
                    'message': 'OTP sent successfully',
                    'sid': message.sid
                }
            except Exception as e:
                logger.error(f"Failed to send SMS to {phone}: {e}")
                return {
                    'success': False,
                    'error': str(e)
                }
        else:
            # Development fallback - log to console
            logger.info(f"DEV MODE - OTP for {phone}: {otp_code}")
            return {
                'success': True,
                'message': 'OTP generated (development mode)',
                'otp_code': otp_code  # Only for development
            }
    
    def is_configured(self):
        """Check if SMS service is properly configured"""
        return self.twilio_client is not None