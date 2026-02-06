"""
Extended serializer tests for increased coverage.
Tests validation, edge cases, and all serializer types.
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory

from ..models import MenuSection, MenuItem, Order, OrderItem, CustomerActivity
from ..serializers import (
    MenuSectionSerializer,
    MenuSectionCreateSerializer,
    MenuItemListSerializer,
    MenuItemDetailSerializer,
    MenuItemCreateSerializer,
    MenuItemAnalysisSerializer,
    OrderListSerializer,
    OrderDetailSerializer,
    OrderCreateSerializer,
    OrderStatusUpdateSerializer,
    OrderItemSerializer,
    OrderItemCreateSerializer,
    CustomerActivitySerializer,
    CustomerActivityCreateSerializer,
)

User = get_user_model()


# ============ Menu Section Serializer Tests ============


class MenuSectionSerializerTests(TestCase):
    def setUp(self):
        self.section = MenuSection.objects.create(
            name="Starters", description="Appetizers"
        )
        MenuItem.objects.create(
            title="Active Item", price=10, cost=5, section=self.section, is_active=True
        )
        MenuItem.objects.create(
            title="Inactive Item",
            price=10,
            cost=5,
            section=self.section,
            is_active=False,
        )

    def test_contains_expected_fields(self):
        """Test serializer contains expected fields."""
        serializer = MenuSectionSerializer(instance=self.section)
        data = serializer.data

        self.assertIn("id", data)
        self.assertIn("name", data)
        self.assertIn("description", data)
        self.assertIn("is_active", data)
        self.assertIn("display_order", data)
        self.assertIn("items_count", data)

    def test_items_count_only_active(self):
        """Test items_count only counts active items."""
        serializer = MenuSectionSerializer(instance=self.section)
        self.assertEqual(serializer.data["items_count"], 1)

    def test_create_serializer_valid(self):
        """Test creating section with valid data."""
        data = {"name": "Mains", "display_order": 2}
        serializer = MenuSectionCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        section = serializer.save()
        self.assertEqual(section.name, "Mains")

    def test_create_serializer_minimal(self):
        """Test creating section with minimal data."""
        data = {"name": "Drinks"}
        serializer = MenuSectionCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_create_serializer_missing_name(self):
        """Test name is required."""
        data = {"display_order": 1}
        serializer = MenuSectionCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_update_section(self):
        """Test updating section."""
        data = {"name": "Updated Starters", "is_active": False}
        serializer = MenuSectionCreateSerializer(
            instance=self.section, data=data, partial=True
        )
        self.assertTrue(serializer.is_valid())
        section = serializer.save()
        self.assertEqual(section.name, "Updated Starters")
        self.assertFalse(section.is_active)


# ============ Menu Item Serializer Tests ============


class MenuItemSerializerTests(TestCase):
    def setUp(self):
        self.section = MenuSection.objects.create(name="Mains")
        self.item = MenuItem.objects.create(
            title="Steak",
            description="Premium beef steak",
            price=Decimal("100.00"),
            cost=Decimal("40.00"),
            section=self.section,
            category="star",
            total_purchases=50,
            total_revenue=Decimal("5000.00"),
        )

    def test_list_serializer_fields(self):
        """Test list serializer has basic fields."""
        serializer = MenuItemListSerializer(instance=self.item)
        data = serializer.data

        self.assertIn("id", data)
        self.assertIn("title", data)
        self.assertIn("price", data)
        self.assertIn("section", data)
        self.assertIn("category", data)
        self.assertIn("is_active", data)

    def test_detail_serializer_fields(self):
        """Test detail serializer has calculated fields."""
        serializer = MenuItemDetailSerializer(instance=self.item)
        data = serializer.data

        self.assertIn("margin", data)
        self.assertIn("margin_percentage", data)
        self.assertIn("section_name", data)
        self.assertIn("total_purchases", data)
        self.assertIn("total_revenue", data)
        self.assertIn("ai_confidence", data)

    def test_detail_serializer_calculations(self):
        """Test calculations are correct."""
        serializer = MenuItemDetailSerializer(instance=self.item)
        data = serializer.data

        self.assertEqual(Decimal(data["margin"]), Decimal("60.00"))
        self.assertEqual(data["margin_percentage"], 60.0)
        self.assertEqual(data["section_name"], "Mains")

    def test_create_serializer_valid(self):
        """Test creating item with valid data."""
        data = {
            "title": "New Item",
            "price": "20.00",
            "cost": "10.00",
            "section": self.section.id,
        }
        serializer = MenuItemCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        item = serializer.save()
        self.assertEqual(item.title, "New Item")

    def test_create_serializer_with_all_fields(self):
        """Test creating item with all fields."""
        data = {
            "title": "Full Item",
            "description": "A complete item",
            "price": "25.00",
            "cost": "12.00",
            "section": self.section.id,
            "display_order": 5,
            "is_active": True,
        }
        serializer = MenuItemCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        item = serializer.save()
        self.assertEqual(item.display_order, 5)

    def test_validate_negative_price(self):
        """Test price must be positive."""
        data = {
            "title": "Bad Price",
            "price": "-5.00",
            "cost": "2.00",
            "section": self.section.id,
        }
        serializer = MenuItemCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("price", serializer.errors)

    def test_validate_zero_price(self):
        """Test price cannot be zero."""
        data = {
            "title": "Zero Price",
            "price": "0.00",
            "cost": "0.00",
            "section": self.section.id,
        }
        serializer = MenuItemCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("price", serializer.errors)

    def test_validate_cost_greater_than_price(self):
        """Test cost cannot be greater than price."""
        data = {
            "title": "Bad Margin",
            "price": "10.00",
            "cost": "15.00",
            "section": self.section.id,
        }
        serializer = MenuItemCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("cost", serializer.errors)

    def test_validate_negative_cost(self):
        """Test cost cannot be negative."""
        data = {
            "title": "Negative Cost",
            "price": "10.00",
            "cost": "-5.00",
            "section": self.section.id,
        }
        serializer = MenuItemCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("cost", serializer.errors)

    def test_update_item(self):
        """Test updating item."""
        data = {"price": "120.00"}
        serializer = MenuItemCreateSerializer(
            instance=self.item, data=data, partial=True
        )
        self.assertTrue(serializer.is_valid())
        item = serializer.save()
        self.assertEqual(item.price, Decimal("120.00"))

    def test_analysis_serializer(self):
        """Test analysis serializer is for response format, not model serialization."""
        # MenuItemAnalysisSerializer is for the ML response format
        # It has fields: category, confidence, recommendations from ML service
        # We test it with sample response data instead of model instance
        response_data = {
            "category": "star",
            "confidence": 0.95,
            "recommendations": ["Promote heavily", "Keep pricing"],
        }
        serializer = MenuItemAnalysisSerializer(data=response_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)


# ============ Order Serializer Tests ============


class OrderSerializerTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            email="staff@test.com",
            password="password",
            first_name="Staff",
            last_name="User",
            phone_number="+1234567890",
        )
        self.section = MenuSection.objects.create(name="Drinks")
        self.item = MenuItem.objects.create(
            title="Cola",
            price=Decimal("3.00"),
            cost=Decimal("1.00"),
            section=self.section,
        )
        self.order = Order.objects.create(
            created_by=self.user, table_number="5", notes="Test order"
        )
        self.order_item = OrderItem.objects.create(
            order=self.order,
            menu_item=self.item,
            quantity=2,
            price_at_order=self.item.price,
        )

    def test_list_serializer_fields(self):
        """Test list serializer fields."""
        serializer = OrderListSerializer(instance=self.order)
        data = serializer.data

        self.assertIn("id", data)
        self.assertIn("status", data)
        self.assertIn("table_number", data)
        self.assertIn("total", data)
        self.assertIn("created_at", data)
        self.assertIn("created_by_name", data)
        self.assertIn("items_count", data)

    def test_list_serializer_computed_fields(self):
        """Test computed fields in list serializer."""
        serializer = OrderListSerializer(instance=self.order)
        data = serializer.data

        self.assertEqual(data["items_count"], 1)
        self.assertEqual(data["created_by_name"], "Staff User")

    def test_detail_serializer_nested_items(self):
        """Test detail serializer includes nested items."""
        serializer = OrderDetailSerializer(instance=self.order)
        data = serializer.data

        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(data["items"][0]["menu_item_title"], "Cola")
        self.assertEqual(data["items"][0]["quantity"], 2)

    def test_create_order_with_items(self):
        """Test creating order with nested items."""
        data = {
            "table_number": "12",
            "notes": "No ice",
            "items": [
                {"menu_item": self.item.id, "quantity": 2, "notes": "Extra cold"}
            ],
        }
        request = self.factory.post("/")
        request.user = self.user

        serializer = OrderCreateSerializer(data=data, context={"request": request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        order = serializer.save()

        self.assertEqual(order.created_by, self.user)
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.subtotal, Decimal("6.00"))

    def test_create_order_multiple_items(self):
        """Test creating order with multiple items."""
        item2 = MenuItem.objects.create(
            title="Fries",
            price=Decimal("5.00"),
            cost=Decimal("2.00"),
            section=self.section,
        )

        data = {
            "table_number": "10",
            "items": [
                {"menu_item": self.item.id, "quantity": 2},
                {"menu_item": item2.id, "quantity": 3},
            ],
        }
        request = self.factory.post("/")
        request.user = self.user

        serializer = OrderCreateSerializer(data=data, context={"request": request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        order = serializer.save()

        self.assertEqual(order.items.count(), 2)
        # 2 * 3.00 + 3 * 5.00 = 6 + 15 = 21
        self.assertEqual(order.subtotal, Decimal("21.00"))

    def test_create_order_updates_item_stats(self):
        """Test creating order updates menu item statistics."""
        original_purchases = self.item.total_purchases
        original_revenue = self.item.total_revenue

        data = {
            "items": [{"menu_item": self.item.id, "quantity": 5}],
        }
        request = self.factory.post("/")
        request.user = self.user

        serializer = OrderCreateSerializer(data=data, context={"request": request})
        serializer.is_valid()
        serializer.save()

        self.item.refresh_from_db()
        self.assertEqual(self.item.total_purchases, original_purchases + 5)
        self.assertEqual(self.item.total_revenue, original_revenue + Decimal("15.00"))

    def test_validate_order_quantity_zero(self):
        """Test quantity must be at least 1."""
        data = {"items": [{"menu_item": self.item.id, "quantity": 0}]}
        request = self.factory.post("/")
        request.user = self.user

        serializer = OrderCreateSerializer(data=data, context={"request": request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("quantity", serializer.errors["items"][0])

    def test_validate_order_quantity_negative(self):
        """Test quantity cannot be negative."""
        data = {"items": [{"menu_item": self.item.id, "quantity": -1}]}
        request = self.factory.post("/")
        request.user = self.user

        serializer = OrderCreateSerializer(data=data, context={"request": request})
        self.assertFalse(serializer.is_valid())

    def test_status_update_serializer(self):
        """Test status update serializer."""
        data = {"status": "preparing"}
        serializer = OrderStatusUpdateSerializer(
            instance=self.order, data=data, partial=True
        )
        self.assertTrue(serializer.is_valid())
        order = serializer.save()
        self.assertEqual(order.status, "preparing")

    def test_status_update_invalid_status(self):
        """Test invalid status value."""
        data = {"status": "invalid_status"}
        serializer = OrderStatusUpdateSerializer(
            instance=self.order, data=data, partial=True
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("status", serializer.errors)


# ============ Order Item Serializer Tests ============


class OrderItemSerializerTests(TestCase):
    def setUp(self):
        self.section = MenuSection.objects.create(name="Food")
        self.item = MenuItem.objects.create(
            title="Burger",
            price=Decimal("10.00"),
            cost=Decimal("5.00"),
            section=self.section,
        )
        self.order = Order.objects.create()
        self.order_item = OrderItem.objects.create(
            order=self.order,
            menu_item=self.item,
            quantity=2,
            price_at_order=Decimal("10.00"),
            notes="No pickles",
        )

    def test_order_item_serializer_fields(self):
        """Test order item serializer fields."""
        serializer = OrderItemSerializer(instance=self.order_item)
        data = serializer.data

        self.assertIn("id", data)
        self.assertIn("menu_item", data)
        self.assertIn("menu_item_title", data)
        self.assertIn("quantity", data)
        self.assertIn("price_at_order", data)
        self.assertIn("notes", data)
        self.assertIn("line_total", data)

    def test_order_item_computed_fields(self):
        """Test computed fields."""
        serializer = OrderItemSerializer(instance=self.order_item)
        data = serializer.data

        self.assertEqual(data["menu_item_title"], "Burger")
        self.assertEqual(Decimal(data["line_total"]), Decimal("20.00"))

    def test_order_item_deleted_menu_item(self):
        """Test serializer when menu item is deleted."""
        self.item.delete()
        self.order_item.refresh_from_db()

        serializer = OrderItemSerializer(instance=self.order_item)
        data = serializer.data

        self.assertIsNone(data["menu_item"])

    def test_create_order_item_serializer(self):
        """Test order item create serializer."""
        data = {"menu_item": self.item.id, "quantity": 3, "notes": "Extra sauce"}
        serializer = OrderItemCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)


# ============ Customer Activity Serializer Tests ============


class CustomerActivitySerializerTests(TestCase):
    def setUp(self):
        self.section = MenuSection.objects.create(name="Desserts")
        self.item = MenuItem.objects.create(
            title="Cake",
            price=Decimal("5.00"),
            cost=Decimal("1.00"),
            section=self.section,
        )
        self.activity = CustomerActivity.objects.create(
            session_id="session-123",
            event_type="view",
            menu_item=self.item,
            metadata={"source": "home"},
        )

    def test_activity_serializer_fields(self):
        """Test activity serializer fields."""
        serializer = CustomerActivitySerializer(instance=self.activity)
        data = serializer.data

        self.assertIn("id", data)
        self.assertIn("session_id", data)
        self.assertIn("event_type", data)
        self.assertIn("menu_item", data)
        self.assertIn("timestamp", data)
        self.assertIn("metadata", data)

    def test_create_activity_serializer_valid(self):
        """Test creating activity with valid data."""
        data = {
            "session_id": "new-session",
            "event_type": "click",
            "menu_item": str(self.item.id),
        }
        serializer = CustomerActivityCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        activity = serializer.save()
        self.assertEqual(activity.event_type, "click")

    def test_create_activity_without_menu_item(self):
        """Test creating activity without menu item."""
        data = {
            "session_id": "new-session",
            "event_type": "view",
        }
        serializer = CustomerActivityCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        activity = serializer.save()
        self.assertIsNone(activity.menu_item)

    def test_create_activity_with_metadata(self):
        """Test creating activity with metadata."""
        data = {
            "session_id": "new-session",
            "event_type": "view",
            "menu_item": str(self.item.id),
            "metadata": {"referrer": "google.com", "time_on_page": 30},
        }
        serializer = CustomerActivityCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        activity = serializer.save()
        self.assertEqual(activity.metadata["referrer"], "google.com")

    def test_create_activity_invalid_event_type(self):
        """Test invalid event type."""
        data = {
            "session_id": "new-session",
            "event_type": "invalid_type",
        }
        serializer = CustomerActivityCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("event_type", serializer.errors)

    def test_create_activity_missing_session_id(self):
        """Test session_id is required."""
        data = {
            "event_type": "view",
        }
        serializer = CustomerActivityCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("session_id", serializer.errors)
