import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import RegexValidator, EmailValidator, MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.conf import settings


class PhoneOTP(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(max_length=20)
    otp = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'phone_otps'
        indexes = [
            models.Index(fields=['phone']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"{self.phone} - {self.otp}"

    def is_expired(self):
        return timezone.now() > self.expires_at

    @classmethod
    def generate_otp(cls):
        import random
        return ''.join(random.choices('0123456789', k=6))

    @classmethod
    def create_otp(cls, phone, expire_minutes=None):
        if expire_minutes is None:
            expire_minutes = settings.OTP_EXPIRE_MINUTES

        # Mark existing OTPs as used
        cls.objects.filter(phone=phone, is_used=False).update(is_used=True)

        otp_code = cls.generate_otp()
        from datetime import timedelta
        expires_at = timezone.now() + timedelta(minutes=expire_minutes)

        return cls.objects.create(
            phone=phone,
            otp=otp_code,
            expires_at=expires_at
        )


class StudentProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=255)
    email = models.EmailField()

    phone = models.CharField(
        max_length=20,
        unique=True,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone number must be entered in format '+999999999'."
        )]
    )


    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "student_profiles"
        indexes = [
            models.Index(fields=["phone"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.phone})"

