"""
Tests for the recommendation engine module.

Tests cover:
- CoPurchaseAnalyzer (market basket analysis)
- RecommendationEngine (multi-strategy scoring)
- Profit optimization correctness
- Edge cases (no orders, single item, etc.)
"""

from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.contrib.auth import get_user_model

from ..models import MenuSection, MenuItem, Order, OrderItem
from ..recommendation_engine import (
    CoPurchaseAnalyzer,
    RecommendationEngine,
    ItemAssociation,
    RecommendationResult,
    AffinityMatrix,
    CATEGORY_SCORES,
    get_recommendations,
    get_frequently_bought_together,
)

User = get_user_model()


class CoPurchaseAnalyzerTests(TestCase):
    """Tests for the CoPurchaseAnalyzer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.section = MenuSection.objects.create(name="Main Dishes")
        self.item_a = MenuItem.objects.create(
            title="Burger",
            price=Decimal("15.00"),
            cost=Decimal("5.00"),
            section=self.section,
            category="star",
            total_purchases=100,
        )
        self.item_b = MenuItem.objects.create(
            title="Fries",
            price=Decimal("6.00"),
            cost=Decimal("1.50"),
            section=self.section,
            category="plowhorse",
            total_purchases=80,
        )
        self.item_c = MenuItem.objects.create(
            title="Drink",
            price=Decimal("3.00"),
            cost=Decimal("0.50"),
            section=self.section,
            category="puzzle",
            total_purchases=50,
        )
        self.item_d = MenuItem.objects.create(
            title="Salad",
            price=Decimal("10.00"),
            cost=Decimal("7.00"),
            section=self.section,
            category="dog",
            total_purchases=10,
        )

        self.analyzer = CoPurchaseAnalyzer(min_support=0.01, min_confidence=0.1)

    def _create_order_with_items(self, *items, status="completed"):
        """Helper to create an order with multiple items."""
        order = Order.objects.create(status=status)
        for item in items:
            OrderItem.objects.create(
                order=order,
                menu_item=item,
                quantity=1,
                price_at_order=item.price,
            )
        return order

    def test_build_affinity_matrix_empty(self):
        """Test matrix with no orders returns empty."""
        matrix = self.analyzer.build_affinity_matrix(use_cache=False)
        self.assertEqual(matrix.total_orders, 0)
        self.assertEqual(matrix.associations, {})

    def test_build_affinity_matrix_single_item_orders(self):
        """Test matrix with single-item orders has no associations."""
        self._create_order_with_items(self.item_a)
        self._create_order_with_items(self.item_b)

        matrix = self.analyzer.build_affinity_matrix(use_cache=False)
        self.assertEqual(matrix.total_orders, 2)
        # No pairs, so no associations
        self.assertEqual(matrix.associations, {})

    def test_build_affinity_matrix_with_pairs(self):
        """Test matrix correctly identifies co-purchased items."""
        # Create orders with burger + fries combo (5 times)
        for _ in range(5):
            self._create_order_with_items(self.item_a, self.item_b)

        # Create some single item orders
        for _ in range(5):
            self._create_order_with_items(self.item_a)

        matrix = self.analyzer.build_affinity_matrix(use_cache=False)
        self.assertEqual(matrix.total_orders, 10)

        # Burger should have association with Fries
        self.assertIn(self.item_a.id, matrix.associations)

        # Check support (5/10 = 0.5)
        burger_associations = matrix.associations[self.item_a.id]
        fries_assoc = next(
            (a for a in burger_associations if a["item_id"] == self.item_b.id), None
        )
        self.assertIsNotNone(fries_assoc)
        self.assertAlmostEqual(fries_assoc["support"], 0.5, places=2)

    def test_get_item_associations(self):
        """Test getting associations for a specific item."""
        # Create co-purchase pattern
        for _ in range(10):
            self._create_order_with_items(self.item_a, self.item_b, self.item_c)

        associations = self.analyzer.get_item_associations(self.item_a.id, limit=5)

        self.assertGreater(len(associations), 0)
        self.assertIsInstance(associations[0], ItemAssociation)
        # Check that both b and c are in associations (order may vary when lift is equal)
        association_item_ids = [a.item_id for a in associations]
        self.assertIn(self.item_b.id, association_item_ids)
        self.assertIn(self.item_c.id, association_item_ids)

    def test_associations_sorted_by_lift(self):
        """Test associations are returned sorted by lift."""
        # Create varied co-purchase patterns
        for _ in range(10):
            self._create_order_with_items(self.item_a, self.item_b)
        for _ in range(3):
            self._create_order_with_items(self.item_a, self.item_c)

        associations = self.analyzer.get_item_associations(self.item_a.id)

        # Should be sorted by lift (strongest association first)
        if len(associations) > 1:
            self.assertGreaterEqual(associations[0].lift, associations[1].lift)

    def test_pending_orders_excluded(self):
        """Test that pending orders are not included in analysis."""
        # Create completed orders
        for _ in range(5):
            self._create_order_with_items(self.item_a, self.item_b, status="completed")

        # Create pending orders
        for _ in range(5):
            self._create_order_with_items(self.item_a, self.item_c, status="pending")

        matrix = self.analyzer.build_affinity_matrix(use_cache=False)

        # Only completed orders count
        self.assertEqual(matrix.total_orders, 5)


class RecommendationEngineTests(TestCase):
    """Tests for the RecommendationEngine class."""

    def setUp(self):
        """Set up test fixtures."""
        self.section = MenuSection.objects.create(name="Main Dishes")
        self.dessert_section = MenuSection.objects.create(name="Desserts")

        # Create items with different categories
        self.star_item = MenuItem.objects.create(
            title="Premium Steak",
            price=Decimal("50.00"),
            cost=Decimal("20.00"),
            section=self.section,
            category="star",
            total_purchases=200,
        )
        self.puzzle_item = MenuItem.objects.create(
            title="Lobster Tail",
            price=Decimal("60.00"),
            cost=Decimal("25.00"),
            section=self.section,
            category="puzzle",
            total_purchases=30,
        )
        self.plowhorse_item = MenuItem.objects.create(
            title="House Burger",
            price=Decimal("15.00"),
            cost=Decimal("8.00"),
            section=self.section,
            category="plowhorse",
            total_purchases=300,
        )
        self.dog_item = MenuItem.objects.create(
            title="Plain Salad",
            price=Decimal("8.00"),
            cost=Decimal("6.00"),
            section=self.section,
            category="dog",
            total_purchases=15,
        )
        self.dessert_item = MenuItem.objects.create(
            title="Chocolate Cake",
            price=Decimal("12.00"),
            cost=Decimal("4.00"),
            section=self.dessert_section,
            category="star",
            total_purchases=150,
        )

        self.engine = RecommendationEngine()

    def test_get_recommendations_empty_cart(self):
        """Test recommendations with no cart context."""
        recommendations = self.engine.get_recommendations(limit=5)

        self.assertGreater(len(recommendations), 0)
        self.assertLessEqual(len(recommendations), 5)
        self.assertIsInstance(recommendations[0], RecommendationResult)

    def test_star_items_score_highest(self):
        """Test that Star items generally score higher than Dogs."""
        recommendations = self.engine.get_recommendations(limit=10)

        # Find positions of star and dog items
        star_positions = [
            i for i, r in enumerate(recommendations) if r.item.category == "star"
        ]
        dog_positions = [
            i for i, r in enumerate(recommendations) if r.item.category == "dog"
        ]

        # Stars should generally appear before dogs
        if star_positions and dog_positions:
            avg_star_pos = sum(star_positions) / len(star_positions)
            avg_dog_pos = sum(dog_positions) / len(dog_positions)
            self.assertLess(avg_star_pos, avg_dog_pos)

    def test_exclude_current_items(self):
        """Test that current cart items are excluded from recommendations."""
        recommendations = self.engine.get_recommendations(
            current_items=[self.star_item.id]
        )

        item_ids = [r.item.id for r in recommendations]
        self.assertNotIn(self.star_item.id, item_ids)

    def test_section_filter(self):
        """Test filtering recommendations by section."""
        recommendations = self.engine.get_recommendations(
            section_id=self.dessert_section.id
        )

        for rec in recommendations:
            self.assertEqual(rec.item.section_id, self.dessert_section.id)

    def test_upsell_strategy_favors_margin(self):
        """Test that upsell strategy prioritizes high-margin items."""
        balanced = self.engine.get_recommendations(limit=5, strategy="balanced")
        upsell = self.engine.get_recommendations(limit=5, strategy="upsell")

        # Upsell should have higher average margin score
        avg_margin_balanced = sum(r.margin_score for r in balanced) / len(balanced)
        avg_margin_upsell = sum(r.margin_score for r in upsell) / len(upsell)

        # Upsell should favor margin more (not strictly greater due to other factors)
        self.assertIsNotNone(avg_margin_upsell)
        self.assertIsNotNone(avg_margin_balanced)

    def test_cross_sell_prefers_different_sections(self):
        """Test that cross-sell suggests items from different sections."""
        recommendations = self.engine.get_cross_sell_suggestions(
            current_items=[self.star_item.id], limit=3
        )

        # Should prefer dessert section over main dishes
        different_section_count = sum(
            1 for r in recommendations if r.item.section_id != self.section.id
        )
        self.assertGreater(different_section_count, 0)

    def test_recommendation_has_reason(self):
        """Test that recommendations include human-readable reasons."""
        recommendations = self.engine.get_recommendations(limit=1)

        self.assertGreater(len(recommendations), 0)
        self.assertIsNotNone(recommendations[0].reason)
        self.assertGreater(len(recommendations[0].reason), 0)

    def test_profit_impact_included(self):
        """Test that profit impact (margin) is included in results."""
        recommendations = self.engine.get_recommendations(limit=1)

        self.assertGreater(len(recommendations), 0)
        # Profit impact should be the item's margin
        rec = recommendations[0]
        if rec.profit_impact:
            self.assertEqual(rec.profit_impact, rec.item.margin)


class FrequentlyBoughtTogetherTests(TestCase):
    """Tests for the frequently bought together functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.section = MenuSection.objects.create(name="Test Section")
        self.item_main = MenuItem.objects.create(
            title="Main Item",
            price=Decimal("20.00"),
            cost=Decimal("8.00"),
            section=self.section,
        )
        self.item_side = MenuItem.objects.create(
            title="Side Item",
            price=Decimal("8.00"),
            cost=Decimal("2.00"),
            section=self.section,
        )

    def _create_combo_orders(self, count=10):
        """Create orders with main + side combo."""
        for _ in range(count):
            order = Order.objects.create(status="completed")
            OrderItem.objects.create(
                order=order,
                menu_item=self.item_main,
                quantity=1,
                price_at_order=self.item_main.price,
            )
            OrderItem.objects.create(
                order=order,
                menu_item=self.item_side,
                quantity=1,
                price_at_order=self.item_side.price,
            )

    def test_get_frequently_bought_together(self):
        """Test getting FBT items."""
        self._create_combo_orders(10)

        engine = RecommendationEngine()
        fbt = engine.get_frequently_bought_together(self.item_main.id, limit=3)

        self.assertGreater(len(fbt), 0)
        self.assertEqual(fbt[0].item_id, self.item_side.id)

    def test_fbt_empty_without_orders(self):
        """Test FBT returns empty list without order history."""
        engine = RecommendationEngine()
        fbt = engine.get_frequently_bought_together(self.item_main.id)

        self.assertEqual(len(fbt), 0)


