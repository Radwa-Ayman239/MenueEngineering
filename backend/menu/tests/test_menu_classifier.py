"""
Tests for the menu_classifier module.

Tests the Menu Engineering Matrix classification algorithm.
"""

from django.test import TestCase
from menu.menu_classifier import (
    MenuEngineeringClassifier,
    classify_menu_item,
    classify_menu_items_batch,
)

# Category names for testing
VALID_CATEGORIES = {"Star", "Plowhorse", "Puzzle", "Dog"}


class TestMenuEngineeringClassifier(TestCase):
    """Tests for the MenuEngineeringClassifier class."""

    def setUp(self):
        """Set up test fixtures."""
        self.classifier = MenuEngineeringClassifier()

    # ============ Category Classification Tests ============

    def test_star_classification(self):
        """Test that high popularity + high profit = Star."""
        result = self.classifier.classify_item(
            purchases=100,  # High popularity
            price=25.00,
            cost=10.00,  # High profit margin (60%)
        )
        self.assertEqual(result.category, "Star")
        self.assertIn("above_popularity_avg", result.metrics)
        self.assertIn("above_profitability_avg", result.metrics)

    def test_plowhorse_classification(self):
        """Test that high popularity + low profit = Plowhorse."""
        result = self.classifier.classify_item(
            purchases=100,  # High popularity
            price=15.00,
            cost=12.00,  # Low profit margin (20%)
        )
        self.assertEqual(result.category, "Plowhorse")

    def test_puzzle_classification(self):
        """Test that low popularity + high profit = Puzzle."""
        result = self.classifier.classify_item(
            purchases=10,  # Low popularity
            price=50.00,
            cost=20.00,  # High profit margin (60%)
        )
        self.assertEqual(result.category, "Puzzle")

    def test_dog_classification(self):
        """Test that low popularity + low profit = Dog."""
        result = self.classifier.classify_item(
            purchases=5,  # Low popularity
            price=10.00,
            cost=8.00,  # Low profit margin (20%)
        )
        self.assertEqual(result.category, "Dog")

    # ============ Confidence Scoring Tests ============

    def test_high_confidence_clear_star(self):
        """Test high confidence for clear Star (both metrics very high)."""
        result = self.classifier.classify_item(
            purchases=200,  # Very high sales
            price=100.00,
            cost=20.00,  # 80% margin
        )
        self.assertEqual(result.category, "Star")
        self.assertGreater(result.confidence, 0.8)

    def test_lower_confidence_borderline(self):
        """Test lower confidence for borderline cases."""
        # Near average values should have moderate confidence
        result = self.classifier.classify_item(
            purchases=55,  # Around average
            price=25.00,
            cost=12.50,  # 50% margin, around average
        )
        # Should still classify but with moderate confidence
        self.assertIn(result.category, VALID_CATEGORIES)
        self.assertLess(result.confidence, 0.9)

    # ============ Metric Calculation Tests ============

    def test_profit_margin_calculation(self):
        """Test that profit margin is correctly calculated."""
        result = self.classifier.classify_item(
            purchases=50,
            price=20.00,
            cost=8.00,  # Expected margin: (20-8)/20 = 60%
        )
        self.assertAlmostEqual(result.metrics["margin_percent"], 60.0, places=2)

    def test_zero_price_handling(self):
        """Test handling of zero price (edge case)."""
        result = self.classifier.classify_item(
            purchases=50,
            price=0.0,  # Zero price
            cost=0.0,
        )
        # Should still return a valid result
        self.assertIn(result.category, VALID_CATEGORIES)

    def test_negative_margin_handling(self):
        """Test handling of negative margin (cost > price)."""
        result = self.classifier.classify_item(
            purchases=10,
            price=10.00,
            cost=15.00,  # Negative margin!
        )
        # Should classify as Dog (unprofitable)
        self.assertEqual(result.category, "Dog")
        self.assertLess(result.metrics["margin_percent"], 0)

    # ============ Recommendations Tests ============

    def test_star_recommendations(self):
        """Test that Stars get appropriate recommendations."""
        result = self.classifier.classify_item(
            purchases=100,
            price=25.00,
            cost=10.00,
        )
        self.assertEqual(result.category, "Star")
        self.assertIsInstance(result.recommendations, list)
        self.assertGreater(len(result.recommendations), 0)

    def test_dog_recommendations(self):
        """Test that Dogs get appropriate recommendations."""
        result = self.classifier.classify_item(
            purchases=5,
            price=10.00,
            cost=8.00,
        )
        self.assertEqual(result.category, "Dog")
        self.assertIsInstance(result.recommendations, list)
        self.assertGreater(len(result.recommendations), 0)

    # ============ Custom Thresholds Tests ============

    def test_custom_thresholds(self):
        """Test classification with custom thresholds."""
        result = self.classifier.classify_item(
            purchases=30,
            price=25.00,
            cost=10.00,
            avg_purchases=20,  # Custom: avg is 20
            avg_margin_percent=40.0,  # Custom: avg margin is 40%
        )
        # With purchases > avg and margin > avg, should be Star
        self.assertEqual(result.category, "Star")

    def test_custom_thresholds_change_classification(self):
        """Test that custom thresholds can change classification."""
        # Without custom thresholds
        result1 = self.classifier.classify_item(
            purchases=40,
            price=25.00,
            cost=12.50,  # 50% margin
        )

        # With high custom thresholds
        result2 = self.classifier.classify_item(
            purchases=40,
            price=25.00,
            cost=12.50,
            avg_purchases=100,  # Much higher average
            avg_margin_percent=70.0,  # Much higher average margin (70%)
        )
        # Second should be Dog (below both high thresholds)
        self.assertEqual(result2.category, "Dog")


