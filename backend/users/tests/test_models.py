from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError


class CustomUserModelTests(TestCase):
    def setUp(self):
        self.User = get_user_model()

    def test_create_user_with_email(self):
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
        self.assertTrue(user.check_password("testpass123"))
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_user_email_normalized(self):
        email = "some@email"
        user = self.User.objects.create_user(
            email=email,
            password="testpass123",
            first_name="John",
            last_name="Doe",
            phone_number="+201234567890",
        )
        self.assertEqual(user.email, email.lower())

    def test_create_user_without_email_raises_error(self):
        with self.assertRaises(ValueError):
            self.User.objects.create_user(
                email="",
                password="testpass123",
                first_name="John",
                last_name="Doe",
                phone_number="+201234567890",
            )

    def test_create_user_without_first_name_raises_error(self):
        with self.assertRaises(ValueError):
            self.User.objects.create_user(
                email="some@email.com",
                password="testpass123",
                first_name="",
                last_name="Doe",
                phone_number="+201234567890",
            )

    def test_create_user_without_last_name_raises_error(self):
        with self.assertRaises(ValueError):
            self.User.objects.create_user(
                email="some@email.com",
                password="testpass123",
                first_name="John",
                last_name="",
                phone_number="+201234567890",
            )

    def test_create_user_without_phone_number_raises_error(self):
        """Test that phone_number is required for 2FA"""
        with self.assertRaises(ValueError):
            self.User.objects.create_user(
                email="some@email.com",
                password="testpass123",
                first_name="John",
                last_name="Doe",
            )

    def test_create_superuser(self):
        admin_user = self.User.objects.create_superuser(
            email="admin@email.com",
            password="testpass123",
            first_name="Admin",
            last_name="User",
            phone_number="+201234567890",
        )
        self.assertEqual(admin_user.email, "admin@email.com")
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)

    def test_create_superuser_with_is_staff_false_raises_error(self):
        with self.assertRaises(ValueError):
            self.User.objects.create_superuser(
                email="admin@email.com",
                password="testpass123",
                first_name="Admin",
                last_name="User",
                phone_number="+201234567890",
                is_staff=False,
            )

    def test_create_superuser_with_is_superuser_false_raises_error(self):
        """Test creating superuser with is_superuser=False raises ValueError"""
        with self.assertRaises(ValueError):
            self.User.objects.create_superuser(
                email="admin@email.com",
                password="testpass123",
                first_name="Admin",
                last_name="User",
                phone_number="+201234567890",
                is_superuser=False,
            )

    def test_email_unique_constraint(self):
        self.User.objects.create_user(
            email="admin@email.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            phone_number="+201234567890",
        )
        with self.assertRaises(IntegrityError):
            self.User.objects.create_user(
                email="admin@email.com",
                password="testpass123",
                first_name="Jane",
                last_name="Smith",
                phone_number="+201234567891",
            )

    def test_username_field_is_email(self):
        self.assertEqual(self.User.USERNAME_FIELD, "email")

    def test_username_is_none(self):
        user = self.User.objects.create_user(
            email="admin@email",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            phone_number="+201234567890",
        )
        self.assertIsNone(user.username)

    def test_default_user_type_is_staff(self):
        user = self.User.objects.create_user(
            email="some@email.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            phone_number="+201234567890",
        )
        self.assertEqual(user.type, self.User.UserTypes.STAFF)

    def test_user_type_choices(self):
        """Test all user type choices"""
        # Test ADMIN type
        admin = self.User.objects.create_user(
            email="admin@email.com",
            password="testpass123",
            first_name="Admin",
            last_name="User",
            phone_number="+201234567890",
            type=self.User.UserTypes.ADMIN,
        )
        self.assertEqual(admin.type, "admin")

        # Test MANAGER type
        manager = self.User.objects.create_user(
            email="manager@email.com",
            password="testpass123",
            first_name="Manager",
            last_name="User",
            phone_number="+201234567891",
            type=self.User.UserTypes.MANAGER,
        )
        self.assertEqual(manager.type, "manager")

        # Test STAFF type
        staff = self.User.objects.create_user(
            email="staff@email.com",
            password="testpass123",
            first_name="Staff",
            last_name="User",
            phone_number="+201234567892",
            type=self.User.UserTypes.STAFF,
        )
        self.assertEqual(staff.type, "staff")

    def test_is_email_verified_default_false(self):
        user = self.User.objects.create_user(
            email="some@email.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            phone_number="+201234567890",
        )
        self.assertFalse(user.is_email_verified)

    def test_set_email_verified(self):
        """Test setting email verification status"""
        user = self.User.objects.create_user(
            email="some@email.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            phone_number="+201234567890",
        )
        user.is_email_verified = True
        user.save()
        user.refresh_from_db()
        self.assertTrue(user.is_email_verified)

    def test_phone_number_with_value(self):
        """Test creating user with phone number"""
        user = self.User.objects.create_user(
            email="some@email.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            phone_number="+201234567890",
        )
        self.assertEqual(str(user.phone_number), "+201234567890")

    def test_str_representation(self):
        """Test string representation of user"""
        user = self.User.objects.create_user(
            email="some@email.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            phone_number="+201234567890",
        )
        expected = "Doe, John - some@email.com (+201234567890)"
        self.assertEqual(str(user), expected)
    
    def test_first_name_max_length(self):
        max_length = self.User._meta.get_field('first_name').max_length
        self.assertEqual(max_length, 150)

    def test_last_name_max_length(self):
        max_length = self.User._meta.get_field('last_name').max_length
        self.assertEqual(max_length, 150)

    def test_type_max_length(self):
        max_length = self.User._meta.get_field('type').max_length
        self.assertEqual(max_length, 50)
    
    def test_user_id_is_uuid(self):
        """Test that user ID is a UUID"""
        user = self.User.objects.create_user(
            email="[email protected]",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            phone_number="+201234567890"
        )
        self.assertIsNotNone(user.id)
        self.assertEqual(len(str(user.id)), 36) 
