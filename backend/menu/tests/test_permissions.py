from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser
from unittest.mock import Mock
from ..permissions import (
    IsAdminOrManager,
    IsStaffOrAbove,
    IsManagerOrReadOnly,
    CanManageMenu,
    CanCreateOrders,
    CanViewAnalytics,
)


class PermissionTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.view = (
            Mock()
        )  # Permissions require a view argument, but we don't need its internal logic

    def _get_request(self, method="GET", user_type=None, is_authenticated=True):
        """Helper to create a request with a specific user type."""
        request = self.factory.generic(method, "/")

        if not is_authenticated:
            request.user = AnonymousUser()
        else:
            # Mock the User object and the 'type' attribute
            request.user = Mock()
            request.user.is_authenticated = True
            request.user.type = user_type

        return request

    # ==========================================
    # Test: IsAdminOrManager
    # ==========================================
    def test_is_admin_or_manager(self):
        permission = IsAdminOrManager()

        # Allowed
        self.assertTrue(
            permission.has_permission(self._get_request(user_type="admin"), self.view)
        )
        self.assertTrue(
            permission.has_permission(self._get_request(user_type="manager"), self.view)
        )

        # Denied
        self.assertFalse(
            permission.has_permission(self._get_request(user_type="staff"), self.view)
        )
        self.assertFalse(
            permission.has_permission(
                self._get_request(user_type="customer"), self.view
            )
        )
        self.assertFalse(
            permission.has_permission(
                self._get_request(is_authenticated=False), self.view
            )
        )

    # ==========================================
    # Test: IsStaffOrAbove
    # ==========================================
    def test_is_staff_or_above(self):
        permission = IsStaffOrAbove()

        # Allowed
        self.assertTrue(
            permission.has_permission(self._get_request(user_type="admin"), self.view)
        )
        self.assertTrue(
            permission.has_permission(self._get_request(user_type="manager"), self.view)
        )
        self.assertTrue(
            permission.has_permission(self._get_request(user_type="staff"), self.view)
        )

        # Denied
        self.assertFalse(
            permission.has_permission(
                self._get_request(user_type="customer"), self.view
            )
        )
        self.assertFalse(
            permission.has_permission(
                self._get_request(is_authenticated=False), self.view
            )
        )

    # ==========================================
    # Test: IsManagerOrReadOnly
    # ==========================================
    def test_is_manager_or_read_only_safe_methods(self):
        """Test that SAFE methods (GET, HEAD, OPTIONS) are allowed for everyone."""
        permission = IsManagerOrReadOnly()
        safe_methods = ["GET", "HEAD", "OPTIONS"]

        for method in safe_methods:
            # Anonymous
            request = self._get_request(method=method, is_authenticated=False)
            self.assertTrue(
                permission.has_permission(request, self.view),
                f"Failed for Anon on {method}",
            )

            # Staff (Non-Manager)
            request = self._get_request(method=method, user_type="staff")
            self.assertTrue(
                permission.has_permission(request, self.view),
                f"Failed for Staff on {method}",
            )

    def test_is_manager_or_read_only_unsafe_methods(self):
        """Test that UNSAFE methods (POST, PUT, DELETE) are restricted."""
        permission = IsManagerOrReadOnly()
        unsafe_methods = ["POST", "PUT", "DELETE", "PATCH"]

        for method in unsafe_methods:
            # Allowed: Manager & Admin
            self.assertTrue(
                permission.has_permission(
                    self._get_request(method=method, user_type="manager"), self.view
                )
            )
            self.assertTrue(
                permission.has_permission(
                    self._get_request(method=method, user_type="admin"), self.view
                )
            )

            # Denied: Staff & Anonymous
            self.assertFalse(
                permission.has_permission(
                    self._get_request(method=method, user_type="staff"), self.view
                )
            )
            self.assertFalse(
                permission.has_permission(
                    self._get_request(method=method, is_authenticated=False), self.view
                )
            )

    # ==========================================
    # Test: CanManageMenu
    # ==========================================
    def test_can_manage_menu(self):
        """Should mimic AdminOrManager logic."""
        permission = CanManageMenu()

        self.assertTrue(
            permission.has_permission(self._get_request(user_type="manager"), self.view)
        )
        self.assertTrue(
            permission.has_permission(self._get_request(user_type="admin"), self.view)
        )

        self.assertFalse(
            permission.has_permission(self._get_request(user_type="staff"), self.view)
        )

    # ==========================================
    # Test: CanCreateOrders
    # ==========================================
    def test_can_create_orders(self):
        """Should mimic StaffOrAbove logic."""
        permission = CanCreateOrders()

        self.assertTrue(
            permission.has_permission(self._get_request(user_type="staff"), self.view)
        )
        self.assertTrue(
            permission.has_permission(self._get_request(user_type="manager"), self.view)
        )

        self.assertFalse(
            permission.has_permission(
                self._get_request(user_type="customer"), self.view
            )
        )
        self.assertFalse(
            permission.has_permission(
                self._get_request(is_authenticated=False), self.view
            )
        )

    # ==========================================
    # Test: CanViewAnalytics
    # ==========================================
    def test_can_view_analytics(self):
        """Should mimic AdminOrManager logic."""
        permission = CanViewAnalytics()

        self.assertTrue(
            permission.has_permission(self._get_request(user_type="manager"), self.view)
        )
        self.assertTrue(
            permission.has_permission(self._get_request(user_type="admin"), self.view)
        )

        self.assertFalse(
            permission.has_permission(self._get_request(user_type="staff"), self.view)
        )
