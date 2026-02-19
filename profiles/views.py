import logging
from datetime import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from django.core.cache import cache
from django.conf import settings

from .models import StudentProfile
from .serializers import (
    ProfileInitiateSerializer,
    ProfileVerifySerializer,
    StudentProfileSerializer,
    ProcessFiltersSerializer,
    CourseSuggestionSerializer
)
from .services.otp_service import OTPService
from .services.sms_service import SMSService
from .services.ai_service import CourseFilterAI
from .services.whatsapp_service import WhatsAppService


logger = logging.getLogger(__name__)


class ProfileInitiateView(APIView):
    """
    Initiate profile creation and send OTP
    """

    def post(self, request):
        serializer = ProfileInitiateSerializer(data=request.data)

        if not serializer.is_valid():
            logger.error(f"Validation errors: {serializer.errors}")
            return Response({
                "success": False,
                "errors": serializer.errors
            }, status=400)

        data = serializer.validated_data
        phone = data["phone"]

        logger.info(f"Initiating profile for phone: {phone}")

        otp_service = OTPService()
        otp_code = otp_service.generate_otp(phone)

        sms_service = SMSService()
        sms_result = sms_service.send_otp(phone, otp_code)

        # Try WhatsApp first
        # whatsapp_service = WhatsAppService()
        # whatsapp_result = whatsapp_service.send_otp(phone, otp_code)
        # logger.info(f"WhatsApp result: {whatsapp_result}")

        # if whatsapp_result["success"]:
        #     logger.info("OTP sent via WhatsApp")
        # else:
        #     logger.warning("WhatsApp failed. Falling back to SMS")
        #     sms_service = SMSService()
        #     sms_result = sms_service.send_otp(phone, otp_code)
        #
        #     if not sms_result["success"]:
        #         logger.error("Both WhatsApp and SMS failed")
        #         return Response({
        #             "success": False,
        #             "message": "Failed to send OTP"
        #         }, status=500)

        # Store full data in cache
        cache_key = f"profile_data_{phone}"
        cache.set(cache_key, data, timeout=600)  # 10 minutes
        logger.info(f"Stored profile data in cache: {cache_key}")

        return Response({
            "success": True,
            "message": "OTP sent successfully"
        }, status=200)


