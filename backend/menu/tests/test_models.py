"""
Extended model tests for increased coverage.
Tests edge cases, relationships, and model methods.
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from ..models import MenuSection, MenuItem, Order, OrderItem, CustomerActivity

User = get_user_model()


# ============ Menu Section Tests ============


class MenuSectionModelTests(TestCase):
    def setUp(self):
        self.section = MenuSection.objects.create(
            name="Appetizers", description="Starters", display_order=1
        )

    def test_create_menu_section(self):
        """Test basic section creation."""
        self.assertEqual(self.section.name, "Appetizers")
        self.assertEqual(self.section.description, "Starters")
        self.assertTrue(self.section.is_active)
        self.assertIsNotNone(self.section.id)

    def test_str_representation(self):
        """Test section string representation."""
        self.assertEqual(str(self.section), "Appetizers")

    def test_section_defaults(self):
        """Test default values for sections."""
        section = MenuSection.objects.create(name="Drinks")
        self.assertTrue(section.is_active)
        self.assertEqual(section.display_order, 0)
        self.assertEqual(section.description, "")

    def test_section_ordering(self):
        """Test sections are ordered by display_order."""
        MenuSection.objects.create(name="Second", display_order=2)
        MenuSection.objects.create(name="Third", display_order=3)

        sections = MenuSection.objects.all()
        self.assertEqual(sections[0].name, "Appetizers")
        self.assertEqual(sections[1].name, "Second")

    def test_section_with_items_count(self):
        """Test section with items relationship."""
        MenuItem.objects.create(
            title="Salad",
            price=Decimal("8.00"),
            cost=Decimal("3.00"),
            section=self.section,
        )
        MenuItem.objects.create(
            title="Soup",
            price=Decimal("6.00"),
            cost=Decimal("2.00"),
            section=self.section,
        )
        self.assertEqual(self.section.items.count(), 2)


# ============ Menu Item Tests ============


class MenuItemModelTests(TestCase):
    def setUp(self):
        self.section = MenuSection.objects.create(name="Main Courses")
        self.item = MenuItem.objects.create(
            title="Cheeseburger",
            description="Juicy burger with cheese",
            price=Decimal("15.00"),
            cost=Decimal("5.00"),
            section=self.section,
            category=MenuItem.CategoryChoices.STAR,
        )

    def test_create_menu_item(self):
        """Test basic item creation."""
        self.assertEqual(self.item.title, "Cheeseburger")
        self.assertEqual(self.item.section, self.section)
        self.assertEqual(self.item.category, "star")
        self.assertTrue(self.item.is_active)

    def test_str_representation(self):
        """Test item string representation."""
        expected = f"Cheeseburger (${Decimal('15.00')})"
        self.assertEqual(str(self.item), expected)

    def test_margin_property(self):
        """Test margin calculation."""
        self.assertEqual(self.item.margin, Decimal("10.00"))

    def test_margin_percentage_property(self):
        """Test margin percentage calculation."""
        expected = (Decimal("10.00") / Decimal("15.00")) * 100
        self.assertEqual(self.item.margin_percentage, expected)

    def test_margin_percentage_zero_price(self):
        """Test margin percentage with zero price."""
        free_item = MenuItem.objects.create(
            title="Water",
            price=Decimal("0.00"),
            cost=Decimal("0.00"),
            section=self.section,
        )
        self.assertEqual(free_item.margin_percentage, 0)

    def test_negative_margin(self):
        """Test item with negative margin (cost > price)."""
        loss_item = MenuItem.objects.create(
            title="Loss Leader",
            price=Decimal("5.00"),
            cost=Decimal("10.00"),
            section=self.section,
        )
        self.assertEqual(loss_item.margin, Decimal("-5.00"))
        self.assertEqual(loss_item.margin_percentage, -100)

    def test_item_defaults(self):
        """Test default values for items."""
        item = MenuItem.objects.create(
            title="Basic Item",
            price=Decimal("10.00"),
            cost=Decimal("5.00"),
            section=self.section,
        )
        self.assertTrue(item.is_active)
        self.assertEqual(item.total_purchases, 0)
        self.assertEqual(item.total_revenue, Decimal("0.00"))
        self.assertIsNone(item.category)
        self.assertIsNone(item.ai_confidence)
        self.assertIsNone(item.last_analyzed)

    def test_item_categories(self):
        """Test all category choices."""
        categories = ["star", "plowhorse", "puzzle", "dog", "uncategorized"]
        for category in categories:
            item = MenuItem.objects.create(
                title=f"Item {category}",
                price=Decimal("10.00"),
                cost=Decimal("5.00"),
                section=self.section,
                category=category,
            )
            self.assertEqual(item.category, category)

    def test_item_cascade_delete_section(self):
        """Test items are deleted when section is deleted."""
        section = MenuSection.objects.create(name="Temp Section")
        MenuItem.objects.create(
            title="Temp Item",
            price=Decimal("10.00"),
            cost=Decimal("5.00"),
            section=section,
        )
        section_id = section.id
        section.delete()
        self.assertEqual(MenuItem.objects.filter(section_id=section_id).count(), 0)

    def test_ai_analysis_fields(self):
        """Test AI analysis fields."""
        self.item.category = "star"
        self.item.ai_confidence = 0.95
        self.item.last_analyzed = timezone.now()
        self.item.save()

        self.item.refresh_from_db()
        self.assertEqual(self.item.category, "star")
        self.assertEqual(self.item.ai_confidence, 0.95)
        self.assertIsNotNone(self.item.last_analyzed)

    def test_update_stats(self):
        """Test updating item statistics."""
        self.item.total_purchases = 100
        self.item.total_revenue = Decimal("1500.00")
        self.item.save()

        self.item.refresh_from_db()
        self.assertEqual(self.item.total_purchases, 100)
        self.assertEqual(self.item.total_revenue, Decimal("1500.00"))


# ============ Order Tests ============


class OrderModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            first_name="John",
            last_name="Doe",
            password="password",
            email="waiter@email.com",
            phone_number="+201234567890",
        )
        self.section = MenuSection.objects.create(name="Drinks")
        self.item_1 = MenuItem.objects.create(
            title="Coke",
            price=Decimal("3.00"),
            cost=Decimal("1.00"),
            section=self.section,
        )
        self.item_2 = MenuItem.objects.create(
            title="Fries",
            price=Decimal("5.00"),
            cost=Decimal("1.50"),
            section=self.section,
        )
        self.order = Order.objects.create(created_by=self.user, table_number="5")

    def test_create_order(self):
        """Test basic order creation."""
        self.assertEqual(self.order.status, Order.StatusChoices.PENDING)
        self.assertEqual(self.order.subtotal, 0)
        self.assertEqual(self.order.created_by, self.user)
        self.assertEqual(self.order.table_number, "5")

    def test_calculate_totals(self):
        """Test order totals calculation."""
        OrderItem.objects.create(
            order=self.order,
            menu_item=self.item_1,
            quantity=2,
            price_at_order=self.item_1.price,
        )
        OrderItem.objects.create(
            order=self.order,
            menu_item=self.item_2,
            quantity=1,
            price_at_order=self.item_2.price,
        )
        self.order.calculate_totals()

        expected_subtotal = Decimal("11.00")  # (2 * 3) + (1 * 5)
        self.assertEqual(self.order.subtotal, expected_subtotal)
        self.assertEqual(self.order.tax, Decimal("0.00"))
        self.assertEqual(self.order.total, expected_subtotal)

    def test_calculate_totals_empty_order(self):
        """Test totals for order with no items."""
        self.order.calculate_totals()
        self.assertEqual(self.order.subtotal, Decimal("0.00"))
        self.assertEqual(self.order.total, Decimal("0.00"))

    def test_str_representation(self):
        """Test order string representation."""
        self.assertIn(f"Order {self.order.id}", str(self.order))
        self.assertIn("pending", str(self.order))

    def test_order_without_user(self):
        """Test order can be created without user."""
        order = Order.objects.create(table_number="10")
        self.assertIsNone(order.created_by)

    def test_order_status_choices(self):
        """Test all status choices."""
        statuses = ["pending", "preparing", "ready", "delivered", "cancelled"]
        for status in statuses:
            order = Order.objects.create(status=status)
            self.assertEqual(order.status, status)

    def test_order_user_set_null_on_delete(self):
        """Test user is set to null when deleted."""
        user = User.objects.create_user(
            email="temp@test.com",
            password="pw",
            first_name="Temp",
            last_name="User",
            phone_number="+9999999999",
        )
        order = Order.objects.create(created_by=user, table_number="1")
        user.delete()
        order.refresh_from_db()
        self.assertIsNone(order.created_by)

    def test_order_timestamps(self):
        """Test order has created_at and updated_at."""
        self.assertIsNotNone(self.order.created_at)
        self.assertIsNotNone(self.order.updated_at)

        old_updated = self.order.updated_at
        self.order.notes = "Updated"
        self.order.save()
        self.order.refresh_from_db()
        self.assertGreater(self.order.updated_at, old_updated)


# ============ Order Item Tests ============


class OrderItemModelTests(TestCase):
    def setUp(self):
        self.section = MenuSection.objects.create(name="Main")
        self.item = MenuItem.objects.create(
            title="Steak",
            price=Decimal("20.00"),
            cost=Decimal("10.00"),
            section=self.section,
        )
        self.order = Order.objects.create()
        self.order_item = OrderItem.objects.create(
            order=self.order,
            menu_item=self.item,
            quantity=3,
            price_at_order=Decimal("20.00"),
        )

    def test_line_total_property(self):
        """Test line total calculation."""
        self.assertEqual(self.order_item.line_total, Decimal("60.00"))

    def test_line_total_single_quantity(self):
        """Test line total with quantity 1."""
        order_item = OrderItem.objects.create(
            order=self.order,
            menu_item=self.item,
            quantity=1,
            price_at_order=Decimal("25.00"),
        )
        self.assertEqual(order_item.line_total, Decimal("25.00"))

    def test_price_at_order_independence(self):
        """Test price at order doesn't change when item price changes."""
        original_price = self.order_item.price_at_order
        self.item.price = Decimal("25.00")
        self.item.save()

        self.order_item.refresh_from_db()
        self.assertEqual(self.order_item.price_at_order, original_price)

    def test_str_with_menu_item(self):
        """Test string representation with menu item."""
        expected = "3x Steak"
        self.assertEqual(str(self.order_item), expected)

    def test_str_without_menu_item(self):
        """Test string representation when item is deleted."""
        self.item.delete()
        self.order_item.refresh_from_db()
        self.assertIsNone(self.order_item.menu_item)
        self.assertEqual(str(self.order_item), "3x Deleted Item")

    def test_menu_item_set_null_on_delete(self):
        """Test menu_item is set to null when deleted."""
        self.item.delete()
        self.order_item.refresh_from_db()
        self.assertIsNone(self.order_item.menu_item)
        # Price at order is preserved
        self.assertEqual(self.order_item.price_at_order, Decimal("20.00"))

    def test_order_item_cascade_delete_order(self):
        """Test order items are deleted when order is deleted."""
        order_id = self.order.id
        self.order.delete()
        self.assertEqual(OrderItem.objects.filter(order_id=order_id).count(), 0)

    def test_order_item_notes(self):
        """Test order item notes."""
        order_item = OrderItem.objects.create(
            order=self.order,
            menu_item=self.item,
            quantity=1,
            price_at_order=Decimal("20.00"),
            notes="No onions, extra cheese",
        )
        self.assertEqual(order_item.notes, "No onions, extra cheese")


