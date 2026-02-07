"""
Tests for AI-powered views.

Tests the AI endpoint views that call the ML service for:
- Description enhancement
- Sales suggestions
- Menu structure analysis
- Customer recommendations
- Owner reports
"""

from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from menu.models import MenuSection, MenuItem
from users.models import CustomUser


class AIViewTestBase(TestCase):
    """Base class for AI view tests with common setup."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()

        # Create users with different roles
        self.admin_user = CustomUser.objects.create_user(
            email="admin@test.com",
            password="adminpass123",
            type="admin",
            first_name="Admin",
            last_name="User",
            phone_number="+15555550000",
        )
        self.manager_user = CustomUser.objects.create_user(
            email="manager@test.com",
            password="managerpass123",
            type="manager",
            first_name="Manager",
            last_name="User",
            phone_number="+15555550001",
        )
        self.staff_user = CustomUser.objects.create_user(
            email="staff@test.com",
            password="staffpass123",
            type="staff",
            first_name="Staff",
            last_name="User",
            phone_number="+15555550002",
        )

        # Create menu data
        self.section = MenuSection.objects.create(
            name="Main Dishes",
            description="Our signature dishes",
            display_order=1,
        )
        self.menu_item = MenuItem.objects.create(
            section=self.section,
            title="Grilled Salmon",
            description="Fresh salmon with vegetables",
            price=24.99,
            cost=10.00,
            total_purchases=50,
            category="puzzle",
            is_active=True,
        )

    def login_as_admin(self):
        """Authenticate as admin user."""
        self.client.force_authenticate(user=self.admin_user)

    def login_as_manager(self):
        """Authenticate as manager user."""
        self.client.force_authenticate(user=self.manager_user)

    def login_as_staff(self):
        """Authenticate as staff user."""
        self.client.force_authenticate(user=self.staff_user)


class TestEnhanceDescriptionView(AIViewTestBase):
    """Tests for the EnhanceDescriptionView."""

    def get_url(self):
        return reverse("menu:ai-enhance-description")

    @patch("menu.services.ml_service.enhance_description_sync")
    def test_enhance_description_success(self, mock_enhance):
        """Test successful description enhancement."""
        mock_enhance.return_value = {
            "enhanced_description": "Succulent grilled salmon...",
            "key_selling_points": ["Fresh", "Healthy"],
            "tips": ["Pair with wine"],
        }

        self.login_as_manager()
        response = self.client.post(
            self.get_url(),
            {
                "item_name": "Grilled Salmon",
                "current_description": "Salmon with rice",
                "category": "Puzzle",
                "price": 24.99,
                "cuisine_type": "Seafood",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("enhanced_description", response.data)

    @patch("menu.services.ml_service.enhance_description_sync")
    def test_enhance_description_with_item_id(self, mock_enhance):
        """Test description enhancement using item_id to fetch details."""
        mock_enhance.return_value = {
            "enhanced_description": "Premium grilled salmon...",
            "key_selling_points": ["Fresh"],
            "tips": ["Upsell wine"],
        }

        self.login_as_manager()
        response = self.client.post(
            self.get_url(),
            {"item_id": str(self.menu_item.id)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should have used the item's details
        mock_enhance.assert_called_once()
        call_args = mock_enhance.call_args
        self.assertEqual(call_args.kwargs["item_name"], "Grilled Salmon")

    def test_enhance_description_unauthenticated(self):
        """Test that unauthenticated users cannot access."""
        response = self.client.post(
            self.get_url(),
            {"item_name": "Test"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_enhance_description_staff_forbidden(self):
        """Test that staff cannot access (managers only)."""
        self.login_as_staff()
        response = self.client.post(
            self.get_url(),
            {"item_name": "Test"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("menu.services.ml_service.enhance_description_sync")
    def test_enhance_description_ml_service_error(self, mock_enhance):
        """Test handling of ML service errors."""
        from menu.services import MLServiceError

        mock_enhance.side_effect = MLServiceError("Service unavailable")

        self.login_as_manager()
        response = self.client.post(
            self.get_url(),
            {"item_name": "Grilled Salmon"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)


class TestSalesSuggestionsView(AIViewTestBase):
    """Tests for the SalesSuggestionsView."""

    def get_url(self):
        return reverse("menu:ai-sales-suggestions")

    @patch("menu.services.ml_service.get_sales_suggestions_sync")
    def test_sales_suggestions_success(self, mock_suggestions):
        """Test successful sales suggestions."""
        mock_suggestions.return_value = {
            "priority": "medium",
            "suggested_price": 27.99,
            "immediate_actions": ["Add description"],
            "marketing_tips": ["Feature on specials"],
            "estimated_impact": "15% increase",
        }

        self.login_as_manager()
        response = self.client.post(
            self.get_url(),
            {
                "item_name": "Grilled Salmon",
                "category": "Puzzle",
                "price": 24.99,
                "cost": 10.00,
                "purchases": 50,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("priority", response.data)

    @patch("menu.services.ml_service.get_sales_suggestions_sync")
    def test_sales_suggestions_with_item_id(self, mock_suggestions):
        """Test sales suggestions using item_id."""
        mock_suggestions.return_value = {
            "priority": "high",
            "suggested_price": 29.99,
            "immediate_actions": [],
            "marketing_tips": [],
        }

        self.login_as_admin()
        response = self.client.post(
            self.get_url(),
            {"item_id": str(self.menu_item.id)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_sales_suggestions_missing_required_fields(self):
        """Test validation of required fields."""
        self.login_as_manager()
        response = self.client.post(
            self.get_url(),
            {"item_name": "Test"},  # Missing required fields
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestMenuStructureAnalysisView(AIViewTestBase):
    """Tests for the MenuStructureAnalysisView."""

    def get_url(self):
        return reverse("menu:ai-menu-analysis")

    @patch("menu.services.ml_service.analyze_menu_structure_sync")
    def test_menu_structure_auto_fetch(self, mock_structure):
        """Test auto-fetching menu structure from database."""
        mock_structure.return_value = {
            "overall_score": 7,
            "section_order_recommendation": ["Main Dishes"],
            "items_to_highlight": ["Grilled Salmon"],
            "items_to_reconsider": [],
            "general_recommendations": ["Add more variety"],
        }

        self.login_as_manager()
        response = self.client.post(self.get_url(), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_structure.assert_called_once()

    @patch("menu.services.ml_service.analyze_menu_structure_sync")
    def test_menu_structure_with_provided_sections(self, mock_structure):
        """Test with manually provided sections."""
        mock_structure.return_value = {
            "overall_score": 8,
            "section_order_recommendation": ["Apps", "Mains"],
            "items_to_highlight": [],
            "items_to_reconsider": [],
            "general_recommendations": [],
        }

        self.login_as_manager()
        response = self.client.post(
            self.get_url(),
            {
                "sections": [
                    {
                        "name": "Appetizers",
                        "items": [{"name": "Wings", "price": 12.99}],
                    }
                ]
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestCustomerRecommendationsView(AIViewTestBase):
    """Tests for the CustomerRecommendationsView."""

    def get_url(self):
        return reverse("menu:ai-recommendations")

    @patch("menu.services.ml_service.get_customer_recommendations_sync")
    def test_customer_recommendations_public_access(self, mock_recs):
        """Test that endpoint is publicly accessible (for customers)."""
        mock_recs.return_value = {
            "top_recommendation": {
                "item": "Cheesecake",
                "reason": "Perfect dessert pairing",
                "pitch": "End your meal with our signature cheesecake!",
            },
            "alternatives": [],
            "upsells": [],
        }

        # No authentication
        response = self.client.post(
            self.get_url(),
            {
                "current_items": ["Burger", "Fries"],
                "budget_remaining": 15.00,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("top_recommendation", response.data)

    @patch("menu.services.ml_service.get_customer_recommendations_sync")
    def test_customer_recommendations_auto_fetch_menu(self, mock_recs):
        """Test that menu items are auto-fetched if not provided."""
        mock_recs.return_value = {
            "top_recommendation": {
                "item": "Salmon",
                "reason": "Healthy",
                "pitch": "Try it!",
            },
            "alternatives": [],
            "upsells": [],
        }

        response = self.client.post(
            self.get_url(),
            {"current_items": ["Burger"]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should have auto-fetched active menu items
        call_args = mock_recs.call_args
        self.assertIn("menu_items", call_args.kwargs)


class TestOwnerReportView(AIViewTestBase):
    """Tests for the OwnerReportView."""

    def get_url(self):
        return reverse("menu:ai-owner-report")

    @patch("menu.services.ml_service.generate_owner_report_sync")
    def test_owner_report_success(self, mock_report):
        """Test successful report generation."""
        mock_report.return_value = {
            "executive_summary": "Strong week with growth in key areas.",
            "highlights": ["Sales up 15%"],
            "concerns": [],
            "top_recommendations": ["Focus on Puzzle items"],
            "next_steps": ["Review pricing"],
        }

        self.login_as_manager()
        response = self.client.post(
            self.get_url(),
            {"period": "weekly"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("executive_summary", response.data)

    @patch("menu.services.ml_service.generate_owner_report_sync")
    def test_owner_report_auto_generates_summary(self, mock_report):
        """Test that summary data is auto-generated if not provided."""
        mock_report.return_value = {
            "executive_summary": "Good performance.",
            "highlights": [],
            "concerns": [],
            "top_recommendations": [],
            "next_steps": [],
        }

        self.login_as_admin()
        response = self.client.post(
            self.get_url(),
            {},  # No summary_data provided
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should have auto-generated summary_data
        call_args = mock_report.call_args
        self.assertIn("summary_data", call_args.kwargs)

    def test_owner_report_staff_forbidden(self):
        """Test that staff cannot access owner reports."""
        self.login_as_staff()
        response = self.client.post(
            self.get_url(),
            {"period": "weekly"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TestAnalyzeEndpoints(AIViewTestBase):
    """Tests for the analyze and bulk_analyze endpoints that use local classifier."""

    def test_analyze_single_item(self):
        """Test analyzing a single menu item."""
        self.login_as_manager()
        response = self.client.post(
            reverse("menu:item-analyze", kwargs={"pk": self.menu_item.pk}),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("category", response.data)
        self.assertIn("confidence", response.data)
        self.assertIn("recommendations", response.data)
        self.assertIn("metrics", response.data)

        # Verify item was updated
        self.menu_item.refresh_from_db()
        self.assertIsNotNone(self.menu_item.category)
        self.assertIsNotNone(self.menu_item.ai_confidence)
        self.assertIsNotNone(self.menu_item.last_analyzed)

    def test_analyze_unauthenticated(self):
        """Test that analyze requires authentication."""
        response = self.client.post(
            reverse("menu:item-analyze", kwargs={"pk": self.menu_item.pk}),
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_bulk_analyze(self):
        """Test bulk analyzing all active items."""
        # Create additional items
        MenuItem.objects.create(
            section=self.section,
            title="Steak",
            price=35.99,
            cost=15.00,
            total_purchases=80,
            is_active=True,
        )
        MenuItem.objects.create(
            section=self.section,
            title="Soup",
            price=8.99,
            cost=3.00,
            total_purchases=10,
            is_active=True,
        )

        self.login_as_admin()
        response = self.client.post(reverse("menu:item-bulk-analyze"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("analyzed_count", response.data)
        self.assertEqual(response.data["analyzed_count"], 3)
        self.assertEqual(len(response.data["results"]), 3)

    def test_bulk_analyze_no_items(self):
        """Test bulk analyze with no active items."""
        MenuItem.objects.all().update(is_active=False)

        self.login_as_manager()
        response = self.client.post(reverse("menu:item-bulk-analyze"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)


class TestMLServiceHealthView(AIViewTestBase):
    """Tests for the ML Service health check endpoint."""

    def test_ml_health_public_access(self):
        """Test that ML health check is publicly accessible."""
        response = self.client.get(reverse("menu:ml-health"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("status", response.data)
