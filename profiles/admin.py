from django.contrib import admin
from .models import StudentProfile, PhoneOTP


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "email",
        "phone",
        "is_verified",
        "created_at",
    )

    list_filter = (
        "is_verified",
        "created_at",
    )

    search_fields = (
        "name",
        "email",
        "phone",
    )

    fieldsets = (
        ("Contact Information", {
            "fields": ("name", "email", "phone")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at")
        }),
    )

    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False  # Profiles should only be created via OTP flow


@admin.register(PhoneOTP)
class PhoneOTPAdmin(admin.ModelAdmin):
    list_display = (
        "phone",
        "otp",
        "is_used",
        "expires_at",
        "created_at",
    )

    list_filter = (
        "is_used",
        "created_at",
        "expires_at",
    )

    search_fields = ("phone",)

    readonly_fields = (
        "id",
        "phone",
        "otp",
        "expires_at",
        "created_at",
    )

    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False  # Prevent manual OTP creation

    def has_change_permission(self, request, obj=None):
        return False  # Prevent editing OTPs manually
