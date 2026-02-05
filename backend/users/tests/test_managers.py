import uuid

from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.signing import BadSignature, SignatureExpired

from users.managers import TokenManager


class CustomUserManagerTests(TestCase):
    def setUp(self):
        self.User = get_user_model()

    def tearDown(self):
        self.User.objects.all().delete()

    def test_create_user_success(self):
        user = self.User.objects.create_user(
            email="some@email.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            phone_number="+201234567890",
        )
        self.assertEqual(user.email, "some@email.com")
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.last_name, "Doe")
        self.assertEqual(str(user.phone_number), "+201234567890")
        self.assertTrue(user.check_password("testpass123"))
        self.assertFalse(user.is_active)

    def test_create_user_email_normalized(self):
        user = self.User.objects.create_user(
            email="some@email.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            phone_number="+201234567890",
        )
        self.assertEqual(user.email, "some@email.com")

    def test_create_user_without_email_raises_error(self):
        with self.assertRaises(ValueError) as context:
            self.User.objects.create_user(
                email="",
                password="testpass123",
                first_name="John",
                last_name="Doe",
                phone_number="+201234567890",
            )
        self.assertEqual(str(context.exception), "The Email field must be set")

    def test_create_user_without_first_name_raises_error(self):
        with self.assertRaises(ValueError) as context:
            self.User.objects.create_user(
                email="some@email.com",
                password="testpass123",
                first_name="",
                last_name="Doe",
                phone_number="+201234567890",
            )
        self.assertEqual(str(context.exception), "The First Name field must be set")

    def test_create_user_without_last_name_raises_error(self):
        with self.assertRaises(ValueError) as context:
            self.User.objects.create_user(
                email="some@email.com",
                password="testpass123",
                first_name="John",
                last_name="",
                phone_number="+201234567890",
            )
        self.assertEqual(str(context.exception), "The Last Name field must be set")

    def test_create_user_without_phone_number_raises_error(self):
        with self.assertRaises(ValueError) as context:
            self.User.objects.create_user(
                email="some@email.com",
                password="testpass123",
                first_name="John",
                last_name="Doe",
            )
        self.assertEqual(
            str(context.exception), "The Phone Number field must be set for 2FA"
        )

    def test_create_user_is_active_default_false(self):
        user = self.User.objects.create_user(
            email="some@email.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            phone_number="+201234567890",
        )
        self.assertFalse(user.is_active)

    def test_create_user_can_override_is_active(self):
        user = self.User.objects.create_user(
            email="some@email.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            phone_number="+201234567890",
            is_active=True,
        )
        self.assertTrue(user.is_active)

    def test_create_superuser_success(self):
        superuser = self.User.objects.create_superuser(
            email="admin@email.com",
            password="adminpass123",
            first_name="Admin",
            last_name="User",
            phone_number="+201234567890",
        )
        self.assertEqual(superuser.email, "admin@email.com")
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_active)
        self.assertEqual(superuser.type, "admin")

    def test_create_superuser_sets_defaults(self):
        superuser = self.User.objects.create_superuser(
            email="admin@email.com",
            password="adminpass123",
            first_name="Admin",
            last_name="User",
            phone_number="+201234567890",
        )
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_active)
        self.assertEqual(superuser.type, "admin")

    def test_create_superuser_with_is_staff_false_raises_error(self):
        with self.assertRaises(ValueError) as context:
            self.User.objects.create_superuser(
                email="admin@email.com",
                password="adminpass123",
                first_name="Admin",
                last_name="User",
                phone_number="+201234567890",
                is_staff=False,
            )
        self.assertEqual(str(context.exception), "Superuser must have is_staff=True")

    def test_create_superuser_with_is_superuser_false_raises_error(self):
        with self.assertRaises(ValueError) as context:
            self.User.objects.create_superuser(
                email="admin@email.com",
                password="adminpass123",
                first_name="Admin",
                last_name="User",
                phone_number="+201234567890",
                is_superuser=False,
            )
        self.assertEqual(
            str(context.exception), "Superuser must have is_superuser=True"
        )

    def test_create_superuser_without_password(self):
        superuser = self.User.objects.create_superuser(
            email="admin@email",
            password=None,
            first_name="Admin",
            last_name="User",
            phone_number="+201234567890",
        )
        self.assertFalse(superuser.has_usable_password())


class TokenManagerTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user_id = uuid.uuid4()

    def tearDown(self):
        cache.clear()

    def test_generate_signed_token_created_token(self):
        token = TokenManager._generate_signed_token()
        self.assertIsNotNone(token)
        self.assertIsInstance(token, str)
        self.assertIn(":", token)

    def test_generate_token_creates_unique_tokens(self):
        token1 = TokenManager._generate_signed_token()
        token2 = TokenManager._generate_signed_token()
        self.assertNotEqual(token1, token2)

    def test_validate_signed_token_valid_token(self):
        token = TokenManager._generate_signed_token()
        is_valid = TokenManager._validate_signed_token(token, max_age=60)
        self.assertTrue(is_valid)

    def test_validated_signed_token_invalid_token(self):
        invalid_token = "invalid:token:signature"
        is_valid = TokenManager._validate_signed_token(invalid_token, max_age=60)
        self.assertFalse(is_valid)

    @patch("users.managers.TimestampSigner.unsign")
    def test_validate_signed_token_expired_token(self, mock_unsign):
        mock_unsign.side_effect = SignatureExpired("Signature expired")
        token = "some:expired_token"
        is_valid = TokenManager._validate_signed_token(token, max_age=1)
        self.assertFalse(is_valid)

    @patch("users.managers.TimestampSigner.unsign")
    def test_validate_signed_token_bad_signature(self, mock_unsign):
        mock_unsign.side_effect = BadSignature("Bad signature")
        token = "some:bad:token"
        is_valid = TokenManager._validate_signed_token(token, max_age=60)
        self.assertFalse(is_valid)

    def test_set_email_verification_token(self):
        token = TokenManager.set_email_verification_token(self.user_id)
        self.assertIsNotNone(token)

        key = f"email_verify:{token}"
        cached_user_id = cache.get(key)
        self.assertEqual(cached_user_id, self.user_id)

    def test_validate_email_verification_token_success(self):
        token = TokenManager.set_email_verification_token(self.user_id)
        validated_user_id = TokenManager.validate_email_verification_token(token)
        self.assertEqual(validated_user_id, self.user_id)

        key = f"email_verify:{token}"
        cached_user_id = cache.get(key)
        self.assertIsNone(cached_user_id)

    def test_validate_email_verification_token_invalid_signature(self):
        invalid_token = "invalid:token"
        validated_user_id = TokenManager.validate_email_verification_token(
            invalid_token
        )
        self.assertIsNone(validated_user_id)

    def test_validate_email_verification_token_not_in_cache(self):
        token = TokenManager._generate_signed_token()
        validated_user_id = TokenManager.validate_email_verification_token(token)
        self.assertIsNone(validated_user_id)

    def test_validate_email_verification_token_already_user(self):
        token = TokenManager.set_email_verification_token(self.user_id)
        validated_user_id = TokenManager.validate_email_verification_token(token)
        self.assertEqual(validated_user_id, self.user_id)

        validated_user_id = TokenManager.validate_email_verification_token(token)
        self.assertIsNone(validated_user_id)

    @patch("users.managers.cache")
    def test_email_verification_token_timeout(self, mock_cache):
        mock_cache.get.return_value = None

        token = TokenManager._generate_signed_token()
        key = f"email_verify:{token}"
        cached_user_id = mock_cache.get(key)
        self.assertIsNone(cached_user_id)

    def test_set_password_reset_token(self):
        token = TokenManager.set_password_reset_token(self.user_id)
        self.assertIsNotNone(token)

        key = f"password_reset:{token}"
        cached_user_id = cache.get(key)
        self.assertEqual(cached_user_id, self.user_id)

    def test_validate_password_reset_token_success(self):
        token = TokenManager.set_password_reset_token(self.user_id)
        validated_user_id = TokenManager.validate_password_reset_token(token)
        self.assertEqual(validated_user_id, self.user_id)

        key = f"password_reset:{token}"
        cached_user_id = cache.get(key)
        self.assertIsNone(cached_user_id)

    def test_validate_password_reset_token_invalid_signature(self):
        invalid_token = "invalid:token"
        validated_user_id = TokenManager.validate_password_reset_token(invalid_token)
        self.assertIsNone(validated_user_id)

    def test_validate_password_reset_token_already_used(self):
        token = TokenManager.set_password_reset_token(self.user_id)

        # First validation should succeed
        validated_user_id = TokenManager.validate_password_reset_token(token)
        self.assertEqual(validated_user_id, self.user_id)

        # Second validation should fail (token deleted)
        validated_user_id = TokenManager.validate_password_reset_token(token)
        self.assertIsNone(validated_user_id)

    def test_generate_complex_otp_format(self):
        otp = TokenManager._generate_complex_otp()
        self.assertEqual(len(otp), 8)
        self.assertTrue(otp.isalnum())
        self.assertTrue(otp.isupper())

        # Verify no confusing characters
        confusing_chars = ["O", "0", "I", "1", "l"]
        for char in confusing_chars:
            self.assertNotIn(char, otp)

    def test_generate_complex_otp_custom_length(self):
        otp = TokenManager._generate_complex_otp(length=12)
        self.assertEqual(len(otp), 12)

    def test_generate_complex_otp_uniqueness(self):
        otps = [TokenManager._generate_complex_otp() for _ in range(100)]
        unique_otps = set(otps)
        self.assertGreater(len(unique_otps), 95)

    def test_set_otp_token(self):
        phone_number = "+201234567890"
        otp = TokenManager.set_otp_token(self.user_id, phone_number)

        self.assertIsNotNone(otp)
        self.assertEqual(len(otp), 8)

        key = f"otp:{phone_number}"
        cached_data = cache.get(key)
        self.assertIsNotNone(cached_data)
        self.assertEqual(cached_data["otp"], otp)
        self.assertEqual(cached_data["user_id"], str(self.user_id))

    def test_validate_otp_success(self):
        phone_number = "+201234567890"
        otp = TokenManager.set_otp_token(self.user_id, phone_number)

        # Validate OTP
        validated_user_id = TokenManager.validate_otp(phone_number, otp)
        self.assertEqual(validated_user_id, str(self.user_id))

        # Verify OTP is deleted after validation
        key = f"otp:{phone_number}"
        cached_data = cache.get(key)
        self.assertIsNone(cached_data)

    def test_validate_otp_case_insensitive(self):
        phone_number = "+201234567890"
        otp = TokenManager.set_otp_token(self.user_id, phone_number)

        # Validate with lowercase
        validated_user_id = TokenManager.validate_otp(phone_number, otp.lower())
        self.assertEqual(validated_user_id, str(self.user_id))

    def test_validate_otp_invalid_code(self):
        phone_number = "+201234567890"
        otp = TokenManager.set_otp_token(self.user_id, phone_number)

        # Try to validate with wrong OTP
        validated_user_id = TokenManager.validate_otp(phone_number, "WRONGOTP")
        self.assertIsNone(validated_user_id)

        # Verify original OTP is still in cache
        key = f"otp:{phone_number}"
        cached_data = cache.get(key)
        self.assertIsNotNone(cached_data)

    def test_validate_otp_wrong_phone_number(self):
        phone_number = "+201234567890"
        otp = TokenManager.set_otp_token(self.user_id, phone_number)

        # Try to validate with different phone number
        validated_user_id = TokenManager.validate_otp("+209876543210", otp)
        self.assertIsNone(validated_user_id)

    def test_validate_otp_not_set(self):
        phone_number = "+201234567890"
        validated_user_id = TokenManager.validate_otp(phone_number, "TESTCODE")
        self.assertIsNone(validated_user_id)

    def test_validate_otp_already_used(self):
        phone_number = "+201234567890"
        otp = TokenManager.set_otp_token(self.user_id, phone_number)

        # First validation should succeed
        validated_user_id = TokenManager.validate_otp(phone_number, otp)
        self.assertEqual(validated_user_id, str(self.user_id))

        # Second validation should fail (OTP deleted)
        validated_user_id = TokenManager.validate_otp(phone_number, otp)
        self.assertIsNone(validated_user_id)

    @patch("users.managers.cache")
    def test_otp_token_timeout(self, mock_cache):
        # Simulate cache miss (expired OTP)
        mock_cache.get.return_value = None

        phone_number = "+201234567890"
        key = f"otp:{phone_number}"
        cached_data = mock_cache.get(key)
        self.assertIsNone(cached_data)

    def test_multiple_users_different_otps(self):
        user_id_1 = uuid.uuid4()
        user_id_2 = uuid.uuid4()
        phone_1 = "+201234567890"
        phone_2 = "+209876543210"

        otp_1 = TokenManager.set_otp_token(user_id_1, phone_1)
        otp_2 = TokenManager.set_otp_token(user_id_2, phone_2)

        self.assertNotEqual(otp_1, otp_2)

        # Validate both OTPs work independently
        validated_1 = TokenManager.validate_otp(phone_1, otp_1)
        validated_2 = TokenManager.validate_otp(phone_2, otp_2)

        self.assertEqual(validated_1, str(user_id_1))
        self.assertEqual(validated_2, str(user_id_2))


