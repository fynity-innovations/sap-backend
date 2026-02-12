import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from django.core.cache import cache

from .models import StudentProfile
from .serializers import (
    ProfileInitiateSerializer, 
    ProfileVerifySerializer, 
    StudentProfileSerializer,
    ProcessFiltersSerializer
)
from .services.otp_service import OTPService
from .services.sms_service import SMSService
from .services.ai_service import CourseFilterAI

logger = logging.getLogger(__name__)


class ProfileInitiateView(APIView):

    def post(self, request):
        serializer = ProfileInitiateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                "success": False,
                "errors": serializer.errors
            }, status=400)

        data = serializer.validated_data
        phone = data["phone"]

        otp_service = OTPService()
        sms_service = SMSService()

        otp_code = otp_service.generate_otp(phone)
        sms_result = sms_service.send_otp(phone, otp_code)

        if not sms_result["success"]:
            return Response({
                "success": False,
                "message": "Failed to send OTP"
            }, status=500)

        # Store full academic payload in cache (not DB)
        cache_key = f"profile_data_{phone}"
        cache.set(cache_key, data, timeout=300)

        return Response({
            "success": True,
            "message": "OTP sent successfully"
        }, status=200)



class ProfileVerifyView(APIView):

    def post(self, request):
        serializer = ProfileVerifySerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                "success": False,
                "errors": serializer.errors
            }, status=400)

        phone = serializer.validated_data["phone"]
        otp = serializer.validated_data["otp"]

        # Verify OTP
        otp_service = OTPService()
        if not otp_service.verify_otp(phone, otp):
            return Response({
                "success": False,
                "message": "Invalid or expired OTP"
            }, status=400)

        # Get academic data from cache
        from django.core.cache import cache
        cache_key = f"profile_data_{phone}"
        profile_data = cache.get(cache_key)

        if not profile_data:
            return Response({
                "success": False,
                "message": "Session expired. Please try again."
            }, status=400)

        try:
            with transaction.atomic():

                # Save ONLY CONTACT INFO
                student_profile, created = StudentProfile.objects.update_or_create(
                    phone=phone,
                    defaults={
                        "name": profile_data["name"],
                        "email": profile_data["email"],
                        "is_verified": True
                    }
                )
                # Clear cache
                cache.delete(cache_key)

                return Response({
                    "success": True,
                    "profile": {
                        "name": student_profile.name,
                        "email": student_profile.email,
                        "phone": student_profile.phone,
                    },
                }, status=201)

        except Exception as e:
            logger.error(str(e))
            return Response({
                "success": False,
                "message": "Internal server error"
            }, status=500)



class ProfileDetailView(APIView):
    """Get profile details"""
    
    def get(self, request, phone):
        try:
            profile = StudentProfile.objects.get(phone=phone, is_verified=True)
            serializer = StudentProfileSerializer(profile)
            return Response({
                'success': True,
                'profile': serializer.data
            }, status=status.HTTP_200_OK)
        except StudentProfile.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Profile detail error: {str(e)}")
            return Response({
                'success': False,
                'message': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProcessFiltersView(APIView):
    """
    Process student profile using AI to generate intelligent course filters
    """

    def post(self, request):
        try:
            serializer = ProcessFiltersSerializer(data=request.data)

            if not serializer.is_valid():
                return Response(
                    {
                        'success': False,
                        'error': 'Invalid input data',
                        'details': serializer.errors
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get validated data
            profile_data = serializer.validated_data
            course_sample = profile_data.pop('courseSample')

            # Process with AI
            ai_service = CourseFilterAI()
            result = ai_service.process_student_profile(profile_data, course_sample)

            if not result['success']:
                logger.error(f"AI processing failed: {result.get('error')}")
                return Response(
                    {
                        'success': False,
                        'error': result.get('error', 'AI processing failed')
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Unexpected error in ProcessFiltersView: {str(e)}")
            return Response(
                {
                    'success': False,
                    'error': 'Server error occurred'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )