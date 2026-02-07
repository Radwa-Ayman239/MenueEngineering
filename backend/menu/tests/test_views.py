"""
Extended view tests for increased coverage.
Tests filtering, edge cases, error handling, and all endpoints.
"""

from decimal import Decimal
from unittest.mock import patch, Mock
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from ..models import MenuSection, MenuItem, Order, OrderItem, CustomerActivity

User = get_user_model()


class BaseViewTest(APITestCase):
    def setUp(self):
        # Users
        self.admin = User.objects.create_user(
            email="admin@test.com",
            password="pw",
            first_name="Admin",
            last_name="User",
            phone_number="+0000000000",
            type="admin",
        )
        self.manager = User.objects.create_user(
            email="manager@test.com",
            password="pw",
            first_name="Manager",
            last_name="User",
            phone_number="+1111111111",
            type="manager",
        )
        self.staff = User.objects.create_user(
            email="staff@test.com",
            password="pw",
            first_name="Staff",
            last_name="User",
            phone_number="+2222222222",
            type="staff",
        )
        self.staff_2 = User.objects.create_user(
            email="staff2@test.com",
            password="pw",
            first_name="Staff",
            last_name="Two",
            phone_number="+3333333333",
            type="staff",
        )

        # Data
        self.section = MenuSection.objects.create(name="Mains", display_order=1)
        self.inactive_section = MenuSection.objects.create(
            name="Seasonal", display_order=2, is_active=False
        )
        self.item = MenuItem.objects.create(
            title="Burger",
            price=Decimal("10.00"),
            cost=Decimal("5.00"),
            section=self.section,
            description="Tasty burger",
        )
        self.inactive_item = MenuItem.objects.create(
            title="Old Item",
            price=Decimal("15.00"),
            cost=Decimal("8.00"),
            section=self.section,
            is_active=False,
        )


# ============ Menu Section Tests ============


class MenuSectionViewTests(BaseViewTest):
    def test_public_list_sections(self):
        """Anyone can list sections."""
        url = reverse("menu:section-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Only active sections for anonymous
        self.assertEqual(len(response.data), 1)

    def test_manager_sees_inactive_sections(self):
        """Managers can see all sections including inactive."""
        self.client.force_authenticate(user=self.manager)
        url = reverse("menu:section-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_filter_sections_by_active(self):
        """Test filtering sections by is_active query param."""
        self.client.force_authenticate(user=self.manager)
        url = reverse("menu:section-list") + "?is_active=false"
        response = self.client.get(url)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Seasonal")

    def test_manager_create_section(self):
        """Managers can create sections."""
        self.client.force_authenticate(user=self.manager)
        url = reverse("menu:section-list")
        data = {"name": "Drinks", "display_order": 2}

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MenuSection.objects.count(), 3)

    def test_admin_create_section(self):
        """Admins can create sections."""
        self.client.force_authenticate(user=self.admin)
        url = reverse("menu:section-list")
        data = {"name": "Appetizers", "display_order": 0}

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_staff_cannot_create_section(self):
        """Staff cannot create sections."""
        self.client.force_authenticate(user=self.staff)
        url = reverse("menu:section-list")
        data = {"name": "Dessert"}

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_public_cannot_create_section(self):
        """Anonymous cannot create sections."""
        url = reverse("menu:section-list")
        data = {"name": "Dessert"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_manager_update_section(self):
        """Managers can update sections."""
        self.client.force_authenticate(user=self.manager)
        url = reverse("menu:section-detail", args=[self.section.id])
        data = {"name": "Main Courses", "display_order": 1}

        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.section.refresh_from_db()
        self.assertEqual(self.section.name, "Main Courses")

    def test_manager_delete_section(self):
        """Managers can delete sections."""
        self.client.force_authenticate(user=self.manager)
        url = reverse("menu:section-detail", args=[self.inactive_section.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(MenuSection.objects.count(), 1)

    def test_retrieve_section(self):
        """Anyone can retrieve section details."""
        url = reverse("menu:section-detail", args=[self.section.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Mains")


# ============ Menu Item Tests ============


class MenuItemViewTests(BaseViewTest):
    def test_public_list_items(self):
        """Anyone can list items."""
        url = reverse("menu:item-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Only active items for anonymous
        self.assertEqual(len(response.data), 1)

    def test_manager_sees_inactive_items(self):
        """Managers see all items including inactive."""
        self.client.force_authenticate(user=self.manager)
        url = reverse("menu:item-list")
        response = self.client.get(url)
        self.assertEqual(len(response.data), 2)

    def test_filter_items_by_section(self):
        """Test filtering items by section."""
        url = reverse("menu:item-list") + f"?section={self.section.id}"
        response = self.client.get(url)
        self.assertEqual(len(response.data), 1)

    def test_filter_items_by_category(self):
        """Test filtering items by category."""
        self.item.category = "star"
        self.item.save()

        url = reverse("menu:item-list") + "?category=star"
        response = self.client.get(url)
        self.assertEqual(len(response.data), 1)

    def test_filter_items_by_active(self):
        """Test filtering items by is_active."""
        self.client.force_authenticate(user=self.manager)
        url = reverse("menu:item-list") + "?is_active=false"
        response = self.client.get(url)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Old Item")

    def test_manager_create_item(self):
        """Managers can create items."""
        self.client.force_authenticate(user=self.manager)
        url = reverse("menu:item-list")
        data = {
            "title": "New Item",
            "price": "12.00",
            "cost": "6.00",
            "section": str(self.section.id),
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_staff_cannot_create_item(self):
        """Staff cannot create items."""
        self.client.force_authenticate(user=self.staff)
        url = reverse("menu:item-list")
        data = {
            "title": "New Item",
            "price": "12.00",
            "cost": "6.00",
            "section": str(self.section.id),
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_update_item(self):
        """Managers can update items."""
        self.client.force_authenticate(user=self.manager)
        url = reverse("menu:item-detail", args=[self.item.id])
        data = {"price": "15.00"}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.item.refresh_from_db()
        self.assertEqual(self.item.price, Decimal("15.00"))

    def test_manager_delete_item(self):
        """Managers can delete items."""
        self.client.force_authenticate(user=self.manager)
        url = reverse("menu:item-detail", args=[self.inactive_item.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_retrieve_item_detail(self):
        """Anyone can retrieve item details."""
        url = reverse("menu:item-detail", args=[self.item.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("margin", response.data)
        self.assertIn("margin_percentage", response.data)

    @patch("menu.views.classify_menu_item")
    def test_analyze_item_action(self, mock_classify):
        """Test the custom 'analyze' action with mocked local classifier."""
        mock_classify.return_value = {
            "category": "Star",
            "confidence": 0.99,
            "recommendations": ["Keep it"],
            "metrics": {},
        }

        self.client.force_authenticate(user=self.manager)
        url = reverse("menu:item-analyze", args=[self.item.id])
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check normalized category (frontend expects capitalized, model stores lowercase)
        # View returns whatever classifier returns, model sets lowercase.
        # Check response (mock return value)
        self.assertEqual(response.data["category"], "Star")

        self.item.refresh_from_db()
        self.assertEqual(self.item.category, "star")
        self.assertEqual(self.item.ai_confidence, 0.99)
        self.assertIsNotNone(self.item.last_analyzed)

    # test_analyze_item_ml_error removed as classification is now local/deterministic

    @patch("menu.views.classify_menu_items_batch")
    def test_bulk_analyze(self, mock_classify_batch):
        """Test bulk analyze endpoint."""
        mock_classify_batch.return_value = [
            {"category": "Star", "confidence": 0.95},
        ]

        self.client.force_authenticate(user=self.manager)
        url = reverse("menu:item-bulk-analyze")
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("analyzed_count", response.data)

    @patch("menu.views.classify_menu_items_batch")
    def test_bulk_analyze_empty(self, mock_classify_batch):
        """Test bulk analyze with no active items."""
        MenuItem.objects.update(is_active=False)

        self.client.force_authenticate(user=self.manager)
        url = reverse("menu:item-bulk-analyze")
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        mock_classify_batch.assert_not_called()

    def test_stats_permission(self):
        """Test stats permission levels."""
        url = reverse("menu:item-stats")

        # Public - 403
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Staff - 403
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Manager - 200
        self.client.force_authenticate(user=self.manager)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("categories", response.data)
        self.assertIn("total_items", response.data)


# ============ Order Tests ============


class OrderViewTests(BaseViewTest):
    def setUp(self):
        super().setUp()
        self.order = Order.objects.create(created_by=self.staff, total=10)

    def test_create_order(self):
        """Staff can create orders."""
        self.client.force_authenticate(user=self.staff)
        url = reverse("menu:order-list")
        data = {
            "table_number": "5",
            "items": [{"menu_item": str(self.item.id), "quantity": 2}],
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 2)

    def test_manager_create_order(self):
        """Managers can create orders."""
        self.client.force_authenticate(user=self.manager)
        url = reverse("menu:order-list")
        data = {
            "table_number": "1",
            "items": [{"menu_item": str(self.item.id), "quantity": 1}],
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_public_cannot_create_order(self):
        """Anonymous cannot create orders."""
        url = reverse("menu:order-list")
        data = {
            "table_number": "5",
            "items": [{"menu_item": str(self.item.id), "quantity": 1}],
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_staff_order_isolation(self):
        """Staff should only see their own orders."""
        Order.objects.create(created_by=self.staff_2, total=20)

        self.client.force_authenticate(user=self.staff)
        url = reverse("menu:order-list")
        response = self.client.get(url)

        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], str(self.order.id))

    def test_manager_sees_all_orders(self):
        """Managers can see all orders."""
        Order.objects.create(created_by=self.staff_2, total=20)

        self.client.force_authenticate(user=self.manager)
        url = reverse("menu:order-list")
        response = self.client.get(url)

        self.assertEqual(len(response.data), 2)

    def test_filter_orders_by_status(self):
        """Test filtering orders by status."""
        self.order.status = "completed"
        self.order.save()
        Order.objects.create(created_by=self.staff, status="pending")

        self.client.force_authenticate(user=self.manager)
        url = reverse("menu:order-list") + "?status=completed"
        response = self.client.get(url)
        self.assertEqual(len(response.data), 1)

    def test_filter_orders_by_date(self):
        """Test filtering orders by date range."""
        self.client.force_authenticate(user=self.manager)
        today = self.order.created_at.date().isoformat()
        url = reverse("menu:order-list") + f"?date_from={today}&date_to={today}"
        response = self.client.get(url)
        self.assertEqual(len(response.data), 1)

    def test_update_status(self):
        """Staff can update order status."""
        self.client.force_authenticate(user=self.staff)
        url = reverse("menu:order-update-status", args=[self.order.id])
        data = {"status": "preparing"}

        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "preparing")

    def test_retrieve_order_detail(self):
        """Staff can retrieve order details."""
        OrderItem.objects.create(
            order=self.order,
            menu_item=self.item,
            quantity=2,
            price_at_order=self.item.price,
        )

        self.client.force_authenticate(user=self.staff)
        url = reverse("menu:order-detail", args=[self.order.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("items", response.data)
        self.assertEqual(len(response.data["items"]), 1)

    def test_order_stats_manager_only(self):
        """Only managers can view order stats."""
        url = reverse("menu:order-stats")

        # Staff - 403
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Manager - 200
        self.client.force_authenticate(user=self.manager)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("today", response.data)
        self.assertIn("by_status", response.data)
        self.assertIn("average_order_value", response.data)


# ============ Customer Activity Tests ============


class CustomerActivityViewTests(BaseViewTest):
    def test_public_log_activity(self):
        """Anyone can log activity."""
        url = reverse("menu:activity-list")
        data = {
            "session_id": "anon-123",
            "event_type": "view",
            "menu_item": str(self.item.id),
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_public_log_activity_with_metadata(self):
        """Activity can include metadata."""
        url = reverse("menu:activity-list")
        data = {
            "session_id": "anon-456",
            "event_type": "click",
            "menu_item": str(self.item.id),
            "metadata": {"source": "recommendation"},
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_public_cannot_list_activities(self):
        """Anonymous cannot list activities."""
        url = reverse("menu:activity-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_staff_cannot_list_activities(self):
        """Staff cannot list activities."""
        self.client.force_authenticate(user=self.staff)
        url = reverse("menu:activity-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_list_activities(self):
        """Managers can list activities."""
        CustomerActivity.objects.create(
            session_id="test-123", event_type="view", menu_item=self.item
        )

        self.client.force_authenticate(user=self.manager)
        url = reverse("menu:activity-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_activities_by_event_type(self):
        """Test filtering activities by event type."""
        CustomerActivity.objects.create(
            session_id="a", event_type="view", menu_item=self.item
        )
        CustomerActivity.objects.create(
            session_id="b", event_type="click", menu_item=self.item
        )

        self.client.force_authenticate(user=self.manager)
        url = reverse("menu:activity-list") + "?event_type=view"
        response = self.client.get(url)
        self.assertEqual(len(response.data), 1)

    def test_filter_activities_by_menu_item(self):
        """Test filtering activities by menu item."""
        CustomerActivity.objects.create(
            session_id="a", event_type="view", menu_item=self.item
        )

        self.client.force_authenticate(user=self.manager)
        url = reverse("menu:activity-list") + f"?menu_item={self.item.id}"
        response = self.client.get(url)
        self.assertEqual(len(response.data), 1)

    def test_filter_activities_by_session(self):
        """Test filtering activities by session."""
        CustomerActivity.objects.create(session_id="unique-session", event_type="view")
        CustomerActivity.objects.create(session_id="other-session", event_type="view")

        self.client.force_authenticate(user=self.manager)
        url = reverse("menu:activity-list") + "?session=unique-session"
        response = self.client.get(url)
        self.assertEqual(len(response.data), 1)

    def test_manager_view_stats(self):
        """Managers can view activity stats."""
        CustomerActivity.objects.create(
            session_id="test", event_type="view", menu_item=self.item
        )

        self.client.force_authenticate(user=self.manager)
        url = reverse("menu:activity-stats")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("by_event_type", response.data)
        self.assertIn("most_viewed_items", response.data)


# ============ Public Menu Tests ============


class PublicMenuViewTests(BaseViewTest):
    def test_get_full_menu(self):
        """Test the aggregated public menu endpoint."""
        url = reverse("menu:public-menu")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("menu", response.data)
        self.assertEqual(len(response.data["menu"]), 1)  # 1 active section
        self.assertEqual(len(response.data["menu"][0]["items"]), 1)  # 1 active item

    def test_public_menu_excludes_inactive(self):
        """Public menu excludes inactive sections and items."""
        url = reverse("menu:public-menu")
        response = self.client.get(url)

        # Should not include inactive section or inactive item
        section_names = [s["name"] for s in response.data["menu"]]
        self.assertNotIn("Seasonal", section_names)

        item_titles = [i["title"] for s in response.data["menu"] for i in s["items"]]
        self.assertNotIn("Old Item", item_titles)


# ============ ML Health Check Tests ============


class MLServiceHealthViewTests(BaseViewTest):
    @patch("menu.views.ml_service")
    def test_health_check_healthy(self, mock_ml_service):
        """Test ML health check when healthy."""
        mock_ml_service.health_check.return_value = {
            "status": "healthy",
            "model_loaded": True,
            "encoder_loaded": True,
        }

        url = reverse("menu:ml-health")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "healthy")

    @patch("menu.views.ml_service")
    def test_health_check_unhealthy(self, mock_ml_service):
        """Test ML health check when unhealthy."""
        mock_ml_service.health_check.return_value = {
            "status": "unhealthy",
            "model_loaded": False,
            "encoder_loaded": False,
        }

        url = reverse("menu:ml-health")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data["status"], "unhealthy")