class ProfileVerifyView(APIView):
    """
    Verify OTP and create/update profile
    """

    def post(self, request):
        serializer = ProfileVerifySerializer(data=request.data)

        if not serializer.is_valid():
            logger.error(f"Validation errors: {serializer.errors}")
            return Response({
                "success": False,
                "errors": serializer.errors
            }, status=400)

        phone = serializer.validated_data["phone"]
        otp = serializer.validated_data["otp"]

        logger.info(f"Verifying OTP for phone: {phone}")

        # Verify OTP
        otp_service = OTPService()
        if not otp_service.verify_otp(phone, otp):
            logger.warning(f"Invalid OTP for {phone}")
            return Response({
                "success": False,
                "message": "Invalid or expired OTP"
            }, status=400)

        # Get data from cache
        cache_key = f"profile_data_{phone}"
        profile_data = cache.get(cache_key)

        if not profile_data:
            logger.error(f"No profile data found in cache for {phone}")
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

                logger.info(f"Profile {'created' if created else 'updated'} for {phone}")

                # Clear cache
                cache.delete(cache_key)
                logger.info(f"Cleared cache: {cache_key}")

                return Response({
                    "success": True,
                    "profile": {
                        "name": student_profile.name,
                        "email": student_profile.email,
                        "phone": student_profile.phone,
                    },
                }, status=201)

        except Exception as e:
            logger.error(f"Error creating profile: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
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
                logger.error(f"Filter validation errors: {serializer.errors}")
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

            logger.info(f"Processing filters for profile: {profile_data}")

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

            logger.info(f"Successfully generated filters: {result['filters']}")
            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Unexpected error in ProcessFiltersView: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {
                    'success': False,
                    'error': 'Server error occurred'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CourseSuggestionView(APIView):
    """
    Get AI-powered course suggestions based on search query
    """

    def post(self, request):
        try:
            serializer = CourseSuggestionSerializer(data=request.data)

            if not serializer.is_valid():
                return Response(
                    {
                        'success': False,
                        'error': 'Invalid input data',
                        'details': serializer.errors
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            query = serializer.validated_data.get('query', '').strip()
            limit = serializer.validated_data.get('limit', 10)
            phone = serializer.validated_data.get('phone')

            if not query:
                return Response(
                    {
                        'success': False,
                        'error': 'Query is required',
                        'suggestions': []
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get course sample
            from .models import Course
            course_sample = list(
                Course.objects.all().values(
                    'course_id',
                    'course_title',
                    'university_name',
                    'country_name',
                    'level',
                    'duration',
                    'tuition_fees',
                    'currency',
                    'intake'
                )
            )[:100]

            # Get user profile (optional)
            user_profile_data = None
            if phone:
                try:
                    user_profile = StudentProfile.objects.get(
                        phone=phone,
                        is_verified=True
                    )
                    user_profile_data = {
                        'countries': user_profile.countries or [],
                        'degree': user_profile.degree or '',
                        'fields': user_profile.fields or [],
                        'budget': user_profile.budget or [0],
                    }
                except StudentProfile.DoesNotExist:
                    logger.warning(f"User profile not found for {phone}")
                    user_profile_data = None

            # Get AI suggestions
            ai_service = CourseFilterAI()
            result = ai_service.get_course_suggestions(
                query=query,
                course_sample=course_sample,
                limit=limit,
                user_profile=user_profile_data
            )

            if not result.get('success'):
                logger.error(f"AI suggestions failed for query '{query}': {result.get('error')}")
                return Response(
                    {
                        'success': False,
                        'error': result.get('error', 'AI suggestions failed'),
                        'suggestions': []
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            logger.info(
                f"AI suggestions successful for query '{query}': {len(result.get('suggestions', []))} suggestions")
            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Unexpected error in CourseSuggestionView: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {
                    'success': False,
                    'error': 'Server error occurred',
                    'suggestions': []
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CourseSelectionView(APIView):
    """
    Handle course selection from AI suggestions
    """

    def post(self, request):
        try:
            serializer = CourseSuggestionSerializer(data=request.data)

            if not serializer.is_valid():
                return Response(
                    {
                        'success': False,
                        'error': 'Invalid input data',
                        'details': serializer.errors
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            course_id = serializer.validated_data.get('course_id')
            phone = serializer.validated_data.get('phone')

            if not course_id:
                return Response(
                    {
                        'success': False,
                        'error': 'Course ID is required',
                        'selected_course': None
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get user profile
            try:
                user_profile = StudentProfile.objects.get(phone=phone, is_verified=True)
            except StudentProfile.DoesNotExist:
                logger.warning(f"User profile not found for {phone}")
                return Response(
                    {
                        'success': False,
                        'error': 'User profile not found',
                        'selected_course': None
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            # Get course details
            try:
                from .models import Course
                selected_course = Course.objects.get(course_id=course_id)

                # Prepare selected course data
                selected_course_data = {
                    'course_id': selected_course.course_id,
                    'course_title': selected_course.course_title,
                    'university_name': selected_course.university_name,
                    'country_name': selected_course.country_name,
                    'level': selected_course.level,
                    'duration': selected_course.duration,
                    'tuition_fees': selected_course.tuition_fees,
                    'currency': selected_course.currency,
                    'intake': selected_course.intake,
                    'selected_at': timezone.now().isoformat(),
                    'user_phone': phone
                }

                logger.info(f"User {phone} selected course: {selected_course.course_title}")

                return Response({
                    'success': True,
                    'message': 'Course selected successfully',
                    'selected_course': selected_course_data
                }, status=status.HTTP_200_OK)

            except Course.DoesNotExist:
                logger.error(f"Course not found with ID: {course_id}")
                return Response(
                    {
                        'success': False,
                        'error': 'Course not found',
                        'selected_course': None
                    },
                    status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.error(f"Error in CourseSelectionView: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {
                    'success': False,
                    'error': 'Server error occurred',
                    'selected_course': None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AICourseRecommendationView(APIView):
    """
    Get AI-powered course recommendations based on user profile
    """

    def post(self, request):
        try:
            phone = request.data.get('phone')

            if not phone:
                return Response(
                    {
                        'success': False,
                        'error': 'Phone number is required',
                        'recommendations': []
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get user profile
            try:
                user_profile = StudentProfile.objects.get(phone=phone, is_verified=True)
            except StudentProfile.DoesNotExist:
                logger.warning(f"User profile not found for {phone}")
                return Response(
                    {
                        'success': False,
                        'error': 'User profile not found',
                        'recommendations': []
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            # Get course sample
            from .models import Course
            course_sample = list(Course.objects.all().values(
                'course_id', 'course_title', 'university_name', 'country_name',
                'level', 'duration', 'tuition_fees', 'currency', 'intake'
            ))[:100]

            # Get AI recommendations
            ai_service = CourseFilterAI()
            result = ai_service.get_ai_course_recommendations(
                user_profile.__dict__,
                course_sample
            )

            if not result['success']:
                logger.error(f"AI recommendations failed for {phone}: {result.get('error')}")
                return Response(
                    {
                        'success': False,
                        'error': result.get('error', 'AI recommendations failed'),
                        'recommendations': []
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            logger.info(
                f"AI recommendations successful for {phone}: {len(result.get('recommendations', []))} recommendations")
            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in AICourseRecommendationView: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {
                    'success': False,
                    'error': 'Server error occurred',
                    'recommendations': []
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ChatbotQueryView(APIView):
    """
    Handle chatbot queries with AI
    """

    def post(self, request):
        try:
            message = request.data.get('message', '')
            context = request.data.get('context', {})
            history = request.data.get('conversationHistory', [])

            if not message:
                return Response({
                    'success': False,
                    'error': 'Message is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            logger.info(f"Chatbot query: {message[:50]}...")

            # Use OpenAI to generate response
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)

            # Build context string
            countries = context.get('countries', [])
            universities = context.get('universities', [])
            courses = context.get('courses', [])
            user_name = context.get('userName', 'there')

            # Extract sample data
            country_names = [c.get('country_name', '') for c in countries[:10] if c.get('country_name')]
            course_titles = [c.get('course_title', '')[:60] for c in courses[:5] if c.get('course_title')]
            uni_names = [u.get('university_name', '') for u in universities[:5] if u.get('university_name')]

            system_prompt = f"""You are a helpful study abroad assistant chatbot. You help students find courses, universities, and countries to study in.

Available Data Context:
- {len(countries)} countries available: {', '.join(country_names)}
- {len(universities)} universities available including: {', '.join(uni_names)}
- {len(courses)} courses available

Sample Courses:
{chr(10).join([f"- {title}" for title in course_titles])}

User's name: {user_name}

Your Role:
1. Be friendly, warm, and conversational
2. Give specific recommendations from the data
3. Keep responses concise (under 150 words)
4. Use emojis sparingly 
5. If asked about finding courses, suggest the AI Profile Evaluator
6. Answer general questions about studying abroad (applications, visas, costs, scholarships)
7. Be encouraging and supportive

Important: Base your answers on the data context provided above."""

            # Build conversation messages
            messages = [
                {"role": "system", "content": system_prompt}
            ]

            # Add conversation history (last 4 messages)
            for msg in history[-4:]:
                role = msg.get('role', 'user')
                if role == 'system':
                    role = 'assistant'
                messages.append({
                    "role": role,
                    "content": msg.get('content', '')
                })

            # Add current message
            messages.append({
                "role": "user",
                "content": message
            })

            logger.info(f"Sending {len(messages)} messages to OpenAI")

            # Get AI response
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
                max_tokens=300
            )

            ai_response = response.choices[0].message.content.strip()
            logger.info(f"AI response: {ai_response[:100]}...")

            # Check if we should suggest filters
            suggest_keywords = [
                'find course', 'recommend course', 'which course', 'suggest course',
                'want to study', 'looking for', 'search for', 'help me find',
                'show me course', 'best course'
            ]

            suggest_filters = any(keyword in message.lower() for keyword in suggest_keywords)

            return Response({
                'success': True,
                'response': ai_response,
                'suggestFilters': suggest_filters
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Chatbot error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return Response({
                'success': False,
                'error': 'Failed to process message'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)