"""
Profit-Optimized Recommendation Engine.

This module implements a sophisticated recommendation system that maximizes
restaurant profit using:
1. Menu Engineering Matrix strategy (prioritize Stars, push Puzzles)
2. Market basket analysis ("frequently bought together")
3. Multi-factor weighted scoring for profit optimization

Key Components:
- CoPurchaseAnalyzer: Market basket analysis using support/confidence/lift
- RecommendationEngine: Multi-strategy recommendation scorer
"""

from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional
from uuid import UUID

from django.core.cache import cache
from django.db.models import Count, Q

from .models import MenuItem, Order, OrderItem


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class ItemAssociation:
    """Represents a co-purchase association between two items."""

    item_id: UUID
    item: MenuItem
    support: float  # How often items appear together / total orders
    confidence: float  # P(B|A) - If customer buys A, probability they buy B
    lift: float  # Confidence / P(B) - How much A increases likelihood of B
    order_count: int  # Number of orders containing both items

    @property
    def message(self) -> str:
        """Human-readable co-purchase message."""
        pct = int(self.confidence * 100)
        return f"{pct}% of customers order this together"


@dataclass
class RecommendationResult:
    """Result of a recommendation with scoring details."""

    item: MenuItem
    score: float  # Overall recommendation score (0-1)
    reason: str  # Human-readable reason
    category_score: float = 0.0
    margin_score: float = 0.0
    copurchase_score: float = 0.0
    popularity_score: float = 0.0
    context_score: float = 0.0
    profit_impact: Optional[Decimal] = None  # Potential margin gain


@dataclass
class AffinityMatrix:
    """Pre-computed co-purchase affinity data."""

    # item_id -> list of (associated_item_id, support, confidence, lift, count)
    associations: dict = field(default_factory=dict)
    total_orders: int = 0
    item_frequencies: dict = field(default_factory=dict)  # item_id -> count


# =============================================================================
# Constants
# =============================================================================

# Category base scores for Menu Engineering Matrix
CATEGORY_SCORES = {
    "star": 1.0,  # High popularity + High profit - Promote heavily
    "puzzle": 0.85,  # Low popularity + High profit - Push for visibility
    "plowhorse": 0.6,  # High popularity + Low profit - Bundle carefully
    "dog": 0.1,  # Low popularity + Low profit - Rarely recommend
    None: 0.5,  # Uncategorized - Neutral
    "uncategorized": 0.5,
}

# Score weights for final recommendation calculation
WEIGHT_CATEGORY = 0.35  # Menu Engineering priority
WEIGHT_MARGIN = 0.30  # Raw profitability
WEIGHT_COPURCHASE = 0.20  # Frequently bought together
WEIGHT_POPULARITY = 0.10  # Social proof
WEIGHT_CONTEXT = 0.05  # Section/preference match

# Cache keys
CACHE_KEY_AFFINITY = "recommendation:affinity_matrix"
CACHE_KEY_FBT_PREFIX = "recommendation:fbt:"
CACHE_TIMEOUT_AFFINITY = 900  # 15 minutes
CACHE_TIMEOUT_FBT = 1800  # 30 minutes


# =============================================================================
# Co-Purchase Analyzer (Market Basket Analysis)
# =============================================================================


