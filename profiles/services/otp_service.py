import logging
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from ..models import PhoneOTP

logger = logging.getLogger(__name__)


class OTPService:
    """OTP Service using Database only (No Redis)"""

    def generate_otp(self, phone, expire_minutes=None):
        if expire_minutes is None:
            expire_minutes = settings.OTP_EXPIRE_MINUTES

        # Mark old OTPs as used
        PhoneOTP.objects.filter(phone=phone, is_used=False).update(is_used=True)

        # Generate 6 digit OTP
        import random
        otp_code = ''.join(random.choices('0123456789', k=6))

        expires_at = timezone.now() + timedelta(minutes=expire_minutes)

        PhoneOTP.objects.create(
            phone=phone.strip(),
            otp=otp_code,
            expires_at=expires_at
        )

        return otp_code

    def verify_otp(self, phone, otp_code):
        phone = phone.strip()

        try:
            otp_obj = PhoneOTP.objects.filter(
                phone=phone,
                otp=otp_code,
                is_used=False
            ).latest('created_at')

            if otp_obj.expires_at > timezone.now():
                otp_obj.is_used = True
                otp_obj.save()
                return True

            return False

        except PhoneOTP.DoesNotExist:
            return False
