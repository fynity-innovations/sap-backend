# profiles/serializers.py
from rest_framework import serializers
from decimal import Decimal
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from .models import StudentProfile, PhoneOTP


class ProfileInitiateSerializer(serializers.Serializer):
    """Serializer for profile initiation and OTP sending"""
    name = serializers.CharField(
        max_length=255,
        validators=[
            RegexValidator(
                regex=r'^[A-Za-z\s\'\-\.]+$',
                message="Name can only contain letters, spaces, hyphens, dots, and apostrophes."
            )
        ]
    )
    email = serializers.EmailField(
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                message="Please enter a valid email address."
            )
        ]
    )
    phone = serializers.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ]
    )

    def validate_name(self, value):
        """Validate name format"""
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters long.")
        return value.title()

    def validate_phone(self, value):
        """Validate phone format"""
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Phone number is required.")
        return value

    def validate_email(self, value):
        """Validate email format"""
        value = value.lower().strip()
        if not value:
            raise serializers.ValidationError("Email is required.")
        if '@' not in value:
            raise serializers.ValidationError("Email must contain '@' symbol.")
        if value.count('@') != 1:
            raise serializers.ValidationError("Email must contain exactly one '@' symbol.")
        return value


class ProfileVerifySerializer(serializers.Serializer):
    """Serializer for OTP verification and profile creation"""
    phone = serializers.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ]
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


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating StudentProfile"""

    class Meta:
        model = StudentProfile
        fields = ['name', 'email']
        extra_kwargs = {
            'name': {'required': False},
            'email': {'required': False}
        }


class ProfileEvaluationSerializer(serializers.Serializer):
    """Serializer for AI evaluation results"""
    score = serializers.IntegerField(
        min_value=0,
        max_value=100,
        error_messages={
            'min_value': 'Score must be between 0 and 100.',
            'max_value': 'Score must be between 0 and 100.'
        }
    )
    best_countries = serializers.ListField(
        child=serializers.CharField(),
        error_messages={
            'not_a_list': 'Best countries must be a list.'
        }
    )
    recommended_programs = serializers.ListField(
        child=serializers.CharField(),
        error_messages={
            'not_a_list': 'Recommended programs must be a list.'
        }
    )
    improvement_tips = serializers.ListField(
        child=serializers.CharField(),
        error_messages={
            'not_a_list': 'Improvement tips must be a list.'
        }
    )
    assessment_summary = serializers.CharField(
        allow_blank=True,
        error_messages={
            'invalid': 'Assessment summary must be a string.'
        }
    )
    confidence_level = serializers.ChoiceField(
        choices=['low', 'medium', 'high'],
        default='medium',
        error_messages={
            'invalid_choice': 'Confidence level must be one of: low, medium, high.'
        }
    )
    evaluated_at = serializers.DateTimeField(read_only=True)


class ProcessFiltersSerializer(serializers.Serializer):
    """Serializer for processing student profile with AI"""

    countries = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=True,
        error_messages={
            'required': 'Countries list is required.',
            'not_a_list': 'Countries must be a list.'
        }
    )
    degree = serializers.CharField(
        max_length=100,
        required=True,
        error_messages={
            'required': 'Target degree is required.',
            'blank': 'Target degree cannot be blank.'
        }
    )
    fields = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=True,
        error_messages={
            'required': 'Fields of interest list is required.',
            'not_a_list': 'Fields must be a list.'
        }
    )
    intakes = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=True,
        error_messages={
            'required': 'Preferred intakes list is required.',
            'not_a_list': 'Intakes must be a list.'
        }
    )
    completedDegree = serializers.CharField(
        max_length=100,
        required=True,
        error_messages={
            'required': 'Completed degree is required.',
            'blank': 'Completed degree cannot be blank.'
        }
    )
    cgpa = serializers.FloatField(
        required=True,
        min_value=0.0,
        max_value=10.0,
        error_messages={
            'required': 'CGPA is required.',
            'min_value': 'CGPA cannot be negative.',
            'max_value': 'CGPA cannot exceed 10.0.'
        }
    )
    gradYear = serializers.CharField(
        max_length=20,
        required=True,
        error_messages={
            'required': 'Graduation year is required.',
            'blank': 'Graduation year cannot be blank.'
        }
    )
    budget = serializers.ListField(
        child=serializers.IntegerField(min_value=0, max_value=1000000),
        required=True,
        error_messages={
            'required': 'Budget list is required.',
            'not_a_list': 'Budget must be a list.'
        }
    )
    courseSample = serializers.ListField(
        child=serializers.DictField(),
        required=True,
        error_messages={
            'required': 'Course sample is required.',
            'not_a_list': 'Course sample must be a list.'
        }
    )
    workExperience = serializers.IntegerField(
        required=False,
        min_value=0,
        max_value=50,
        default=0,
        error_messages={
            'min_value': 'Work experience cannot be negative.',
            'max_value': 'Work experience cannot exceed 50 years.'
        }
    )
    backlogs = serializers.IntegerField(
        required=False,
        min_value=0,
        max_value=10,
        default=0,
        error_messages={
            'min_value': 'Backlogs cannot be negative.',
            'max_value': 'Backlogs cannot exceed 10.'
        }
    )
    englishProficiency = serializers.ChoiceField(
        choices=['basic', 'intermediate', 'advanced', 'native'],
        default='intermediate',
        required=False,
        error_messages={
            'invalid_choice': 'English proficiency must be one of: basic, intermediate, advanced, native.'
        }
    )
    targetCountries = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        error_messages={
            'not_a_list': 'Target countries must be a list.'
        }
    )
    preferredUniversities = serializers.ListField(
        child=serializers.CharField(max_length=200),
        required=False,
        error_messages={
            'not_a_list': 'Preferred universities must be a list.'
        }
    )
    scholarshipRequired = serializers.BooleanField(
        required=False,
        default=False,
        error_messages={
            'invalid': 'Scholarship required must be a boolean.'
        }
    )
    visaAssistance = serializers.BooleanField(
        required=False,
        default=False,
        error_messages={
            'invalid': 'Visa assistance required must be a boolean.'
        }
    )

    def validate_countries(self, value):
        """Validate countries list"""
        if not value:
            raise serializers.ValidationError("Countries list cannot be empty.")
        if len(value) > 10:
            raise serializers.ValidationError("Cannot select more than 10 countries.")
        return [country.strip().title() for country in value if country.strip()]

    def validate_fields(self, value):
        """Validate fields of interest list"""
        if not value:
            raise serializers.ValidationError("Fields list cannot be empty.")
        if len(value) > 5:
            raise serializers.ValidationError("Cannot select more than 5 fields of interest.")
        return [field.strip().title() for field in value if field.strip()]

    def validate_intakes(self, value):
        """Validate intakes list"""
        if not value:
            raise serializers.ValidationError("Intakes list cannot be empty.")
        if len(value) > 5:
            raise serializers.ValidationError("Cannot select more than 5 preferred intakes.")
        return [intake.strip().title() for intake in value if intake.strip()]

    def validate_budget(self, value):
        """Validate budget list"""
        if not value:
            raise serializers.ValidationError("Budget list cannot be empty.")
        if len(value) > 3:
            raise serializers.ValidationError("Cannot specify more than 3 budget options.")
        return [budget for budget in value if budget >= 0]

    def validate_courseSample(self, value):
        """Validate course sample list"""
        if not value:
            raise serializers.ValidationError("Course sample cannot be empty.")
        if len(value) > 100:
            raise serializers.ValidationError("Course sample cannot exceed 100 courses.")
        return value

    def validate_cgpa(self, value):
        """Validate CGPA with proper decimal places"""
        if value < 0 or value > 10:
            raise serializers.ValidationError("CGPA must be between 0 and 10.")
        # Round to 2 decimal places
        return round(value, 2)

    def validate_gradYear(self, value):
        """Validate graduation year"""
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Graduation year is required.")
        try:
            year = int(value)
            current_year = 2024
            if year < current_year - 50 or year > current_year + 10:
                raise serializers.ValidationError(
                    f"Graduation year must be between {current_year - 50} and {current_year + 10}.")
            return str(year)
        except ValueError:
            raise serializers.ValidationError("Graduation year must be a valid year.")

    def validate_workExperience(self, value):
        """Validate work experience in years"""
        if value < 0:
            raise serializers.ValidationError("Work experience cannot be negative.")
        return value

    def validate_backlogs(self, value):
        """Validate number of backlogs"""
        if value < 0:
            raise serializers.ValidationError("Backlogs cannot be negative.")
        return value

    def validate_targetCountries(self, value):
        """Validate target countries list"""
        if value:
            return [country.strip().title() for country in value if country.strip()]
        return []

    def validate_preferredUniversities(self, value):
        """Validate preferred universities list"""
        if value:
            return [uni.strip().title() for uni in value if uni.strip()]
        return []


class CourseSuggestionSerializer(serializers.Serializer):
    """Serializer for course suggestions"""
    query = serializers.CharField(
        max_length=100,
        required=True,
        error_messages={
            'required': 'Search query is required.',
            'blank': 'Search query cannot be blank.',
            'max_length': 'Query cannot exceed 100 characters.'
        }
    )
    phone = serializers.CharField(
        max_length=20,
        required=False,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ]
    )
    limit = serializers.IntegerField(
        default=10,
        min_value=1,
        max_value=20,
        error_messages={
            'min_value': 'Limit must be at least 1.',
            'max_value': 'Limit cannot exceed 20.'
        }
    )
    userPreferences = serializers.JSONField(
        required=False,
        help_text="User preferences for personalized suggestions"
    )

    def validate_query(self, value):
        """Validate search query"""
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("Search query must be at least 2 characters long.")
        return value

    def validate_phone(self, value):
        """Validate phone number"""
        if value:
            return value.strip()
        return None


class CourseSelectionSerializer(serializers.Serializer):
    """Serializer for course selection from suggestions"""
    course_id = serializers.CharField(
        max_length=100,
        required=True,
        error_messages={
            'required': 'Course ID is required.',
            'blank': 'Course ID cannot be blank.',
            'max_length': 'Course ID cannot exceed 100 characters.'
        }
    )
    phone = serializers.CharField(
        max_length=20,
        required=False,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ]
    )
    selected_at = serializers.DateTimeField(read_only=True)
    user_feedback = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
        help_text="User feedback on the selection"
    )

    def validate_course_id(self, value):
        """Validate course ID format"""
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Course ID is required.")
        # Basic UUID validation
        import re
        uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I)
        if not uuid_pattern.match(value):
            raise serializers.ValidationError("Invalid course ID format.")
        return value


class CourseRecommendationSerializer(serializers.Serializer):
    """Serializer for AI course recommendations"""
    phone = serializers.CharField(
        max_length=20,
        required=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ]
    )
    recommendationType = serializers.ChoiceField(
        choices=['ai_specialized', 'general', 'personalized'],
        default='ai_specialized',
        error_messages={
            'invalid_choice': 'Recommendation type must be one of: ai_specialized, general, personalized.'
        }
    )
    preferences = serializers.JSONField(
        required=False,
        help_text="Additional preferences for recommendations"
    )

    def validate_phone(self, value):
        """Validate phone number"""
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Phone number is required.")
        return value


class ProfileSearchSerializer(serializers.Serializer):
    """Serializer for searching student profiles"""
    query = serializers.CharField(
        max_length=100,
        required=False,
        help_text="Search query for profiles"
    )
    phone = serializers.CharField(
        max_length=20,
        required=False,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ]
    )
    country = serializers.CharField(
        max_length=100,
        required=False,
        help_text="Filter by country"
    )
    degree = serializers.CharField(
        max_length=100,
        required=False,
        help_text="Filter by degree"
    )
    field = serializers.CharField(
        max_length=100,
        required=False,
        help_text="Filter by field of study"
    )
    verified = serializers.BooleanField(
        required=False,
        help_text="Filter by verification status"
    )
    limit = serializers.IntegerField(
        default=20,
        min_value=1,
        max_value=100,
        error_messages={
            'min_value': 'Limit must be at least 1.',
            'max_value': 'Limit cannot exceed 100.'
        }
    )

    def validate_query(self, value):
        """Validate search query"""
        if value:
            value = value.strip()
            if len(value) < 2:
                raise serializers.ValidationError("Search query must be at least 2 characters long.")
        return value


class ProfileAnalyticsSerializer(serializers.Serializer):
    """Serializer for profile analytics and insights"""
    phone = serializers.CharField(
        max_length=20,
        required=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ]
    )
    metrics = serializers.JSONField(
        required=False,
        help_text="Analytics metrics for the profile"
    )
    timeframe = serializers.ChoiceField(
        choices=['7d', '30d', '90d', '1y'],
        default='30d',
        required=False,
        help_text="Timeframe for analytics"
    )

    def validate_metrics(self, value):
        """Validate metrics JSON structure"""
        if value and not isinstance(value, dict):
            raise serializers.ValidationError("Metrics must be a valid JSON object.")
        return value


class ProfileComparisonSerializer(serializers.Serializer):
    """Serializer for comparing student profiles"""
    phone1 = serializers.CharField(
        max_length=20,
        required=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ]
    )
    phone2 = serializers.CharField(
        max_length=20,
        required=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ]
    )
    comparisonType = serializers.ChoiceField(
        choices=['academic', 'financial', 'comprehensive'],
        default='comprehensive',
        error_messages={
            'invalid_choice': 'Comparison type must be one of: academic, financial, comprehensive.'
        }
    )

    def validate_phone1(self, value):
        """Validate first phone number"""
        value = value.strip()
        if not value:
            raise serializers.ValidationError("First phone number is required.")
        return value

    def validate_phone2(self, value):
        """Validate second phone number"""
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Second phone number is required.")
        return value


class ProfileExportSerializer(serializers.Serializer):
    """Serializer for exporting profile data"""
    phone = serializers.CharField(
        max_length=20,
        required=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ]
    )
    format = serializers.ChoiceField(
        choices=['json', 'csv', 'excel', 'pdf'],
        default='json',
        error_messages={
            'invalid_choice': 'Format must be one of: json, csv, excel, pdf.'
        }
    )
    includeSensitive = serializers.BooleanField(
        default=False,
        help_text="Include sensitive information in export"
    )

    def validate_phone(self, value):
        """Validate phone number"""
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Phone number is required.")
        return value


class ProfileNotificationSerializer(serializers.Serializer):
    """Serializer for profile notifications and preferences"""
    phone = serializers.CharField(
        max_length=20,
        required=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ]
    )
    notificationType = serializers.ChoiceField(
        choices=['email', 'sms', 'push', 'whatsapp'],
        default='email',
        error_messages={
            'invalid_choice': 'Notification type must be one of: email, sms, push, whatsapp.'
        }
    )
    preferences = serializers.JSONField(
        required=False,
        help_text="Notification preferences"
    )

    def validate_phone(self, value):
        """Validate phone number"""
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Phone number is required.")
        return value


class ProfileActivitySerializer(serializers.Serializer):
    """Serializer for tracking profile activities"""
    phone = serializers.CharField(
        max_length=20,
        required=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ]
    )
    activityType = serializers.ChoiceField(
        choices=[
            'profile_created', 'profile_updated', 'course_viewed',
            'course_saved', 'search_performed', 'application_submitted',
            'document_uploaded', 'payment_made', 'notification_sent'
        ],
        required=True,
        error_messages={
            'invalid_choice': 'Invalid activity type.'
        }
    )
    metadata = serializers.JSONField(
        required=False,
        help_text="Additional metadata about the activity"
    )
    timestamp = serializers.DateTimeField(read_only=True)

    def validate_phone(self, value):
        """Validate phone number"""
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Phone number is required.")
        return value


class ProfileFeedbackSerializer(serializers.Serializer):
    """Serializer for collecting user feedback"""
    phone = serializers.CharField(
        max_length=20,
        required=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ]
    )
    feedbackType = serializers.ChoiceField(
        choices=['course_suggestion', 'search_result', 'app_experience', 'bug_report'],
        required=True,
        error_messages={
            'invalid_choice': 'Feedback type must be one of: course_suggestion, search_result, app_experience, bug_report.'
        }
    )
    rating = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=5,
        error_messages={
            'min_value': 'Rating must be between 1 and 5.',
            'max_value': 'Rating must be between 1 and 5.'
        }
    )
    comment = serializers.CharField(
        required=True,
        max_length=1000,
        error_messages={
            'required': 'Comment is required.',
            'blank': 'Comment cannot be blank.',
            'max_length': 'Comment cannot exceed 1000 characters.'
        }
    )

    def validate_phone(self, value):
        """Validate phone number"""
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Phone number is required.")
        return value

    def validate_rating(self, value):
        """Validate rating"""
        if value is not None and (value < 1 or value > 5):
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value


class ProfileBatchOperationSerializer(serializers.Serializer):
    """Serializer for batch operations on profiles"""
    operation = serializers.ChoiceField(
        choices=['export', 'delete', 'update', 'notify'],
        required=True,
        error_messages={
            'invalid_choice': 'Operation must be one of: export, delete, update, notify.'
        }
    )
    phoneNumbers = serializers.ListField(
        child=serializers.CharField(
            max_length=20,
            validators=[
                RegexValidator(
                    regex=r'^\+?1?\d{9,15}$',
                    message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
                )
            ]
        ),
        required=True,
        error_messages={
            'required': 'Phone numbers list is required.',
            'not_a_list': 'Phone numbers must be a list.'
        }
    )
    parameters = serializers.JSONField(
        required=False,
        help_text="Additional parameters for the batch operation"
    )

    def validate_phoneNumbers(self, value):
        """Validate phone numbers list"""
        if not value:
            raise serializers.ValidationError("Phone numbers list is required.")
        if len(value) > 100:
            raise serializers.ValidationError("Cannot process more than 100 phone numbers at once.")
        return [phone.strip() for phone in value if phone.strip()]

    def validate_operation(self, value):
        """Validate operation type"""
        if value == 'delete':
            # Additional validation for delete operation
            if not self.phoneNumbers or len(self.phoneNumbers) == 0:
                raise serializers.ValidationError("Phone numbers are required for delete operation.")
        return value


class ProfileImportSerializer(serializers.Serializer):
    """Serializer for importing profile data from external sources"""
    source = serializers.ChoiceField(
        choices=['csv', 'excel', 'json', 'api'],
        required=True,
        error_messages={
            'invalid_choice': 'Source must be one of: csv, excel, json, api.'
        }
    )
    data = serializers.JSONField(
        required=True,
        help_text="Profile data to import"
    )
    options = serializers.JSONField(
        required=False,
        help_text="Import options and mappings"
    )
    overwrite = serializers.BooleanField(
        default=False,
        help_text="Overwrite existing profiles"
    )

    def validate_data(self, value):
        """Validate import data structure"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Data must be a valid JSON object.")
        return value


class ProfileBackupSerializer(serializers.Serializer):
    """Serializer for profile backup and restore operations"""
    phone = serializers.CharField(
        max_length=20,
        required=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ]
    )
    operation = serializers.ChoiceField(
        choices=['backup', 'restore'],
        required=True,
        error_messages={
            'invalid_choice': 'Operation must be one of: backup, restore.'
        }
    )
    includeSensitive = serializers.BooleanField(
        default=True,
        help_text="Include sensitive information in backup"
    )

    def validate_phone(self, value):
        """Validate phone number"""
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Phone number is required.")
        return value