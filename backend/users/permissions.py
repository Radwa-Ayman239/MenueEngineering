"""
Custom permission classes for role-based access control.
"""

from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    message = "Only administrators can perform this action."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.type == "admin"


class IsAdminOrManager(BasePermission):
    message = "Only administrators or managers can perform this action."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.type in [
            "admin",
            "manager",
        ]


class IsEmailVerified(BasePermission):
    message = "Email verification required for this action."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_email_verified


class CanCreateUserType(BasePermission):
    message = "You do not have permission to create this user type."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        user_type_to_create = request.data.get("type")

        if user_type_to_create is None:
            user_type_to_create = "staff"
        elif user_type_to_create == "":
            return False

        requester_type = request.user.type

        if requester_type == "admin":
            return user_type_to_create in ["manager", "staff"]
        elif requester_type == "manager":
            return user_type_to_create == "staff"

        return False