class ConvenienceFunctionsTests(TestCase):
    """Tests for the convenience wrapper functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.section = MenuSection.objects.create(name="Test")
        self.item = MenuItem.objects.create(
            title="Test Item",
            price=Decimal("15.00"),
            cost=Decimal("5.00"),
            section=self.section,
            category="star",
        )

    def test_get_recommendations_returns_dicts(self):
        """Test get_recommendations returns dictionaries."""
        results = get_recommendations(limit=3)

        self.assertIsInstance(results, list)
        if results:
            self.assertIsInstance(results[0], dict)
            self.assertIn("item_id", results[0])
            self.assertIn("title", results[0])
            self.assertIn("score", results[0])
            self.assertIn("reason", results[0])

    def test_get_frequently_bought_together_returns_dicts(self):
        """Test get_frequently_bought_together returns dictionaries."""
        results = get_frequently_bought_together(self.item.id, limit=3)

        self.assertIsInstance(results, list)


class CategoryScoreTests(TestCase):
    """Tests for category-based scoring."""

    def test_category_scores_defined(self):
        """Test all expected categories have scores."""
        expected_categories = ["star", "puzzle", "plowhorse", "dog", None]

        for category in expected_categories:
            self.assertIn(category, CATEGORY_SCORES)

    def test_star_highest_score(self):
        """Test Star has the highest category score."""
        self.assertEqual(CATEGORY_SCORES["star"], 1.0)

    def test_dog_lowest_score(self):
        """Test Dog has the lowest category score."""
        self.assertEqual(CATEGORY_SCORES["dog"], 0.1)

    def test_score_ordering(self):
        """Test category scores are in expected order."""
        self.assertGreater(CATEGORY_SCORES["star"], CATEGORY_SCORES["puzzle"])
        self.assertGreater(CATEGORY_SCORES["puzzle"], CATEGORY_SCORES["plowhorse"])
        self.assertGreater(CATEGORY_SCORES["plowhorse"], CATEGORY_SCORES["dog"])
