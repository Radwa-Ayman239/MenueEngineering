"""
Custom permission classes for the Menu app.
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrManager(BasePermission):
    """
    Only administrators or managers can perform this action.
    """

    message = "Only administrators or managers can perform this action."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.type in [
            "admin",
            "manager",
        ]


class IsStaffOrAbove(BasePermission):
    """
    Any authenticated staff member (staff, manager, admin) can perform this action.
    """

    message = "Only staff members can perform this action."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.type in [
            "admin",
            "manager",
            "staff",
        ]


class IsManagerOrReadOnly(BasePermission):
    """
    Managers/Admins have full access.
    Others have read-only access (including unauthenticated).
    """

    message = "Only managers can modify menu items."

    def has_permission(self, request, view):
        # Read-only methods are allowed for everyone
        if request.method in SAFE_METHODS:
            return True

        # Write operations require manager/admin
        return request.user.is_authenticated and request.user.type in [
            "admin",
            "manager",
        ]


class CanManageMenu(BasePermission):
    """
    Only managers and admins can manage menu (create, update, delete, analyze).
    """

    message = "Only managers can manage the menu."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.type in [
            "admin",
            "manager",
        ]


class CanCreateOrders(BasePermission):
    """
    Staff, managers, and admins can create orders.
    """

    message = "Only staff members can create orders."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.type in [
            "admin",
            "manager",
            "staff",
        ]


class CanViewAnalytics(BasePermission):
    """
    Only managers and admins can view analytics and statistics.
    """

    message = "Only managers can view analytics."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.type in [
            "admin",
            "manager",
        ]