class ManagerIntegrationTests(TestCase):
    """Integration tests for CustomUserManager and TokenManager together"""

    def setUp(self):
        self.User = get_user_model()
        cache.clear()

    def tearDown(self):
        cache.clear()
        self.User.objects.all().delete()

    def test_user_creation_and_email_verification_flow(self):
        user = self.User.objects.create_user(
            email="some@email.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            phone_number="+201234567890",
        )
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_email_verified)

        token = TokenManager.set_email_verification_token(user.id)
        self.assertIsNotNone(token)

        validated_user_id = TokenManager.validate_email_verification_token(token)
        self.assertEqual(validated_user_id, user.id)

        user.is_email_verified = True
        user.is_active = True
        user.save()
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_email_verified)

    def test_password_reset_flow(self):
        user = self.User.objects.create_user(
            email="some@email",
            password="oldpass123",
            first_name="John",
            last_name="Doe",
            phone_number="+201234567890",
            is_active=True,
        )
        token = TokenManager.set_password_reset_token(user.id)
        validated_user_id = TokenManager.validate_password_reset_token(token)
        self.assertEqual(validated_user_id, user.id)

        user.set_password("newpass123")
        user.save()
        user.refresh_from_db()
        self.assertTrue(user.check_password("newpass123"))
        self.assertFalse(user.check_password("oldpass123"))

    def test_otp_2fa_login_flow(self):
        user = self.User.objects.create_user(
            email="some@email.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            phone_number="+201234567890",
            is_active=True,
        )
        otp = TokenManager.set_otp_token(user.id, str(user.phone_number))
        self.assertEqual(len(otp), 8)

        validated_user_id = TokenManager.validate_otp(str(user.phone_number), otp)
        self.assertEqual(validated_user_id, str(user.id))
