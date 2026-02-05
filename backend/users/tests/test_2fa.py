from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch

from django.test import override_settings

User = get_user_model()


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class AuthenticationTests(APITestCase):
    def setUp(self):
        # Create admin user
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="adminpassword",
            first_name="Admin",
            last_name="User",
            phone_number="+16502530000",
            type="admin",
            is_active=True,
            is_email_verified=True,
        )

    @patch("users.services.send_verification_email_task.delay")
    def test_create_user_by_admin(self, mock_send_email_task):
        """Test that admin can create a staff user (no password set initially)"""
        self.client.force_authenticate(user=self.admin)
        url = reverse("users:create-user")
        data = {
            "email": "staff@example.com",
            "first_name": "Staff",
            "last_name": "Member",
            "phone_number": "+16502530001",
            "type": "staff",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)

        # Verify task was triggered
        mock_send_email_task.assert_called_once()

        new_user = User.objects.get(email="staff@example.com")
        self.assertFalse(new_user.has_usable_password())
        self.assertFalse(new_user.is_email_verified)
        self.assertFalse(new_user.is_active)

    @patch("users.serializers.send_otp_sms_task.delay")
    def test_login_flow(self, mock_send_sms):
        """Test the full 2FA login flow"""
        # 1. Setup active user with password
        user = User.objects.create_user(
            email="user@example.com",
            password="mypassword",
            first_name="Test",
            last_name="User",
            phone_number="+16502530002",
            type="staff",
            is_active=True,
            is_email_verified=True,
        )

        # 2. Login Step 1 (Password)
        url_step1 = reverse("users:login")
        data_step1 = {"email": "user@example.com", "password": "mypassword"}
        response = self.client.post(url_step1, data_step1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("session_token", response.data)
        session_token = response.data["session_token"]

        # Verify OTP was "sent" (mocked)
        mock_send_sms.assert_called_once()

        # Get the real OTP from cache to verify (since we can't see the SMS)
        from django.core.cache import cache

        key = f"otp:{user.phone_number}"
        otp_data = cache.get(key)
        self.assertIsNotNone(otp_data)
        otp = otp_data["otp"]

        # 3. Login Step 2 (OTP)
        url_step2 = reverse("users:login-verify")
        data_step2 = {"session_token": session_token, "otp": otp}
        response_step2 = self.client.post(url_step2, data_step2)

        self.assertEqual(response_step2.status_code, status.HTTP_200_OK)
        self.assertIn("access", response_step2.data)
        self.assertIn("refresh", response_step2.data)
        self.assertEqual(response_step2.data["user_data"]["email"], "user@example.com")