class CoPurchaseAnalyzer:
    """
    Market basket analysis for discovering co-purchase patterns.

    Uses association rule mining concepts:
    - Support: Frequency of itemset in all transactions
    - Confidence: P(B|A) = Support(A,B) / Support(A)
    - Lift: Confidence(A->B) / Support(B) - measures association strength
    """

    def __init__(self, min_support: float = 0.01, min_confidence: float = 0.1):
        """
        Initialize analyzer.

        Args:
            min_support: Minimum support threshold (default 1%)
            min_confidence: Minimum confidence threshold (default 10%)
        """
        self.min_support = min_support
        self.min_confidence = min_confidence

    def build_affinity_matrix(self, use_cache: bool = True) -> AffinityMatrix:
        """
        Build co-purchase affinity matrix from order history.

        Returns:
            AffinityMatrix with all item associations
        """
        # Check cache first
        if use_cache:
            cached = cache.get(CACHE_KEY_AFFINITY)
            if cached:
                return cached

        # Get all completed orders with their items
        orders = Order.objects.filter(
            status__in=["completed", "delivered", "ready"]
        ).prefetch_related("items__menu_item")

        total_orders = orders.count()
        if total_orders == 0:
            return AffinityMatrix(total_orders=0)

        # Count item frequencies and co-occurrences
        item_counts = defaultdict(int)  # item_id -> count
        pair_counts = defaultdict(int)  # (item_a, item_b) -> count

        for order in orders:
            # Get unique menu items in this order
            items_in_order = set()
            for order_item in order.items.all():
                if order_item.menu_item:
                    items_in_order.add(order_item.menu_item.id)

            # Update individual counts
            for item_id in items_in_order:
                item_counts[item_id] += 1

            # Update pair counts (both directions for easy lookup)
            items_list = list(items_in_order)
            for i, item_a in enumerate(items_list):
                for item_b in items_list[i + 1 :]:
                    pair_counts[(item_a, item_b)] += 1
                    pair_counts[(item_b, item_a)] += 1

        # Build associations with support/confidence/lift
        associations = defaultdict(list)

        for (item_a, item_b), pair_count in pair_counts.items():
            support = pair_count / total_orders
            if support < self.min_support:
                continue

            # Confidence: P(B|A) = P(A,B) / P(A)
            confidence = pair_count / item_counts[item_a] if item_counts[item_a] else 0
            if confidence < self.min_confidence:
                continue

            # Lift: Confidence / P(B)
            p_b = item_counts[item_b] / total_orders if total_orders else 0
            lift = confidence / p_b if p_b > 0 else 0

            associations[item_a].append(
                {
                    "item_id": item_b,
                    "support": support,
                    "confidence": confidence,
                    "lift": lift,
                    "count": pair_count,
                }
            )

        # Sort associations by lift (strongest associations first)
        for item_id in associations:
            associations[item_id].sort(key=lambda x: x["lift"], reverse=True)

        matrix = AffinityMatrix(
            associations=dict(associations),
            total_orders=total_orders,
            item_frequencies=dict(item_counts),
        )

        # Cache the result
        if use_cache:
            cache.set(CACHE_KEY_AFFINITY, matrix, CACHE_TIMEOUT_AFFINITY)

        return matrix

    def get_item_associations(
        self, item_id: UUID, limit: int = 5, use_cache: bool = True
    ) -> list[ItemAssociation]:
        """
        Get items frequently bought together with the given item.

        Args:
            item_id: The source item UUID
            limit: Maximum associations to return
            use_cache: Whether to use cached data

        Returns:
            List of ItemAssociation objects sorted by lift
        """
        # Check item-specific cache first
        if use_cache:
            cache_key = f"{CACHE_KEY_FBT_PREFIX}{item_id}"
            cached = cache.get(cache_key)
            if cached:
                return cached[:limit]

        matrix = self.build_affinity_matrix(use_cache=use_cache)

        # If item not in cached matrix, try rebuilding without cache
        if item_id not in matrix.associations and use_cache:
            matrix = self.build_affinity_matrix(use_cache=False)

        if item_id not in matrix.associations:
            return []

        # Get associated items with full details
        associations = []
        for assoc_data in matrix.associations[item_id][:limit]:
            try:
                item = MenuItem.objects.get(id=assoc_data["item_id"], is_active=True)
                associations.append(
                    ItemAssociation(
                        item_id=assoc_data["item_id"],
                        item=item,
                        support=assoc_data["support"],
                        confidence=assoc_data["confidence"],
                        lift=assoc_data["lift"],
                        order_count=assoc_data["count"],
                    )
                )
            except MenuItem.DoesNotExist:
                continue

        # Cache the result
        if use_cache:
            cache_key = f"{CACHE_KEY_FBT_PREFIX}{item_id}"
            cache.set(cache_key, associations, CACHE_TIMEOUT_FBT)

        return associations

    def calculate_lift(self, item_a: UUID, item_b: UUID) -> float:
        """Calculate lift between two specific items."""
        matrix = self.build_affinity_matrix()

        if item_a not in matrix.associations:
            return 0.0

        for assoc in matrix.associations[item_a]:
            if assoc["item_id"] == item_b:
                return assoc["lift"]

        return 0.0


# =============================================================================
# Recommendation Engine
# =============================================================================


