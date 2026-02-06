"""
URL Configuration for the Menu app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    MenuSectionViewSet,
    MenuItemViewSet,
    OrderViewSet,
    CustomerActivityViewSet,
    MLServiceHealthView,
    PublicMenuView,
)

router = DefaultRouter()
router.register(r"sections", MenuSectionViewSet, basename="section")
router.register(r"items", MenuItemViewSet, basename="item")
router.register(r"orders", OrderViewSet, basename="order")
router.register(r"activities", CustomerActivityViewSet, basename="activity")

urlpatterns = [
    path("", include(router.urls)),
    path("ml/health/", MLServiceHealthView.as_view(), name="ml-health"),
    path(
        "public/", PublicMenuView.as_view(), name="public-menu"
    ),  # Customer-facing menu
]
