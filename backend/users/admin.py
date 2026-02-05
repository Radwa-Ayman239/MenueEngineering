"""
Django admin configuration for users app.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Custom admin for CustomUser model."""

    list_display = [
        "email",
        "first_name",
        "last_name",
        "type",
        "is_active",
        "is_email_verified",
        "date_joined",
    ]
    list_filter = ["type", "is_active", "is_email_verified", "date_joined"]
    search_fields = ["email", "first_name", "last_name", "phone_number"]
    ordering = ["-date_joined"]

    # Fields for viewing/editing a user
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "phone_number")}),
        (_("Role & Status"), {"fields": ("type", "is_email_verified")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    # Fields for adding a new user
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "phone_number",
                    "type",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    # Remove username from required fields
    readonly_fields = ["date_joined", "last_login"]