# ============ Customer Activity Tests ============


class CustomerActivityModelTests(TestCase):
    def setUp(self):
        self.section = MenuSection.objects.create(name="Desserts")
        self.item = MenuItem.objects.create(
            title="Cake",
            price=Decimal("5.00"),
            cost=Decimal("1.00"),
            section=self.section,
        )

    def test_create_activity(self):
        """Test basic activity creation."""
        activity = CustomerActivity.objects.create(
            session_id="abc-123",
            event_type=CustomerActivity.EventType.VIEW,
            menu_item=self.item,
            metadata={"source": "recommendation"},
        )
        self.assertEqual(activity.event_type, "view")
        self.assertEqual(activity.metadata["source"], "recommendation")
        self.assertIsNotNone(activity.timestamp)

    def test_str_representation_with_item(self):
        """Test string representation with menu item."""
        activity = CustomerActivity.objects.create(
            session_id="xyz-789",
            event_type=CustomerActivity.EventType.PURCHASE,
            menu_item=self.item,
        )
        self.assertIn("purchase", str(activity))
        self.assertIn("Cake", str(activity))

    def test_str_representation_without_item(self):
        """Test string representation without menu item."""
        activity = CustomerActivity.objects.create(
            session_id="abc-123",
            event_type=CustomerActivity.EventType.VIEW,
        )
        self.assertIn("view", str(activity))
        self.assertIn("No item", str(activity))

    def test_activity_without_menu_item(self):
        """Test activity can be created without menu item."""
        activity = CustomerActivity.objects.create(
            session_id="session-1",
            event_type="page_view",
        )
        self.assertIsNone(activity.menu_item)

    def test_all_event_types(self):
        """Test all event type choices."""
        event_types = ["view", "click", "hover", "add_to_cart", "purchase", "page_view"]
        for event_type in event_types:
            activity = CustomerActivity.objects.create(
                session_id=f"session-{event_type}",
                event_type=event_type,
            )
            self.assertEqual(activity.event_type, event_type)

    def test_activity_metadata_empty(self):
        """Test activity with empty metadata."""
        activity = CustomerActivity.objects.create(
            session_id="session-1",
            event_type="view",
        )
        self.assertEqual(activity.metadata, {})

    def test_activity_metadata_complex(self):
        """Test activity with complex metadata."""
        metadata = {
            "viewport": {"width": 1920, "height": 1080},
            "scroll_position": 500,
            "referrer": "google.com",
            "tags": ["mobile", "ios"],
        }
        activity = CustomerActivity.objects.create(
            session_id="session-1",
            event_type="view",
            menu_item=self.item,
            metadata=metadata,
        )
        self.assertEqual(activity.metadata, metadata)
        self.assertEqual(activity.metadata["viewport"]["width"], 1920)

    def test_menu_item_set_null_on_delete(self):
        """Test menu_item is set to null when deleted."""
        activity = CustomerActivity.objects.create(
            session_id="session-1", event_type="view", menu_item=self.item
        )
        self.item.delete()
        activity.refresh_from_db()
        self.assertIsNone(activity.menu_item)

    def test_activity_ordering(self):
        """Test activities are ordered by timestamp."""
        activity1 = CustomerActivity.objects.create(session_id="a", event_type="view")
        activity2 = CustomerActivity.objects.create(session_id="b", event_type="click")

        activities = CustomerActivity.objects.all()
        self.assertEqual(activities[0], activity2)  # Most recent first