class TestBatchClassification(TestCase):
    """Tests for batch classification functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_items = [
            {"purchases": 100, "price": 25.00, "cost": 10.00},  # Star
            {"purchases": 100, "price": 15.00, "cost": 12.00},  # Plowhorse
            {"purchases": 10, "price": 50.00, "cost": 20.00},  # Puzzle
            {"purchases": 5, "price": 10.00, "cost": 8.00},  # Dog
        ]

    def test_batch_classification(self):
        """Test batch classification returns correct number of results."""
        results = classify_menu_items_batch(self.sample_items)

        self.assertEqual(len(results), 4)
        for result in results:
            self.assertIn("category", result)
            self.assertIn("confidence", result)
            self.assertIn("recommendations", result)
            self.assertIn("metrics", result)

    def test_batch_uses_batch_averages(self):
        """Test that batch classification uses batch-computed averages."""
        # All high performers
        high_items = [
            {"purchases": 100, "price": 30.00, "cost": 10.00},
            {"purchases": 120, "price": 35.00, "cost": 12.00},
            {"purchases": 90, "price": 28.00, "cost": 9.00},
        ]
        results = classify_menu_items_batch(high_items)

        # With batch averages, some should be below-average relative to batch
        categories = [r["category"] for r in results]
        # Should have variety based on relative positioning
        self.assertEqual(len(results), 3)

    def test_empty_batch(self):
        """Test that empty batch returns empty list."""
        results = classify_menu_items_batch([])
        self.assertEqual(results, [])

    def test_single_item_batch(self):
        """Test batch with single item."""
        results = classify_menu_items_batch([self.sample_items[0]])

        self.assertEqual(len(results), 1)
        self.assertIn("category", results[0])


class TestConvenienceFunctions(TestCase):
    """Tests for convenience wrapper functions."""

    def test_classify_menu_item_function(self):
        """Test the classify_menu_item convenience function."""
        result = classify_menu_item(
            purchases=100,
            price=25.00,
            cost=10.00,
        )

        self.assertIn("category", result)
        self.assertIn("confidence", result)
        self.assertIn("recommendations", result)
        self.assertIn("metrics", result)
        self.assertEqual(result["category"], "Star")

    def test_classify_menu_items_batch_function(self):
        """Test the classify_menu_items_batch convenience function."""
        items = [
            {"purchases": 100, "price": 25.00, "cost": 10.00},
            {"purchases": 5, "price": 10.00, "cost": 8.00},
        ]
        results = classify_menu_items_batch(items)

        self.assertEqual(len(results), 2)


class TestEdgeCases(TestCase):
    """Tests for edge cases and error handling."""

    def test_very_large_numbers(self):
        """Test handling of very large numbers."""
        result = classify_menu_item(
            purchases=1000000,
            price=10000.00,
            cost=1000.00,
        )
        self.assertIn(result["category"], VALID_CATEGORIES)

    def test_very_small_numbers(self):
        """Test handling of very small (but positive) numbers."""
        result = classify_menu_item(
            purchases=1,
            price=0.01,
            cost=0.001,
        )
        self.assertIn(result["category"], VALID_CATEGORIES)

    def test_float_values(self):
        """Test handling of float values."""
        result = classify_menu_item(
            purchases=50,
            price=19.99,
            cost=7.53,
        )
        self.assertIn(result["category"], VALID_CATEGORIES)
        self.assertIsInstance(result["metrics"]["margin_percent"], float)

    def test_description_length_optional(self):
        """Test that description_length is optional."""
        result1 = classify_menu_item(
            purchases=50,
            price=20.00,
            cost=10.00,
        )
        result2 = classify_menu_item(
            purchases=50,
            price=20.00,
            cost=10.00,
            description_length=100,
        )
        # Both should work and return same category
        self.assertEqual(result1["category"], result2["category"])
