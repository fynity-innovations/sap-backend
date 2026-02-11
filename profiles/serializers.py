from rest_framework import serializers
from decimal import Decimal
from django.core.validators import RegexValidator
from .models import StudentProfile, PhoneOTP


class ProfileInitiateSerializer(serializers.Serializer):
    """Serializer for profile initiation and OTP sending"""
    name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    phone = serializers.CharField(
        max_length=20,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )]
    )

    def validate_phone(self, value):
        return value.strip()
    
    def validate_email(self, value):
        """Validate email format"""
        return value.lower().strip()


class ProfileVerifySerializer(serializers.Serializer):
    """Serializer for OTP verification and profile creation"""
    phone = serializers.CharField(
        max_length=20,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )]
    )
    otp = serializers.CharField(
        max_length=6,
        min_length=6,
        error_messages={
            'min_length': 'OTP must be exactly 6 digits.',
            'max_length': 'OTP must be exactly 6 digits.'
        }
    )
    
    def validate_otp(self, value):
        """Validate OTP format"""
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain only digits.")
        return value


class StudentProfileSerializer(serializers.ModelSerializer):
    """Serializer for StudentProfile data display"""
    
    class Meta:
        model = StudentProfile
        fields = [
            'id', 'name', 'email', 'phone',
            'is_verified', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_verified', 'created_at', 'updated_at']


class ProfileCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating StudentProfile"""
    
    class Meta:
        model = StudentProfile
        exclude = ['id', 'is_verified', 'created_at', 'updated_at']

    def validate_phone(self, value):
        return value.strip()


class ProfileEvaluationSerializer(serializers.Serializer):
    """Serializer for AI evaluation results"""
    score = serializers.IntegerField(min_value=0, max_value=100)
    best_countries = serializers.ListField(child=serializers.CharField())
    recommended_programs = serializers.ListField(child=serializers.CharField())
    improvement_tips = serializers.ListField(child=serializers.CharField())
    assessment_summary = serializers.CharField(allow_blank=True)