from django.test import TestCase
from django.contrib.auth import get_user_model

from rest_framework.test import APIRequestFactory

from users.permissions import (
    IsAdmin,
    IsAdminOrManager,
    IsEmailVerified,
    CanCreateUserType,
)


class IsAdminPermissionTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.factory = APIRequestFactory()
        self.permission = IsAdmin()

        self.admin_user = self.User.objects.create_user(
            email="admin@email.com",
            password="testpass123",
            first_name="Admin",
            last_name="User",
            phone_number="+201234567890",
            type="admin",
            is_active=True,
        )

        self.manager_user = self.User.objects.create_user(
            email="manager@email.com",
            password="testpass123",
            first_name="Manager",
            last_name="User",
            phone_number="+201234567891",
            type="manager",
            is_active=True,
        )

        self.staff_user = self.User.objects.create_user(
            email="staff@email.com",
            password="testpass123",
            first_name="Staff",
            last_name="User",
            phone_number="+201234567892",
            type="staff",
            is_active=True,
        )

    def test_admin_user_has_permission(self):
        request = self.factory.get("/")
        request.user = self.admin_user
        permission = self.permission.has_permission(request, None)
        self.assertTrue(permission)

    def test_manager_user_denied_permission(self):
        request = self.factory.get("/")
        request.user = self.manager_user
        permission = self.permission.has_permission(request, None)
        self.assertFalse(permission)

    def test_staff_user_denied_permission(self):
        request = self.factory.get("/")
        request.user = self.staff_user
        permission = self.permission.has_permission(request, None)
        self.assertFalse(permission)

    def test_unauthenticated_user_denied_permission(self):
        from django.contrib.auth.models import AnonymousUser

        request = self.factory.get("/")
        request.user = AnonymousUser()
        permission = self.permission.has_permission(request, None)
        self.assertFalse(permission)

    def test_permission_message(self):
        self.assertEqual(
            self.permission.message, "Only administrators can perform this action."
        )

    def test_admin_user_all_http_methods(self):
        methods = ["get", "post", "put", "patch", "delete"]
        for method in methods:
            with self.subTest(method=method):
                request = getattr(self.factory, method)("/")
                request.user = self.admin_user
                permission = self.permission.has_permission(request, None)
                self.assertTrue(permission)


class IsAdminOrManagerPermissionTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.factory = APIRequestFactory()
        self.permission = IsAdminOrManager()

        self.admin_user = self.User.objects.create_user(
            email="admin@email.com",
            password="testpass123",
            first_name="Admin",
            last_name="User",
            phone_number="+201234567890",
            type="admin",
            is_active=True,
        )

        self.manager_user = self.User.objects.create_user(
            email="manager@email.com",
            password="testpass123",
            first_name="Manager",
            last_name="User",
            phone_number="+201234567891",
            type="manager",
            is_active=True,
        )

        self.staff_user = self.User.objects.create_user(
            email="staff@email.com",
            password="testpass123",
            first_name="Staff",
            last_name="User",
            phone_number="+201234567892",
            type="staff",
            is_active=True,
        )

    def test_admin_user_has_permission(self):
        request = self.factory.get("/")
        request.user = self.admin_user
        permission = self.permission.has_permission(request, None)
        self.assertTrue(permission)

    def test_manager_user_has_permission(self):
        request = self.factory.get("/")
        request.user = self.manager_user
        permission = self.permission.has_permission(request, None)
        self.assertTrue(permission)

    def test_staff_user_denied_permission(self):
        request = self.factory.get("/")
        request.user = self.staff_user
        permission = self.permission.has_permission(request, None)
        self.assertFalse(permission)

    def test_unauthenticated_user_denied_permission(self):
        from django.contrib.auth.models import AnonymousUser

        request = self.factory.get("/")
        request.user = AnonymousUser()
        permission = self.permission.has_permission(request, None)
        self.assertFalse(permission)

    def test_permission_message(self):
        self.assertEqual(
            self.permission.message,
            "Only administrators or managers can perform this action.",
        )

    def test_admin_and_manager_all_http_methods(self):
        methods = ["get", "post", "put", "patch", "delete"]
        users = [self.admin_user, self.manager_user]

        for user in users:
            for method in methods:
                with self.subTest(user=user.type, method=method):
                    request = getattr(self.factory, method)("/")
                    request.user = user

                    permission = self.permission.has_permission(request, None)
                    self.assertTrue(permission)


class IsEmailVerifiedPermissionTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.factory = APIRequestFactory()
        self.permission = IsEmailVerified()

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
            password="testpass123",
            first_name="Unverified",
            last_name="User",
            phone_number="+201234567891",
            is_active=True,
            is_email_verified=False,
        )

    def test_verified_user_has_permission(self):
        request = self.factory.get("/")
        request.user = self.verified_user
        permission = self.permission.has_permission(request, None)
        self.assertTrue(permission)

    def test_unverified_user_denied_permission(self):
        request = self.factory.get("/")
        request.user = self.unverified_user
        permission = self.permission.has_permission(request, None)
        self.assertFalse(permission)

    def test_unauthenticated_user_denied_permission(self):
        from django.contrib.auth.models import AnonymousUser

        request = self.factory.get("/")
        request.user = AnonymousUser()
        permission = self.permission.has_permission(request, None)
        self.assertFalse(permission)

    def test_permission_message(self):
        self.assertEqual(
            self.permission.message, "Email verification required for this action."
        )

    def test_verified_user_all_http_methods(self):
        methods = ["get", "post", "put", "patch", "delete"]
        for method in methods:
            with self.subTest(method=method):
                request = getattr(self.factory, method)("/")
                request.user = self.verified_user
                permission = self.permission.has_permission(request, None)
                self.assertTrue(permission)

    def test_admin_user_with_verified_email(self):
        admin_user = self.User.objects.create_user(
            email="[email protected]",
            password="testpass123",
            first_name="Admin",
            last_name="User",
            phone_number="+201234567892",
            type="admin",
            is_active=True,
            is_email_verified=True,
        )

        request = self.factory.get("/")
        request.user = admin_user

        permission = self.permission.has_permission(request, None)
        self.assertTrue(permission)

    def test_admin_user_without_verified_email_denied(self):
        admin_user = self.User.objects.create_user(
            email="[email protected]",
            password="testpass123",
            first_name="Admin",
            last_name="User",
            phone_number="+201234567893",
            type="admin",
            is_active=True,
            is_email_verified=False,
        )

        request = self.factory.get("/")
        request.user = admin_user

        permission = self.permission.has_permission(request, None)
        self.assertFalse(permission)


class CanCreateUserTypePermissionTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.factory = APIRequestFactory()
        self.permission = CanCreateUserType()

        # Create test users
        self.admin_user = self.User.objects.create_user(
            email="admin@email.com",
            password="testpass123",
            first_name="Admin",
            last_name="User",
            phone_number="+201234567890",
            type="admin",
            is_active=True,
        )

        self.manager_user = self.User.objects.create_user(
            email="manager@email.com",
            password="testpass123",
            first_name="Manager",
            last_name="User",
            phone_number="+201234567891",
            type="manager",
            is_active=True,
        )

        self.staff_user = self.User.objects.create_user(
            email="staff@email.com",
            password="testpass123",
            first_name="Staff",
            last_name="User",
            phone_number="+201234567892",
            type="staff",
            is_active=True,
        )

    def _wrap_request(self, request, user):
        from rest_framework.request import Request
        from rest_framework.parsers import JSONParser, FormParser, MultiPartParser

        drf_request = Request(
            request, parsers=[JSONParser(), FormParser(), MultiPartParser()]
        )
        drf_request.user = user
        return drf_request

    def test_admin_can_create_manager(self):
        request = self.factory.post("/", {"type": "manager"}, format="json")
        request = self._wrap_request(request, self.admin_user)
        permission = self.permission.has_permission(request, None)
        self.assertTrue(permission)

    def test_admin_can_create_staff(self):
        request = self.factory.post("/", {"type": "staff"}, format="json")
        request = self._wrap_request(request, self.admin_user)
        permission = self.permission.has_permission(request, None)
        self.assertTrue(permission)

    def test_admin_cannot_create_admin(self):
        request = self.factory.post("/", {"type": "admin"}, format="json")
        request = self._wrap_request(request, self.admin_user)
        permission = self.permission.has_permission(request, None)
        self.assertFalse(permission)

    def test_admin_creates_staff_by_default(self):
        request = self.factory.post("/", {}, format="json")
        request = self._wrap_request(request, self.admin_user)
        permission = self.permission.has_permission(request, None)
        self.assertTrue(permission)

    # Manager user tests
    def test_manager_can_create_staff(self):
        request = self.factory.post("/", {"type": "staff"}, format="json")
        request = self._wrap_request(request, self.manager_user)
        permission = self.permission.has_permission(request, None)
        self.assertTrue(permission)

    def test_manager_cannot_create_manager(self):
        request = self.factory.post("/", {"type": "manager"}, format="json")
        request = self._wrap_request(request, self.manager_user)
        permission = self.permission.has_permission(request, None)
        self.assertFalse(permission)

    def test_manager_cannot_create_admin(self):
        request = self.factory.post("/", {"type": "admin"}, format="json")
        request = self._wrap_request(request, self.manager_user)
        permission = self.permission.has_permission(request, None)
        self.assertFalse(permission)

    def test_manager_creates_staff_by_default(self):
        request = self.factory.post("/", {}, format="json")
        request = self._wrap_request(request, self.manager_user)
        permission = self.permission.has_permission(request, None)
        self.assertTrue(permission)

    # Staff user tests
    def test_staff_cannot_create_staff(self):
        request = self.factory.post("/", {"type": "staff"}, format="json")
        request = self._wrap_request(request, self.staff_user)
        permission = self.permission.has_permission(request, None)
        self.assertFalse(permission)

    def test_staff_cannot_create_manager(self):
        request = self.factory.post("/", {"type": "manager"}, format="json")
        request = self._wrap_request(request, self.staff_user)
        permission = self.permission.has_permission(request, None)
        self.assertFalse(permission)

    def test_staff_cannot_create_admin(self):
        request = self.factory.post("/", {"type": "admin"}, format="json")
        request = self._wrap_request(request, self.staff_user)
        permission = self.permission.has_permission(request, None)
        self.assertFalse(permission)

    def test_staff_cannot_create_default_type(self):
        request = self.factory.post("/", {}, format="json")
        request = self._wrap_request(request, self.staff_user)
        permission = self.permission.has_permission(request, None)
        self.assertFalse(permission)

    # Unauthenticated user tests
    def test_unauthenticated_user_denied_permission(self):
        from django.contrib.auth.models import AnonymousUser

        request = self.factory.post("/", {"type": "staff"}, format="json")
        request = self._wrap_request(request, AnonymousUser())
        permission = self.permission.has_permission(request, None)
        self.assertFalse(permission)

    # Permission message test
    def test_permission_message(self):
        self.assertEqual(
            self.permission.message,
            "You do not have permission to create this user type.",
        )

    # Edge cases
    def test_invalid_user_type_string(self):
        request = self.factory.post("/", {"type": "invalid"}, format="json")
        request = self._wrap_request(request, self.admin_user)
        permission = self.permission.has_permission(request, None)
        self.assertFalse(permission)

    def test_empty_string_user_type(self):
        request = self.factory.post("/", {"type": ""}, format="json")
        request = self._wrap_request(request, self.admin_user)
        permission = self.permission.has_permission(request, None)
        self.assertFalse(permission)

    def test_none_user_type_defaults_to_staff(self):
        request = self.factory.post("/", {"type": None}, format="json")
        request = self._wrap_request(request, self.admin_user)
        permission = self.permission.has_permission(request, None)
        self.assertTrue(permission)

    def test_case_sensitive_user_type(self):
        request = self.factory.post("/", {"type": "Manager"}, format="json")
        request = self._wrap_request(request, self.admin_user)
        permission = self.permission.has_permission(request, None)
        self.assertFalse(permission)

    # Test with different HTTP methods
    def test_permission_with_put_request(self):
        request = self.factory.put("/", {"type": "staff"}, format="json")
        request = self._wrap_request(request, self.admin_user)
        permission = self.permission.has_permission(request, None)
        self.assertTrue(permission)

    def test_permission_with_patch_request(self):
        request = self.factory.patch("/", {"type": "manager"}, format="json")
        request = self._wrap_request(request, self.admin_user)
        permission = self.permission.has_permission(request, None)
        self.assertTrue(permission)

    # Hierarchical permission tests
    def test_permission_hierarchy_admin_over_manager(self):
        request = self.factory.post("/", {"type": "manager"}, format="json")
        request = self._wrap_request(request, self.admin_user)
        self.assertTrue(self.permission.has_permission(request, None))

    def test_permission_hierarchy_manager_cannot_create_manager(self):
        request = self.factory.post("/", {"type": "manager"}, format="json")
        request = self._wrap_request(request, self.manager_user)
        self.assertFalse(self.permission.has_permission(request, None))

    def test_permission_hierarchy_manager_over_staff(self):
        request = self.factory.post("/", {"type": "staff"}, format="json")
        request = self._wrap_request(request, self.manager_user)
        self.assertTrue(self.permission.has_permission(request, None))

    def test_permission_hierarchy_staff_cannot_create_staff(self):
        request = self.factory.post("/", {"type": "staff"}, format="json")
        request = self._wrap_request(request, self.staff_user)
        self.assertFalse(self.permission.has_permission(request, None))
