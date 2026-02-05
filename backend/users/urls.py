"""
URL configuration for users app.
"""

from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    # User management (Admin/Manager only)
    path("create/", views.CreateUserView.as_view(), name="create-user"),
    # Account activation
    path("activate/", views.ActivateAccountView.as_view(), name="activate"),
    path(
        "resend-activation/",
        views.ResendActivationView.as_view(),
        name="resend-activation",
    ),
    # 2FA Login
    path("login/", views.LoginStep1View.as_view(), name="login"),
    path("login/verify/", views.LoginStep2View.as_view(), name="login-verify"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    # Token management
    path("token/refresh/", views.RefreshTokenView.as_view(), name="token-refresh"),
    # Password reset
    path(
        "forgot-password/",
        views.ForgotPasswordRequestView.as_view(),
        name="forgot-password",
    ),
    path(
        "reset-password/",
        views.ForgotPasswordResetView.as_view(),
        name="reset-password",
    ),
]