class RecommendationEngine:
    """
    Profit-optimized menu recommendation system.

    Combines multiple scoring strategies:
    1. Strategic (Menu Engineering Matrix) - Prioritize Stars/Puzzles
    2. Profitability (Margin) - Higher margin = higher score
    3. Co-purchase (Association) - Frequently bought together
    4. Popularity (Social proof) - Purchase counts
    5. Context (Relevance) - Section/preference matching
    """

    def __init__(self):
        self.analyzer = CoPurchaseAnalyzer()

    def get_recommendations(
        self,
        current_items: list[UUID] = None,
        session_id: str = None,
        section_id: UUID = None,
        exclude_ids: list[UUID] = None,
        limit: int = 5,
        strategy: str = "balanced",
    ) -> list[RecommendationResult]:
        """
        Get personalized menu recommendations.

        Args:
            current_items: Items already in cart (for context)
            session_id: Customer session for personalization
            section_id: Filter recommendations to specific section
            exclude_ids: Items to exclude from recommendations
            limit: Maximum recommendations to return
            strategy: "balanced", "upsell" (high margin), or "cross_sell" (variety)

        Returns:
            List of RecommendationResult sorted by score
        """
        current_items = current_items or []
        exclude_ids = set(exclude_ids or [])
        exclude_ids.update(current_items)  # Don't recommend items already in cart

        # Get candidate items
        candidates = MenuItem.objects.filter(is_active=True).exclude(id__in=exclude_ids)

        if section_id:
            candidates = candidates.filter(section_id=section_id)

        # Get co-purchase data for context
        copurchase_scores = {}
        if current_items:
            copurchase_scores = self._get_copurchase_scores(current_items)

        # Get menu statistics for normalization
        stats = self._get_menu_stats()

        # Score each candidate
        results = []
        for item in candidates:
            result = self._score_item(
                item,
                copurchase_scores=copurchase_scores,
                stats=stats,
                strategy=strategy,
            )
            results.append(result)

        # Sort by score and return top N
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]

    def get_frequently_bought_together(
        self, item_id: UUID, limit: int = 3
    ) -> list[ItemAssociation]:
        """
        Get items frequently purchased with the given item.

        This is a direct wrapper around CoPurchaseAnalyzer for the API.
        """
        return self.analyzer.get_item_associations(item_id, limit=limit)

    def get_upsell_suggestions(
        self, current_items: list[UUID], limit: int = 3
    ) -> list[RecommendationResult]:
        """
        Get upsell suggestions focused on high-margin items.

        Uses "upsell" strategy to prioritize profit over other factors.
        """
        return self.get_recommendations(
            current_items=current_items,
            limit=limit,
            strategy="upsell",
        )

    def get_cross_sell_suggestions(
        self, current_items: list[UUID], limit: int = 3
    ) -> list[RecommendationResult]:
        """
        Get cross-sell suggestions for variety/complementary items.

        Suggests items from different sections than current cart.
        """
        # Find sections already in cart
        current_sections = set(
            MenuItem.objects.filter(id__in=current_items).values_list(
                "section_id", flat=True
            )
        )

        recommendations = self.get_recommendations(
            current_items=current_items,
            limit=limit * 2,  # Get more, then filter
            strategy="cross_sell",
        )

        # Prioritize items from different sections
        cross_sell = [
            r for r in recommendations if r.item.section_id not in current_sections
        ]
        same_section = [
            r for r in recommendations if r.item.section_id in current_sections
        ]

        return (cross_sell + same_section)[:limit]

    def _score_item(
        self,
        item: MenuItem,
        copurchase_scores: dict,
        stats: dict,
        strategy: str,
    ) -> RecommendationResult:
        """Calculate comprehensive score for an item."""

        # 1. Category score (Menu Engineering Matrix)
        category_score = CATEGORY_SCORES.get(item.category, 0.5)

        # 2. Margin score (normalized 0-1)
        margin_score = self._normalize_margin(item, stats)

        # 3. Co-purchase score
        copurchase_score = copurchase_scores.get(item.id, 0.0)

        # 4. Popularity score (normalized 0-1)
        popularity_score = self._normalize_popularity(item, stats)

        # 5. Context score (placeholder - can be enhanced with preferences)
        context_score = 0.5  # Neutral for now

        # Adjust weights based on strategy
        weights = self._get_strategy_weights(strategy)

        # Calculate final score
        score = (
            category_score * weights["category"]
            + margin_score * weights["margin"]
            + copurchase_score * weights["copurchase"]
            + popularity_score * weights["popularity"]
            + context_score * weights["context"]
        )

        # Generate reason
        reason = self._generate_reason(
            item, category_score, margin_score, copurchase_score, popularity_score
        )

        # Calculate profit impact
        profit_impact = item.margin if hasattr(item, "margin") else None

        return RecommendationResult(
            item=item,
            score=round(score, 3),
            reason=reason,
            category_score=round(category_score, 3),
            margin_score=round(margin_score, 3),
            copurchase_score=round(copurchase_score, 3),
            popularity_score=round(popularity_score, 3),
            context_score=round(context_score, 3),
            profit_impact=profit_impact,
        )

    def _get_copurchase_scores(self, current_items: list[UUID]) -> dict:
        """Get co-purchase scores for all items based on cart contents."""
        scores = defaultdict(float)

        for item_id in current_items:
            associations = self.analyzer.get_item_associations(item_id, limit=10)
            for assoc in associations:
                # Use lift as the score, accumulate across cart items
                scores[assoc.item_id] = max(scores[assoc.item_id], assoc.lift / 5)

        # Normalize to 0-1
        if scores:
            max_score = max(scores.values())
            if max_score > 1:
                scores = {k: v / max_score for k, v in scores.items()}

        return dict(scores)

    def _get_menu_stats(self) -> dict:
        """Get menu statistics for normalization."""
        cache_key = "recommendation:menu_stats"
        cached = cache.get(cache_key)
        if cached:
            return cached

        items = MenuItem.objects.filter(is_active=True)
        purchases = list(items.values_list("total_purchases", flat=True))
        margins = []
        for item in items:
            if hasattr(item, "margin"):
                margins.append(float(item.margin))

        stats = {
            "max_purchases": max(purchases) if purchases else 1,
            "avg_purchases": sum(purchases) / len(purchases) if purchases else 0,
            "max_margin": max(margins) if margins else 1,
            "avg_margin": sum(margins) / len(margins) if margins else 0,
        }

        cache.set(cache_key, stats, 300)  # 5 min cache
        return stats

    def _normalize_margin(self, item: MenuItem, stats: dict) -> float:
        """Normalize item margin to 0-1 scale."""
        if not hasattr(item, "margin"):
            return 0.5
        margin = float(item.margin)
        max_margin = stats.get("max_margin", 1) or 1
        return min(margin / max_margin, 1.0)

    def _normalize_popularity(self, item: MenuItem, stats: dict) -> float:
        """Normalize item popularity to 0-1 scale."""
        max_purchases = stats.get("max_purchases", 1) or 1
        return min(item.total_purchases / max_purchases, 1.0)

    def _get_strategy_weights(self, strategy: str) -> dict:
        """Get scoring weights based on strategy."""
        if strategy == "upsell":
            # Focus on margin and strategic value
            return {
                "category": 0.30,
                "margin": 0.45,
                "copurchase": 0.15,
                "popularity": 0.05,
                "context": 0.05,
            }
        elif strategy == "cross_sell":
            # Focus on co-purchase and context
            return {
                "category": 0.25,
                "margin": 0.20,
                "copurchase": 0.35,
                "popularity": 0.10,
                "context": 0.10,
            }
        else:  # balanced
            return {
                "category": WEIGHT_CATEGORY,
                "margin": WEIGHT_MARGIN,
                "copurchase": WEIGHT_COPURCHASE,
                "popularity": WEIGHT_POPULARITY,
                "context": WEIGHT_CONTEXT,
            }

    def _generate_reason(
        self,
        item: MenuItem,
        category_score: float,
        margin_score: float,
        copurchase_score: float,
        popularity_score: float,
    ) -> str:
        """Generate human-readable recommendation reason."""
        reasons = []

        # Category-based reason
        if item.category == "star":
            reasons.append("⭐ Popular favorite")
        elif item.category == "puzzle":
            reasons.append("💎 Hidden gem")

        # Co-purchase reason
        if copurchase_score > 0.5:
            reasons.append("🍽️ Pairs perfectly with your order")
        elif copurchase_score > 0.2:
            reasons.append("👥 Often ordered together")

        # Popularity reason
        if popularity_score > 0.7:
            reasons.append("🔥 Customer favorite")

        # Margin reason (only for backend/owner view)
        if margin_score > 0.8:
            reasons.append("💰 Great value")

        if not reasons:
            reasons.append("✨ Recommended for you")

        return " • ".join(reasons[:2])


