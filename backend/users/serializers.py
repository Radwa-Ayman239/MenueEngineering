"""
File: serializers.py
Author: Hamdy El-Madbouly
Description: Serializers for User data and Authentication payloads.
Includes logic for validating registration data, ensuring password strength,
and formatting user profiles for API responses.

User Creation Flow:
1. Admin/Manager creates user (email, phone, name, type) - NO password
2. User receives activation email with token
3. User sets password via activation endpoint

Login Flow (2FA):
1. User enters email + password -> receives OTP via SMS
2. User enters OTP -> receives access token
"""

from datetime import timedelta

from django.db import transaction
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from django.core.validators import RegexValidator

from rest_framework import serializers, exceptions
from rest_framework.validators import UniqueValidator

from knox.models import AuthToken

from .models import CustomUser
from .sms_service import send_otp_sms
from .services import send_verification_email
from .managers import TokenManager
from .tasks import send_otp_sms_task


# ============================================================================
# User Creation (by Admin/Manager)
# ============================================================================


class CreateUserSerializer(serializers.ModelSerializer):
    """
    Admin/Manager creates a user without password.
    Password is set by user during email activation.
    """

    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=CustomUser.objects.all())]
    )
    type = serializers.ChoiceField(
        choices=[
            (CustomUser.UserTypes.MANAGER, "Manager"),
            (CustomUser.UserTypes.STAFF, "Staff"),
        ],
        default=CustomUser.UserTypes.STAFF,
    )

    class Meta:
        model = CustomUser
        fields = [
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "type",
        ]

    def validate_type(self, value):
        """Ensure requester can create this user type."""
        request = self.context.get("request")
        if not request or not request.user:
            raise serializers.ValidationError("Authentication required.")

        requester_type = request.user.type

        if requester_type == "admin":
            if value not in ["manager", "staff"]:
                raise serializers.ValidationError(
                    "Admin can only create Managers or Staff."
                )
        elif requester_type == "manager":
            if value != "staff":
                raise serializers.ValidationError("Managers can only create Staff.")
        else:
            raise serializers.ValidationError(
                "You do not have permission to create users."
            )

        return value

    def create(self, validated_data):
        # Create user without password, inactive until email verified
        user = CustomUser.objects.create_user(
            email=validated_data["email"],
            password=None,  # No password yet
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            phone_number=validated_data.get("phone_number"),
            type=validated_data.get("type", CustomUser.UserTypes.STAFF),
            is_active=False,
            is_email_verified=False,
        )

        # Send activation email
        token = TokenManager.set_email_verification_token(user.id)
        send_verification_email(user, token)

        return user


# ============================================================================
# Account Activation (User sets password)
# ============================================================================


class ActivateAccountSerializer(serializers.Serializer):
    """
    User activates account by setting their password via email token.
    """

    token = serializers.CharField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def validate_token(self, value):
        user_id = TokenManager.validate_email_verification_token(value)
        if not user_id:
            raise serializers.ValidationError(
                "Invalid or expired token", code="invalid_token"
            )
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("User not found", code="user_not_found")

        if user.is_email_verified:
            raise serializers.ValidationError("Account already activated.")

        return user

    def save(self):
        user = self.validated_data["token"]
        password = self.validated_data["password"]

        with transaction.atomic():
            user.set_password(password)
            user.is_active = True
            user.is_email_verified = True
            user.save(update_fields=["password", "is_active", "is_email_verified"])

        return {"status": "activated", "email": user.email}


# ============================================================================
# Login Step 1: Password Verification → Send OTP
# ============================================================================


