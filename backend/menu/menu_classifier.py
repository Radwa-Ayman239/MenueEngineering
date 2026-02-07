"""
File: menu_classifier.py
Author: Malak
Description: Menu Engineering Matrix Classification Service.
Implements the standard algorithm to classify menu items into Stars, Plowhorses,
Puzzles, and Dogs based on popularity and profitability thresholds.
Deterministic logic separate from the ML service.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ClassificationResult:
    """Result of menu item classification."""

    category: str
    confidence: float
    recommendations: list[str]
    metrics: dict


class MenuEngineeringClassifier:
    """
    Menu Engineering Matrix classifier.

    Uses the standard menu engineering methodology to classify items
    based on their popularity (purchases) and profitability (margin %).

    Usage:
        classifier = MenuEngineeringClassifier()
        result = classifier.classify_item(
            purchases=75,
            price=29.99,
            cost=12.00,
            avg_purchases=50,
            avg_margin_percent=35.0
        )
    """

    # Default thresholds when no context provided
    DEFAULT_POPULARITY_THRESHOLD = 50  # purchases
    DEFAULT_MARGIN_THRESHOLD = 30.0  # percent

    # Category definitions
    STAR = "Star"
    PLOWHORSE = "Plowhorse"
    PUZZLE = "Puzzle"
    DOG = "Dog"

    def __init__(
        self,
        default_popularity_threshold: float = None,
        default_margin_threshold: float = None,
    ):
        """
        Initialize classifier with optional custom default thresholds.

        Args:
            default_popularity_threshold: Default purchases threshold
            default_margin_threshold: Default margin % threshold
        """
        self.default_popularity_threshold = (
            default_popularity_threshold or self.DEFAULT_POPULARITY_THRESHOLD
        )
        self.default_margin_threshold = (
            default_margin_threshold or self.DEFAULT_MARGIN_THRESHOLD
        )

    def calculate_margin_percent(self, price: float, cost: float) -> float:
        """Calculate margin percentage from price and cost."""
        if price <= 0:
            return 0.0
        margin = price - cost
        return (margin / price) * 100

    def classify_item(
        self,
        purchases: int,
        price: float,
        cost: float,
        avg_purchases: Optional[float] = None,
        avg_margin_percent: Optional[float] = None,
        description_length: int = 0,
    ) -> ClassificationResult:
        """
        Classify a single menu item using Menu Engineering Matrix.

        Args:
            purchases: Number of times item was purchased
            price: Selling price
            cost: Cost to produce
            avg_purchases: Average purchases across menu (for threshold)
            avg_margin_percent: Average margin % across menu (for threshold)
            description_length: Length of item description (for recommendations)

        Returns:
            ClassificationResult with category, confidence, and recommendations
        """
        # Calculate metrics
        margin_percent = self.calculate_margin_percent(price, cost)
        margin_amount = price - cost

        # Use provided averages or defaults
        pop_threshold = avg_purchases or self.default_popularity_threshold
        prof_threshold = avg_margin_percent or self.default_margin_threshold

        # Classification logic
        high_popularity = purchases >= pop_threshold
        high_profitability = margin_percent >= prof_threshold

        # Determine category
        if high_popularity and high_profitability:
            category = self.STAR
        elif high_popularity and not high_profitability:
            category = self.PLOWHORSE
        elif not high_popularity and high_profitability:
            category = self.PUZZLE
        else:
            category = self.DOG

        # Calculate confidence based on distance from thresholds
        confidence = self._calculate_confidence(
            purchases, margin_percent, pop_threshold, prof_threshold
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            category, price, margin_percent, description_length
        )

        # Build metrics dict
        metrics = {
            "purchases": purchases,
            "price": float(price),
            "cost": float(cost),
            "margin_amount": round(margin_amount, 2),
            "margin_percent": round(margin_percent, 2),
            "popularity_threshold": pop_threshold,
            "profitability_threshold": prof_threshold,
            "above_popularity_avg": high_popularity,
            "above_profitability_avg": high_profitability,
        }

        return ClassificationResult(
            category=category,
            confidence=confidence,
            recommendations=recommendations,
            metrics=metrics,
        )

    def classify_batch(self, items: list[dict]) -> list[ClassificationResult]:
        """
        Classify multiple items, using batch averages for thresholds.

        Each item dict should have: purchases, price, cost, description_length (optional)

        Args:
            items: List of item dictionaries

        Returns:
            List of ClassificationResult objects
        """
        if not items:
            return []

        # Calculate batch averages for thresholds
        total_purchases = sum(item.get("purchases", 0) for item in items)
        avg_purchases = total_purchases / len(items)

        margins = []
        for item in items:
            price = float(item.get("price", 0))
            cost = float(item.get("cost", 0))
            if price > 0:
                margins.append(self.calculate_margin_percent(price, cost))

        avg_margin = (
            sum(margins) / len(margins) if margins else self.default_margin_threshold
        )

        # Classify each item using batch averages
        results = []
        for item in items:
            result = self.classify_item(
                purchases=item.get("purchases", 0),
                price=float(item.get("price", 0)),
                cost=float(item.get("cost", 0)),
                avg_purchases=avg_purchases,
                avg_margin_percent=avg_margin,
                description_length=item.get("description_length", 0),
            )
            results.append(result)

        return results

    def _calculate_confidence(
        self,
        purchases: int,
        margin_percent: float,
        pop_threshold: float,
        prof_threshold: float,
    ) -> float:
        """
        Calculate confidence score based on distance from thresholds.

        Items further from the threshold boundaries have higher confidence.
        """
        # Normalize distances (how far from threshold as percentage)
        if pop_threshold > 0:
            pop_distance = abs(purchases - pop_threshold) / pop_threshold
        else:
            pop_distance = 1.0

        if prof_threshold > 0:
            prof_distance = abs(margin_percent - prof_threshold) / prof_threshold
        else:
            prof_distance = 1.0

        # Average distance, capped at 1.0
        avg_distance = min((pop_distance + prof_distance) / 2, 1.0)

        # Convert to confidence (0.7 base + up to 0.25 based on distance)
        confidence = 0.70 + (avg_distance * 0.25)

        return round(min(confidence, 0.95), 2)

    def _generate_recommendations(
        self,
        category: str,
        price: float,
        margin_percent: float,
        description_length: int,
    ) -> list[str]:
        """Generate actionable recommendations based on category."""
        recommendations = []

        if category == self.DOG:
            recommendations.append("Consider removing or rebranding this item")
            recommendations.append("Test a 10-15% price reduction to gauge demand")
            recommendations.append("Move to less prominent menu position")
            if description_length < 30:
                recommendations.append("If keeping, add an appealing description")

        elif category == self.PLOWHORSE:
            recommendations.append(
                "Increase price by 5-10% (popular items tolerate increases)"
            )
            recommendations.append("Add premium add-ons to increase margin")
            recommendations.append(
                "Reduce portion size slightly while maintaining value"
            )
            recommendations.append("Review supplier costs for reduction opportunities")

        elif category == self.PUZZLE:
            recommendations.append("Move to a more prominent menu position")
            recommendations.append("Train staff to actively recommend this item")
            recommendations.append("Add to popular bundle combinations")
            if description_length < 50:
                recommendations.append("Enhance description with sensory words")
            recommendations.append("Consider a limited-time promotion for awareness")

        elif category == self.STAR:
            recommendations.append("Maintain current pricing and positioning")
            recommendations.append("Feature prominently on menu")
            recommendations.append("Use as anchor for bundle deals")
            recommendations.append("Monitor competitor pricing for similar items")

        return recommendations


# Singleton instance for convenience
menu_classifier = MenuEngineeringClassifier()


def classify_menu_item(
    purchases: int,
    price: float,
    cost: float,
    avg_purchases: float = None,
    avg_margin_percent: float = None,
    description_length: int = 0,
) -> dict:
    """
    Convenience function to classify a menu item.

    Returns a dictionary with category, confidence, recommendations, and metrics.
    """
    result = menu_classifier.classify_item(
        purchases=purchases,
        price=price,
        cost=cost,
        avg_purchases=avg_purchases,
        avg_margin_percent=avg_margin_percent,
        description_length=description_length,
    )

    return {
        "category": result.category,
        "confidence": result.confidence,
        "recommendations": result.recommendations,
        "metrics": result.metrics,
    }


def classify_menu_items_batch(items: list[dict]) -> list[dict]:
    """
    Convenience function to classify multiple menu items.

    Uses batch averages for threshold calculation.

    Each item dict should have: purchases, price, cost, description_length (optional)
    """
    results = menu_classifier.classify_batch(items)

    return [
        {
            "category": r.category,
            "confidence": r.confidence,
            "recommendations": r.recommendations,
            "metrics": r.metrics,
        }
        for r in results
    ]
