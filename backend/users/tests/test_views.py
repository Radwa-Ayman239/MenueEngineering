from unittest.mock import patch, MagicMock
from django.urls import reverse
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.core.cache import cache
from knox.models import AuthToken

from users.views import (
    CreateUserView,
    ActivateAccountView,
    ResendActivationView,
    LoginStep1View,
    LoginStep2View,
    RefreshTokenView,
    ForgotPasswordRequestView,
    ForgotPasswordResetView,
    LogoutView,
)


class UsersURLTests(TestCase):
    def test_url_names_reverse(self):
        url_names = [
            "users:create-user",
            "users:activate",
            "users:resend-activation",
            "users:login",
            "users:login-verify",
            "users:logout",
            "users:token-refresh",
            "users:forgot-password",
            "users:reset-password",
        ]

        for name in url_names:
            with self.subTest(name=name):
                url = reverse(name)
                self.assertIsInstance(url, str)
                self.assertNotEqual(url, "")


class CreateUserViewTests(APITestCase):
    def setUp(self):
        self.User = get_user_model()
        self.admin_user = self.User.objects.create_user(
            email="admin@test.com",
            password="adminpass123",
            first_name="Admin",
            last_name="User",
            phone_number="+201234567890",
            type="admin",
            is_active=True,
        )
        self.admin_token = AuthToken.objects.create(user=self.admin_user)[1]
        self.manager_user = self.User.objects.create_user(
            email="manager@test.com",
            password="managerpass123",
            first_name="Manager",
            last_name="User",
            phone_number="+201234567891",
            type="manager",
            is_active=True,
        )
        self.manager_token = AuthToken.objects.create(user=self.manager_user)[1]
        cache.clear()

    def get_authenticated_client(self, token):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Token " + token)
        return client

    def test_admin_can_create_manager(self):
        client = self.get_authenticated_client(self.admin_token)

        data = {
            "email": "newmanager@test.com",
            "first_name": "New",
            "last_name": "Manager",
            "phone_number": "+201234567892",
            "type": "manager",
        }

        with patch("users.views.CreateUserSerializer") as mock_serializer_class:
            mock_serializer = MagicMock()
            mock_serializer.is_valid.return_value = True
            mock_serializer.save.return_value = MagicMock(
                id="uuid", email="newmanager@test.com", type="manager"
            )
            mock_serializer_class.return_value = mock_serializer

            response = client.post(reverse("users:create-user"), data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("User created successfully", response.data["message"])

    def test_admin_cannot_create_admin(self):
        client = self.get_authenticated_client(self.admin_token)
        data = {
            "email": "fakeadmin@test.com",
            "first_name": "Fake",
            "last_name": "Admin",
            "phone_number": "+201234567892",
            "type": "admin",
        }
        response = client.post(reverse("users:create-user"), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_can_create_staff(self):
        client = self.get_authenticated_client(self.manager_token)
        data = {
            "email": "newstaff@test.com",
            "first_name": "New",
            "last_name": "Staff",
            "phone_number": "+201234567893",
            "type": "staff",
        }
        response = client.post(reverse("users:create-user"), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_unauthenticated_cannot_create(self):
        client = APIClient()
        data = {"email": "test@test.com", "first_name": "Test", "last_name": "User"}
        response = client.post(reverse("users:create-user"), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ActivateAccountViewTests(APITestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="pending@test.com",
            password=None,
            first_name="Pending",
            last_name="User",
            phone_number="+201234567890",
            is_active=False,
            is_email_verified=False,
        )
        cache.clear()

    @patch("users.views.ActivateAccountSerializer")
    def test_valid_activation(self, mock_serializer):
        mock_serializer_instance = MagicMock()
        mock_serializer_instance.is_valid.return_value = True
        mock_serializer_instance.save.return_value = {
            "status": "activated",
            "email": "pending@test.com",
        }
        mock_serializer.return_value = mock_serializer_instance

        response = self.client.post(reverse("users:activate"), {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_token(self):
        response = self.client.post(
            reverse("users:activate"),
            {"token": "invalid-token", "password": "test123", "password2": "test123"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginFlowTests(APITestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="user@test.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            phone_number="+201234567890",
            is_active=True,
            is_email_verified=True,
        )
        cache.clear()

    @patch("users.views.LoginStep1Serializer")
    @patch("users.views.LoginStep2Serializer")
    def test_complete_login_flow(self, mock_step2, mock_step1):
        # Mock step 1
        mock_step1_instance = MagicMock()
        mock_step1_instance.is_valid.return_value = True
        mock_step1_instance.create_session_and_send_otp.return_value = {
            "message": "OTP sent",
            "session_token": "test-session",
        }
        mock_step1.return_value = mock_step1_instance

        # Mock step 2
        mock_step2_instance = MagicMock()
        mock_step2_instance.is_valid.return_value = True
        mock_step2_instance.create_tokens.return_value = {
            "access": "access_token",
            "refresh": "refresh_token",
        }
        mock_step2.return_value = mock_step2_instance

        # Step 1
        step1_response = self.client.post(
            reverse("users:login"),
            {"email": "user@test.com", "password": "testpass123"},
        )
        self.assertEqual(step1_response.status_code, status.HTTP_200_OK)

        # Step 2
        step2_response = self.client.post(
            reverse("users:login-verify"),
            {"session_token": "test-session", "otp": "123456"},
        )
        self.assertEqual(step2_response.status_code, status.HTTP_200_OK)

    def test_login_step1_invalid_credentials(self):
        response = self.client.post(
            reverse("users:login"), {"email": "wrong@test.com", "password": "wrongpass"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TokenManagementTests(APITestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="tokenuser@test.com",
            password="testpass123",
            first_name="Token",
            last_name="User",
            phone_number="+201234567890",
            is_active=True,
        )
        self.token = AuthToken.objects.create(user=self.user)[1]
        cache.clear()

    def test_token_refresh(self):
        response = self.client.post(
            reverse("users:token-refresh"), {"refresh": self.token}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_token_refresh_invalid(self):
        response = self.client.post(
            reverse("users:token-refresh"), {"refresh": "invalid-token"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Token " + self.token)
        response = client.post(reverse("users:logout"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"detail": "Successfully logged out."})


class ForgotPasswordTests(APITestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="reset@test.com",
            password="oldpass123",
            first_name="Reset",
            last_name="User",
            phone_number="+201234567890",
            is_active=True,
            is_email_verified=True,
        )
        cache.clear()

    @patch("users.views.ForgotPasswordRequestSerializer")
    def test_forgot_password_request(self, mock_serializer):
        mock_serializer_instance = MagicMock()
        mock_serializer_instance.is_valid.return_value = True
        mock_serializer.return_value = mock_serializer_instance

        response = self.client.post(
            reverse("users:forgot-password"), {"email": "reset@test.com"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("users.views.ForgotPasswordResetSerializer")
    def test_password_reset(self, mock_serializer):
        mock_serializer_instance = MagicMock()
        mock_serializer_instance.is_valid.return_value = True
        mock_serializer_instance.save.return_value = {
            "status": "password_reset_success"
        }
        mock_serializer.return_value = mock_serializer_instance

        response = self.client.post(
            reverse("users:reset-password"),
            {
                "token": "reset-token",
                "password": "newpass123",
                "password2": "newpass123",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PermissionTests(APITestCase):
    def setUp(self):
        self.User = get_user_model()
        self.admin_user = self.User.objects.create_user(
            email="admin@test.com",
            password="adminpass",
            first_name="Admin",
            last_name="Test",
            type="admin",
            is_active=True,
            phone_number="+201234567891"
        )
        self.staff_user = self.User.objects.create_user(
            email="staff@test.com",
            password="staffpass",
            first_name="Staff",
            last_name="Test",
            type="staff",
            is_active=True,
            phone_number="+201234567890"
        )
        self.admin_token = AuthToken.objects.create(user=self.admin_user)[1]
        self.staff_token = AuthToken.objects.create(user=self.staff_user)[1]

    def test_create_user_permissions(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Token " + self.staff_token)

        response = client.post(reverse("users:create-user"), {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_logout_requires_auth(self):
        response = self.client.post(reverse("users:logout"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_public_endpoints_allow_any(self):
        public_endpoints = [
            reverse("users:activate"),
            reverse("users:resend-activation"),
            reverse("users:login"),
            reverse("users:login-verify"),
            reverse("users:forgot-password"),
            reverse("users:reset-password"),
        ]

        for url in public_endpoints:
            with self.subTest(url=url):
                response = self.client.post(url, {})
                self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