class LoginStep1Serializer(serializers.Serializer):
    """
    First step of 2FA login: Validate email + password, then send OTP.
    Returns a temporary session token for step 2.
    """

    email = serializers.EmailField(
        validators=[
            RegexValidator(
                regex=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
                message="Enter a valid email address.",
                code="invalid",
            )
        ],
        help_text="User's registered email address (e.g., john.doe@example.com)",
    )
    password = serializers.CharField(
        write_only=True, help_text="User's account password (e.g., MySecurePass123!)"
    )

    # Response fields
    message = serializers.CharField(read_only=True)
    session_token = serializers.CharField(read_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if not email or not password:
            raise serializers.ValidationError('Must include "email" and "password".')

        # Check if user exists and get details for better error messages
        try:
            user = CustomUser.objects.get(email=email.lower())
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError(
                "Unable to log in with provided credentials.", code="authorization"
            )

        # Check if account is activated (has password set)
        if not user.has_usable_password():
            raise serializers.ValidationError(
                "Account not activated. Please check your email for activation link.",
                code="not_activated",
            )

        # Authenticate
        authenticated_user = authenticate(
            request=self.context.get("request"), username=email, password=password
        )

        if not authenticated_user:
            raise serializers.ValidationError(
                "Unable to log in with provided credentials.", code="authorization"
            )

        # Check if user has phone number for OTP
        if not user.phone_number:
            raise serializers.ValidationError(
                "No phone number registered. Please contact administrator.",
                code="no_phone",
            )

        attrs["user"] = authenticated_user
        return attrs

    def create_session_and_send_otp(self):
        """Send OTP and return session token for step 2."""
        user = self.validated_data["user"]

        # Generate OTP and store
        otp = TokenManager.set_otp_token(user.id, str(user.phone_number))

        # Send OTP via SMS (async)
        send_otp_sms_task.delay(str(user.phone_number), otp)

        # Create a temporary session token for step 2
        session_token = TokenManager._generate_signed_token()
        from django.core.cache import cache

        cache.set(
            f"login_session:{session_token}",
            str(user.id),
            timeout=300,  # 5 minutes to complete step 2
        )

        return {
            "message": f"OTP sent to phone ending in ...{str(user.phone_number)[-4:]}",
            "session_token": session_token,
        }


# ============================================================================
# Login Step 2: OTP Verification → Access Token
# ============================================================================


class LoginStep2Serializer(serializers.Serializer):
    """
    Second step of 2FA login: Validate OTP and return access token.
    """

    session_token = serializers.CharField()
    otp = serializers.CharField(max_length=10)

    # Response fields (read-only)
    access = serializers.CharField(read_only=True)
    access_expiry = serializers.DateTimeField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    refresh_expiry = serializers.DateTimeField(read_only=True)
    user_data = serializers.DictField(read_only=True)

    access_ttl = timedelta(hours=3)  # 3 hours for OTP-based login
    refresh_ttl = timedelta(days=7)

    def validate_session_token(self, value):
        from django.core.cache import cache

        user_id = cache.get(f"login_session:{value}")
        if not user_id:
            raise serializers.ValidationError(
                "Session expired. Please start login again.", code="session_expired"
            )

        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("User not found.")

        self._user = user
        self._session_token = value
        return value

    def validate(self, attrs):
        otp = attrs.get("otp", "").strip()

        if not hasattr(self, "_user"):
            raise serializers.ValidationError("Invalid session.")

        # Validate OTP
        from django.core.cache import cache

        # Ensure session is cleaned up regardless of OTP validity
        try:
            user_id = TokenManager.validate_otp(str(self._user.phone_number), otp)
        finally:
            cache.delete(f"login_session:{self._session_token}")

        if not user_id:
            raise serializers.ValidationError(
                {"otp": "Invalid or expired OTP."}, code="invalid_otp"
            )
        attrs["user"] = self._user
        return attrs

    def create_tokens(self):
        """Create and return access/refresh tokens."""
        user = self.validated_data["user"]

        # Delete existing tokens
        AuthToken.objects.filter(user=user).delete()

        # Choose token TTL based on email verification
        if user.is_email_verified:
            access_ttl = timedelta(hours=1)  # Full access
        else:
            access_ttl = timedelta(hours=3)  # Temporary access

        access_instance, access_token = AuthToken.objects.create(
            user=user, expiry=access_ttl
        )
        refresh_instance, refresh_token = AuthToken.objects.create(
            user=user, expiry=self.refresh_ttl
        )

        return {
            "access": access_token,
            "access_expiry": access_instance.expiry,
            "refresh": refresh_token,
            "refresh_expiry": refresh_instance.expiry,
            "user_data": {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "type": user.type,
                "is_email_verified": user.is_email_verified,
            },
        }


# ============================================================================
# Resend Activation Email
# ============================================================================


class ResendActivationSerializer(serializers.Serializer):
    """Resend activation email for unactivated accounts."""

    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = CustomUser.objects.get(email=value.lower())
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")

        if user.is_email_verified:
            raise serializers.ValidationError("Account is already activated.")

        return value

    def save(self):
        email = self.validated_data["email"]
        user = CustomUser.objects.get(email=email.lower())

        token = TokenManager.set_email_verification_token(user.id)
        send_verification_email(user, token)
        return {"detail": "Activation email sent."}


# ============================================================================
# Token Refresh (keep for authenticated users)
# ============================================================================


class RefreshTokenSerializer(serializers.Serializer):
    """Refresh access token using refresh token."""

    refresh = serializers.CharField()
    access_ttl = timedelta(hours=1)
    refresh_ttl = timedelta(days=7)

    def validate_refresh(self, value):
        from knox.auth import TokenAuthentication

        try:
            user, token_instance = TokenAuthentication().authenticate_credentials(
                value.encode("utf-8")
            )
        except exceptions.AuthenticationFailed:
            raise serializers.ValidationError("Invalid or expired refresh token")

        self.instance = token_instance
        self._user = user
        return value

    def save(self, **kwargs):
        old_refresh = self.instance
        user = self._user

        old_refresh.delete()
        AuthToken.objects.filter(user=user).exclude(pk=old_refresh.pk).delete()

        new_access_instance, new_access_token = AuthToken.objects.create(
            user=user, expiry=self.access_ttl
        )
        new_refresh_instance, new_refresh_token = AuthToken.objects.create(
            user=user, expiry=self.refresh_ttl
        )

        return {
            "access": new_access_token,
            "access_expiry": new_access_instance.expiry,
            "refresh": new_refresh_token,
            "refresh_expiry": new_refresh_instance.expiry,
        }


# ============================================================================
# Forgot Password (for users who forgot their password)
# ============================================================================


class ForgotPasswordRequestSerializer(serializers.Serializer):
    """Request password reset link via email."""

    email = serializers.EmailField()

    def save(self, **kwargs):
        email = self.validated_data["email"]

        try:
            user = CustomUser.objects.get(email=email.lower())
        except CustomUser.DoesNotExist:
            # Don't reveal if email exists, but return generic success
            return {
                "detail": "If an account exists with this email, a password reset link has been sent."
            }

        if not user.is_email_verified:
            # Only verified users can reset password, but return generic success
            return {
                "detail": "If an account exists with this email, a password reset link has been sent."
            }

        from .services import send_forgot_password_email

        token = TokenManager.set_password_reset_token(user.id)
        send_forgot_password_email(user, token)

        return {
            "detail": "If an account exists with this email, a password reset link has been sent."
        }


class ForgotPasswordResetSerializer(serializers.Serializer):
    """Reset password using token from email."""

    token = serializers.CharField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    def validate(self, attrs):
        # Validate password mismatch first (before token validation)
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError(
                {"password": "Passwords do not match"}, code="passwords_not_match"
            )

        # Then validate token
        token = attrs.get("token")
        user_id = TokenManager.validate_password_reset_token(token)
        if not user_id:
            raise serializers.ValidationError(
                {"token": "Invalid or expired token"}, code="invalid_token"
            )
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError(
                {"token": "User not found"}, code="user_not_found"
            )

        attrs["user"] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data["user"]
        password = self.validated_data["password"]

        with transaction.atomic():
            user.set_password(password)
            user.save(update_fields=["password"])

        return {"status": "password_reset_success"}
