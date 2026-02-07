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
    # AI-Powered Views
    EnhanceDescriptionView,
    SalesSuggestionsView,
    MenuStructureAnalysisView,
    CustomerRecommendationsView,
    OwnerReportView,
)

app_name = "menu"

router = DefaultRouter()
router.register(r"sections", MenuSectionViewSet, basename="section")
router.register(r"items", MenuItemViewSet, basename="item")
router.register(r"orders", OrderViewSet, basename="order")
router.register(r"activities", CustomerActivityViewSet, basename="activity")

urlpatterns = [
    path("", include(router.urls)),
    path("ml/health/", MLServiceHealthView.as_view(), name="ml-health"),
    path("public/", PublicMenuView.as_view(), name="public-menu"),
    # AI-Powered Endpoints
    path(
        "ai/enhance-description/",
        EnhanceDescriptionView.as_view(),
        name="ai-enhance-description",
    ),
    path(
        "ai/sales-suggestions/",
        SalesSuggestionsView.as_view(),
        name="ai-sales-suggestions",
    ),
    path(
        "ai/menu-analysis/",
        MenuStructureAnalysisView.as_view(),
        name="ai-menu-analysis",
    ),
    path(
        "ai/recommendations/",
        CustomerRecommendationsView.as_view(),
        name="ai-recommendations",
    ),
    path("ai/owner-report/", OwnerReportView.as_view(), name="ai-owner-report"),
]