# =============================================================================
# Singleton instances for convenience
# =============================================================================

copurchase_analyzer = CoPurchaseAnalyzer()
recommendation_engine = RecommendationEngine()


# =============================================================================
# Convenience functions
# =============================================================================


def get_recommendations(
    current_items: list[UUID] = None,
    limit: int = 5,
    strategy: str = "balanced",
) -> list[dict]:
    """
    Convenience function to get recommendations.

    Returns dictionaries instead of dataclass objects.
    """
    results = recommendation_engine.get_recommendations(
        current_items=current_items,
        limit=limit,
        strategy=strategy,
    )
    return [
        {
            "item_id": str(r.item.id),
            "title": r.item.title,
            "price": str(r.item.price),
            "category": r.item.category,
            "score": r.score,
            "reason": r.reason,
            "profit_impact": str(r.profit_impact) if r.profit_impact else None,
        }
        for r in results
    ]


def get_frequently_bought_together(item_id: UUID, limit: int = 3) -> list[dict]:
    """
    Convenience function to get frequently bought together items.

    Returns dictionaries instead of dataclass objects.
    """
    associations = recommendation_engine.get_frequently_bought_together(
        item_id, limit=limit
    )
    return [
        {
            "item_id": str(a.item_id),
            "title": a.item.title,
            "price": str(a.item.price),
            "category": a.item.category,
            "confidence": round(a.confidence, 3),
            "lift": round(a.lift, 2),
            "message": a.message,
        }
        for a in associations
    ]
