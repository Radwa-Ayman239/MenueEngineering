import uuid
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core import mail

from users.services import (
    send_verification_email,
    send_forgot_password_email,
    too_many_requests_email,
)
from users.tasks import (
    send_verification_email_task,
    send_forgot_password_email_task,
    send_security_alert_task,
    send_otp_sms_task,
)


class ServicesTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="some@email.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            phone_number="+201234567890",
        )
        self.token = "test-token-123"

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @patch("users.tasks.send_verification_email_task.delay")
    def test_send_verification_email_calls_task(self, mock_task):
        send_verification_email(self.user, self.token)
        mock_task.assert_called_once_with(self.user.id, self.token)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @patch("users.tasks.send_forgot_password_email_task.delay")
    def test_send_forgot_password_email_calls_task(self, mock_task):
        send_forgot_password_email(self.user, self.token)
        mock_task.assert_called_once_with(self.user.id, self.token)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @patch("users.tasks.send_security_alert_task.delay")
    def test_too_many_requests_email_calls_task(self, mock_task):
        msg = "Suspicious login attempt"
        too_many_requests_email(self.user.email, msg)
        mock_task.assert_called_once_with(self.user.email, msg)


class SendVerificationEmailTaskTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="some@email.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            phone_number="+201234567890",
        )
        self.token = "test-token-123"

    @override_settings(
        CELERY_TASK_ALWAYS_EAGER=True,
        DEFAULT_FROM_EMAIL="[email protected]",
        EMAIL_HOST="localhost",
        EMAIL_PORT=1025,
    )
    def test_send_verification_email_task_success(self):
        result = send_verification_email_task(self.user.id, self.token)
        self.assertIsNone(result)
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertEqual(email.subject, "Verify your email")
        self.assertEqual(email.from_email, "[email protected]")
        self.assertEqual(email.to, [self.user.email])

        expected_link = f"http://localhost:3000/verify-email/?token={self.token}"
        self.assertIn(expected_link, email.body)

    @override_settings(
        CELERY_TASK_ALWAYS_EAGER=True,
        DEFAULT_FROM_EMAIL="[email protected]",
    )
    def test_send_verification_email_task_user_not_found(self):
        result = send_verification_email_task(uuid.uuid4(), self.token)
        self.assertIsNone(result)
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_send_verification_email_task_invalid_token(self):
        result = send_verification_email_task(self.user.id, None)
        self.assertIsNone(result)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("token=", mail.outbox[0].body)


class SendForgotPasswordEmailTaskTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="some@email.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            phone_number="+201234567890",
        )
        self.token = "reset-token-456"

    @override_settings(
        CELERY_TASK_ALWAYS_EAGER=True,
        DEFAULT_FROM_EMAIL="[email protected]",
        EMAIL_HOST="localhost",
        EMAIL_PORT=1025,
    )
    def test_send_forgot_password_email_task_success(self):
        result = send_forgot_password_email_task(self.user.id, self.token)
        self.assertIsNone(result)
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertEqual(email.subject, "Password Reset")
        self.assertEqual(email.from_email, "[email protected]")
        self.assertEqual(email.to, [self.user.email])

        expected_link = f"http://localhost:3000/reset-password/?token={self.token}"
        self.assertIn(expected_link, email.body)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_send_forgot_password_email_task_user_not_found(self):
        result = send_forgot_password_email_task(uuid.uuid4(), self.token)
        self.assertIsNone(result)
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_send_forgot_password_email_task_invalid_token(self):
        result = send_forgot_password_email_task(self.user.id, None)
        self.assertIsNone(result)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("token=", mail.outbox[0].body)


class SendSecurityAlertTests(TestCase):
    @override_settings(
        CELERY_TASK_ALWAYS_EAGER=True,
        DEFAULT_FROM_EMAIL="[email protected]",
        EMAIL_HOST="localhost",
        EMAIL_PORT=1025,
    )
    def test_send_security_alert_task_success(self):
        user_email = "some@email.com"
        msg = "Multiple failed login attempts detected"
        result = send_security_alert_task(user_email, msg)
        self.assertIsNone(result)
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertEqual(email.subject, "Security Alert")
        self.assertEqual(email.from_email, "[email protected]")
        self.assertEqual(email.to, [user_email])
        self.assertIn(msg, email.body)
        self.assertIn("security alert", email.body.lower())

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_send_security_alert_task_empty_message(self):
        user_email = "some@email.com"
        result = send_security_alert_task(user_email, "")
        self.assertIsNone(result)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("strange activity", mail.outbox[0].body)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_send_security_alert_task_long_message(self):
        user_email = "some@email.com"
        long_msg = "Very long suspicious activity description " * 10
        result = send_security_alert_task(user_email, long_msg)
        self.assertIsNone(result)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(long_msg[:100], mail.outbox[0].body)


