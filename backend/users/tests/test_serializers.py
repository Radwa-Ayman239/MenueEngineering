from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.cache import cache
from django.test import override_settings

from rest_framework.test import APIRequestFactory
from rest_framework import serializers

from knox.models import AuthToken

from users.serializers import (
    CreateUserSerializer,
    ActivateAccountSerializer,
    LoginStep1Serializer,
    LoginStep2Serializer,
    ResendActivationSerializer,
    RefreshTokenSerializer,
    ForgotPasswordRequestSerializer,
    ForgotPasswordResetSerializer,
)


class CreateUserSerializerTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.factory = APIRequestFactory()
        self.admin_user = self.User.objects.create_user(
            email="admin@email.com",
            password="adminpass",
            first_name="Admin",
            last_name="User",
            phone_number="+201234567890",
            type="admin",
            is_active=True,
        )
        self.manager_user = self.User.objects.create_user(
            email="manager@email.com",
            password="managerpass",
            first_name="Manager",
            last_name="User",
            phone_number="+201234567891",
            type="manager",
            is_active=True,
        )
        cache.clear()

    @patch("users.serializers.TokenManager.set_email_verification_token")
    @patch("users.serializers.send_verification_email")
    def test_create_user_admin_success(self, mock_email, mock_token):
        mock_token.return_value = "test-token"
        data = {
            "email": "manager0@email.com",
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "+201234567892",
            "type": "manager",
        }
        # Create a mock request with the admin user
        mock_request = MagicMock()
        mock_request.user = self.admin_user

        serializer = CreateUserSerializer(
            data=data,
            context={"request": mock_request},
        )
        self.assertTrue(serializer.is_valid())

        user = serializer.save()
        self.assertEqual(user.email, "manager0@email.com")
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_email_verified)
        mock_token.assert_called_once_with(user.id)
        mock_email.assert_called_once_with(user, "test-token")

    def test_create_user_email_already_exists(self):
        data = {
            "email": "manager@email.com",
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "+201234567892",
        }
        mock_request = MagicMock()
        mock_request.user = self.admin_user
        serializer = CreateUserSerializer(data=data, context={"request": mock_request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_admin_cannot_create_admin(self):
        data = {
            "email": "admin01@email.com",
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "+201234567892",
            "type": "admin",
        }
        mock_request = MagicMock()
        mock_request.user = self.admin_user
        serializer = CreateUserSerializer(data=data, context={"request": mock_request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("type", serializer.errors)

    def test_manager_can_create_staff(self):
        data = {
            "email": "staff@email.com",
            "first_name": "staff",
            "last_name": "User",
            "phone_number": "+201234567893",
            "type": "staff",
        }
        mock_request = MagicMock()
        mock_request.user = self.manager_user
        serializer = CreateUserSerializer(data=data, context={"request": mock_request})
        self.assertTrue(serializer.is_valid())

    def test_manager_cannot_create_manager(self):
        data = {
            "email": "manager01@email.com",
            "first_name": "Manager",
            "last_name": "User",
            "phone_number": "+201234567893",
            "type": "manager",
        }
        mock_request = MagicMock()
        mock_request.user = self.manager_user
        serializer = CreateUserSerializer(data=data, context={"request": mock_request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("type", serializer.errors)

    def test_no_request_context_fails(self):
        data = {
            "email": "[email protected]",
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "+201234567892",
        }
        serializer = CreateUserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("type", serializer.errors)
        self.assertEqual(serializer.errors["type"][0], "Authentication required.")


class ActivateAccountSerializerTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        cache.clear()
        self.user = self.User.objects.create_user(
            email="[email protected]",
            password=None,
            first_name="John",
            last_name="Doe",
            phone_number="+201234567890",
            is_active=False,
            is_email_verified=False,
        )

    def test_valid_token_activates_account(self):
        from users.managers import TokenManager

        token = TokenManager.set_email_verification_token(self.user.id)
        data = {
            "token": token,
            "password": "newSecurePassword123!",
            "password2": "newSecurePassword123!",
        }
        serializer = ActivateAccountSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        result = serializer.save()
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertTrue(self.user.is_email_verified)
        self.assertEqual(result["status"], "activated")

    def test_invalid_token_fails(self):
        data = {
            "token": "invalid-token",
            "password": "password123",
            "password2": "password123",
        }
        serializer = ActivateAccountSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("token", serializer.errors)

    def test_passwords_not_match(self):
        token = "valid-token"
        data = {
            "token": token,
            "password": "password123",
            "password2": "different123",
        }
        serializer = ActivateAccountSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)

    def test_already_activated_account(self):
        self.user.is_active = True
        self.user.is_email_verified = True
        self.user.set_password("existing")
        self.user.save()

        from users.managers import TokenManager

        token = TokenManager.set_email_verification_token(self.user.id)
        data = {
            "token": token,
            "password": "newpass123",
            "password2": "newpass123",
        }
        serializer = ActivateAccountSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("token", serializer.errors)


class LoginStep1SerializerTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="john.doe@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            phone_number="+201234567890",
            is_active=True,
            is_email_verified=True,
        )
        cache.clear()

    @patch("users.serializers.authenticate")
    @patch("users.serializers.TokenManager.set_otp_token")
    @patch("users.tasks.send_otp_sms_task.delay")
    @patch("django.core.cache.cache.set")
    def test_successful_step1(self, mock_cache, mock_sms, mock_otp, mock_auth):
        """Test successful password verification and OTP sending"""
        # Mock authenticate to return the test user
        mock_auth.return_value = self.user
        mock_otp.return_value = "ABCD5678"

        data = {
            "email": "john.doe@example.com",
            "password": "testpass123",
        }
        mock_request = MagicMock()
        serializer = LoginStep1Serializer(data=data, context={"request": mock_request})

        self.assertTrue(serializer.is_valid())

        # Test OTP flow
        result = serializer.create_session_and_send_otp()
        self.assertIn("OTP sent", result["message"])
        self.assertIn(str(self.user.phone_number)[-4:], result["message"])
        mock_otp.assert_called_once()
        mock_sms.assert_called_once()
        mock_cache.assert_called_once()

    def test_user_not_found(self):
        data = {"email": "nonexistent@example.com", "password": "pass"}
        serializer = LoginStep1Serializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)
        self.assertEqual(serializer.errors["non_field_errors"][0].code, "authorization")

    def test_account_not_activated(self):
        user = self.User.objects.create_user(
            email="[email protected]",
            password=None,
            first_name="Inactive",
            last_name="User",
            phone_number="+201234567891",
        )
        data = {"email": "inactive@email.com", "password": "pass"}
        serializer = LoginStep1Serializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)
        self.assertEqual(serializer.errors["non_field_errors"][0].code, "authorization")

    def test_no_phone_number(self):
        mock_user = MagicMock()
        mock_user.phone_number = None
        mock_user.email = "nophone@email.com"

        with patch("users.serializers.authenticate", return_value=mock_user):
            with patch(
                "users.serializers.CustomUser.objects.get", return_value=mock_user
            ):
                data = {"email": "nophone@email.com", "password": "pass"}
                mock_request = MagicMock()
                serializer = LoginStep1Serializer(
                    data=data, context={"request": mock_request}
                )

                self.assertFalse(serializer.is_valid())
                self.assertIn("non_field_errors", serializer.errors)
                self.assertEqual(
                    serializer.errors["non_field_errors"][0].code, "no_phone"
                )


class LoginStep2SerializerTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="some@email.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            phone_number="+201234567890",
            is_active=True,
            is_email_verified=True,
        )
        cache.clear()

    def test_valid_session_and_otp(self):
        from users.managers import TokenManager
        from django.core.cache import cache

        session_token = "valid-session-token"
        cache.set(f"login_session:{session_token}", str(self.user.id), timeout=300)
        otp = TokenManager.set_otp_token(self.user.id, str(self.user.phone_number))
        data = {"session_token": session_token, "otp": otp}
        serializer = LoginStep2Serializer(data=data)
        self.assertTrue(serializer.is_valid())

        result = serializer.create_tokens()
        self.assertIn("access", result)
        self.assertIn("refresh", result)
        self.assertEqual(result["user_data"]["email"], self.user.email)

    def test_invalid_session_token(self):
        data = {"session_token": "invalid", "otp": 123456}
        serializer = LoginStep2Serializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors["session_token"][0].code, "session_expired")
        self.assertEqual(
            str(serializer.errors["session_token"][0]),
            "Session expired. Please start login again.",
        )

    def test_invalid_otp(self):
        from django.core.cache import cache

        cache.set(f"login_session:valid-token", str(self.user.id), timeout=300)
        data = {"session_token": "valid-token", "otp": "WRONG"}
        serializer = LoginStep2Serializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors["otp"][0].code, "invalid_otp")
        self.assertEqual(str(serializer.errors["otp"][0]), "Invalid or expired OTP.")

    def test_token_cleanup(self):
        from django.core.cache import cache

        session_token = "test-cleanup"
        cache.set(f"login_session:{session_token}", str(self.user.id), timeout=300)
        data = {"session_token": session_token, "otp": "VALID"}
        serializer = LoginStep2Serializer(data=data)
        serializer.is_valid()
        self.assertIsNone(cache.get(f"login_session:{session_token}"))


class ResendActivationSerializerTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.unverified_user = self.User.objects.create_user(
            email="unverified@email.com",
            password=None,
            first_name="Unverified",
            last_name="User",
            phone_number="+201234567890",
            is_active=False,
            is_email_verified=False,
        )
        self.verified_user = self.User.objects.create_user(
            email="verified@email.com",
            password="VerifiedPass",
            first_name="Verified",
            last_name="User",
            phone_number="+201234567891",
            is_active=True,
            is_email_verified=True,
        )

    @patch("users.serializers.TokenManager.set_email_verification_token")
    @patch("users.serializers.send_verification_email")
    def test_resend_to_unverified_user(self, mock_email, mock_token):
        mock_token.return_value = "new-token"
        data = {"email": self.unverified_user.email}
        serializer = ResendActivationSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        result = serializer.save()
        self.assertEqual(result["detail"], "Activation email sent.")
        mock_token.assert_called_once()
        mock_email.assert_called_once()

    def test_resend_to_verified_user_fails(self):
        data = {"email": self.verified_user.email}
        serializer = ResendActivationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_resend_nonexistent_email(self):
        data = {"email": "nonexistent@example.com"}
        serializer = ResendActivationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)


class ForgotPasswordSerializersTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.verified_user = self.User.objects.create_user(
            email="verified@email.com",
            password="testpass123",
            first_name="Verified",
            last_name="User",
            phone_number="+201234567890",
            is_active=True,
            is_email_verified=True,
        )
        self.unverified_user = self.User.objects.create_user(
            email="unverified@email.com",
            password=None,
            first_name="Unverified",
            last_name="User",
            is_active=False,
            phone_number="+201234567891",
            is_email_verified=False,
        )

    @patch("users.managers.TokenManager.set_password_reset_token")
    @patch("users.services.send_forgot_password_email")
    def test_forgot_password_request(self, mock_email, mock_token):
        mock_token.return_value = "reset-token"
        data = {"email": self.verified_user.email}
        serializer = ForgotPasswordRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        result = serializer.save()
        self.assertIn("password reset link has been sent", result["detail"])
        mock_token.assert_called_once()
        mock_email.assert_called_once()

    @patch("users.managers.TokenManager.set_password_reset_token")
    def test_forgot_password_unverified_user_silent_fail(self, mock_token):
        data = {"email": self.unverified_user.email}
        serializer = ForgotPasswordRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        result = serializer.save()
        self.assertIn("password reset link has been sent", result["detail"])
        mock_token.assert_not_called()
    
    def test_forgot_password_reset_valid_token(self):
        from users.managers import TokenManager
        token = TokenManager.set_password_reset_token(self.verified_user.id)

        data = {
            "token": token,
            "password": "newSecurePassword123!",
            "password2": "newSecurePassword123!",
        }
        serializer = ForgotPasswordResetSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        result = serializer.save()

        self.verified_user.refresh_from_db()
        self.assertTrue(self.verified_user.check_password("newSecurePassword123!"))
        self.assertEqual(result["status"], "password_reset_success")
    
    def test_forgot_password_reset_password_mismatch(self):
        data = {
            "token": "valid-token",
            "password": "testpass123",
            "password2": "testpass1234",
        }
        serializer = ForgotPasswordResetSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("Passwords do not match", str(serializer.errors))
        self.assertIn("passwords_not_match", serializer.errors["password"][0].code)


class RefreshTokenSerializerTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="some@email.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            phone_number="+201234567890",
            is_active=True,
            is_email_verified=True,
        )
    
    def test_refresh_token_valid(self):
        access_token, _ = AuthToken.objects.create(user=self.user)
        refresh_instance, refresh_token = AuthToken.objects.create(user=self.user)

        data = {"refresh": refresh_token}
        serializer = RefreshTokenSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        result = serializer.save()

        self.assertIn("access", result)
        self.assertIn("refresh", result)
        self.assertEqual(len(AuthToken.objects.filter(user=self.user)), 2)
    
    def test_refresh_token_invalid(self):
        data = {"refresh": "invalid-token"}
        serializer = RefreshTokenSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("refresh", serializer.errors)