class SendOtpSmsTaskTests(TestCase):
    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @patch("users.sms_service.send_otp_sms")
    def test_send_otp_sms_task_calls_sms_service(self, mock_sms):
        phone_number = "+201234567890"
        otp = "ABCD5678"
        result = send_otp_sms_task(phone_number, otp)
        self.assertIsNone(result)
        mock_sms.assert_called_once_with(phone_number, otp)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @patch("users.sms_service.send_otp_sms")
    def test_send_otp_sms_task_handles_sms_failure(self, mock_sms):
        phone_number = "+201234567890"
        otp = "ABCD5678"
        mock_sms.side_effect = Exception("SMS service unavailable")
        with self.assertRaises(Exception):
            send_otp_sms_task(phone_number, otp)
        mock_sms.assert_called_once_with(phone_number, otp)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @patch("users.sms_service.send_otp_sms")
    def test_send_otp_task_invalid_phone(self, mock_sms):
        phone_number = ""
        otp = "ABCD5678"
        result = send_otp_sms_task(phone_number, otp)
        self.assertIsNone(result)
        mock_sms.assert_called_once_with(phone_number, otp)


class CeleryTaskDirectExecutionTests(TestCase):
    """Test Celery tasks by calling them directly (without .delay)"""

    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="[email protected]",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            phone_number="+201234567890",
        )
        self.token = "test-token-123"

    @override_settings(
        DEFAULT_FROM_EMAIL="[email protected]",
        EMAIL_HOST="localhost",
        EMAIL_PORT=1025,
    )
    def test_verification_task_direct_execution(self):
        result = send_verification_email_task(self.user.id, self.token)

        self.assertIsNone(result)
        self.assertEqual(len(mail.outbox), 1)

    @override_settings(
        DEFAULT_FROM_EMAIL="[email protected]",
        EMAIL_HOST="localhost",
        EMAIL_PORT=1025,
    )
    def test_password_reset_task_direct_execution(self):
        result = send_forgot_password_email_task(self.user.id, self.token)

        self.assertIsNone(result)
        self.assertEqual(len(mail.outbox), 1)

    @override_settings(
        DEFAULT_FROM_EMAIL="[email protected]",
        EMAIL_HOST="localhost",
        EMAIL_PORT=1025,
    )
    def test_security_alert_direct_execution(self):
        result = send_security_alert_task("[email protected]", "test alert")

        self.assertIsNone(result)
        self.assertEqual(len(mail.outbox), 1)


# Service Layer Error Handling Tests
class ServiceErrorHandlingTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="[email protected]",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            phone_number="+201234567890",
        )
        self.token = "error-test-token"

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @patch("users.tasks.send_verification_email_task.delay")
    def test_send_verification_email_task_failure(self, mock_task):
        # Mock task to raise exception
        mock_task.side_effect = Exception("Task failed")

        # Service calls the task which raises exception
        with self.assertRaises(Exception):
            send_verification_email(self.user, self.token)

        mock_task.assert_called_once_with(self.user.id, self.token)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @patch("users.tasks.send_forgot_password_email_task.delay")
    def test_send_forgot_password_email_task_failure(self, mock_task):
        mock_task.side_effect = Exception("Task failed")

        with self.assertRaises(Exception):
            send_forgot_password_email(self.user, self.token)

        mock_task.assert_called_once_with(self.user.id, self.token)


# Integration Tests
class ServicesTasksIntegrationTests(TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="[email protected]",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            phone_number="+201234567890",
        )
        self.token = "integration-test-token"

    @override_settings(
        CELERY_TASK_ALWAYS_EAGER=True,
        DEFAULT_FROM_EMAIL="[email protected]",
        EMAIL_HOST="localhost",
        EMAIL_PORT=1025,
    )
    def test_complete_verification_flow(self):
        # Service calls task
        send_verification_email(self.user, self.token)

        # Verify email was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn(self.token, email.body)
        self.assertIn("verify-email", email.body)

    @override_settings(
        CELERY_TASK_ALWAYS_EAGER=True,
        DEFAULT_FROM_EMAIL="[email protected]",
        EMAIL_HOST="localhost",
        EMAIL_PORT=1025,
    )
    def test_complete_password_reset_flow(self):
        send_forgot_password_email(self.user, self.token)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn(self.token, email.body)
        self.assertIn("reset-password", email.body)

    @override_settings(
        CELERY_TASK_ALWAYS_EAGER=True,
        DEFAULT_FROM_EMAIL="[email protected]",
        EMAIL_HOST="localhost",
        EMAIL_PORT=1025,
    )
    def test_security_alert_flow(self):
        too_many_requests_email(self.user.email, "Login attempts")

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, "Security Alert")
        self.assertIn("strange activity", email.body)
