"""
Celery tasks for recommendation engine background processing.

Pre-computes expensive calculations so real-time API requests are instant:
- rebuild_affinity_matrix: Recompute co-purchase associations
- cache_top_recommendations: Pre-cache recommendations for popular items
- update_item_popularity_scores: Refresh popularity rankings
"""

from celery import shared_task
from django.core.cache import cache

from .models import MenuItem


@shared_task(name="menu.rebuild_affinity_matrix")
def rebuild_affinity_matrix():
    """
    Recompute co-purchase associations from order history.

    Should be run every 15 minutes or after significant order activity.
    This task builds the affinity matrix and stores it in Redis cache.
    """
    from .recommendation_engine import CoPurchaseAnalyzer

    analyzer = CoPurchaseAnalyzer()
    matrix = analyzer.build_affinity_matrix(use_cache=False)  # Force rebuild

    # Store in cache
    cache.set("recommendation:affinity_matrix", matrix, timeout=3600)

    return {
        "status": "success",
        "total_orders": matrix.total_orders,
        "items_with_associations": len(matrix.associations),
        "total_associations": sum(len(v) for v in matrix.associations.values()),
    }


@shared_task(name="menu.cache_top_recommendations")
def cache_top_recommendations():
    """
    Pre-cache frequently bought together recommendations for popular items.

    Should be run every 30 minutes. Pre-caches recommendations for items
    with more than 10 purchases to ensure fast API responses.
    """
    from .recommendation_engine import recommendation_engine, CACHE_KEY_FBT_PREFIX

    # Get popular items (more than 10 purchases)
    popular_items = MenuItem.objects.filter(
        is_active=True, total_purchases__gt=10
    ).values_list("id", flat=True)

    cached_count = 0
    for item_id in popular_items:
        associations = recommendation_engine.get_frequently_bought_together(
            item_id, limit=5
        )
        cache.set(f"{CACHE_KEY_FBT_PREFIX}{item_id}", associations, timeout=1800)
        cached_count += 1

    return {
        "status": "success",
        "items_cached": cached_count,
    }


@shared_task(name="menu.update_item_popularity_scores")
def update_item_popularity_scores():
    """
    Refresh popularity rankings based on recent orders.

    Should be run hourly. Computes rolling popularity scores
    and updates the menu stats cache.
    """
    from django.db.models import Sum
    from django.utils import timezone
    from datetime import timedelta

    # Calculate rolling 30-day popularity
    thirty_days_ago = timezone.now() - timedelta(days=30)

    # Get purchase counts from recent orders
    from .models import OrderItem, Order

    recent_purchases = (
        OrderItem.objects.filter(
            order__created_at__gte=thirty_days_ago,
            order__status__in=["completed", "delivered", "ready"],
            menu_item__isnull=False,
        )
        .values("menu_item")
        .annotate(recent_count=Sum("quantity"))
    )

    # Update cache with stats
    items = MenuItem.objects.filter(is_active=True)
    purchases = list(items.values_list("total_purchases", flat=True))
    margins = []
    for item in items:
        try:
            margins.append(float(item.margin))
        except (AttributeError, TypeError):
            pass

    stats = {
        "max_purchases": max(purchases) if purchases else 1,
        "avg_purchases": sum(purchases) / len(purchases) if purchases else 0,
        "max_margin": max(margins) if margins else 1,
        "avg_margin": sum(margins) / len(margins) if margins else 0,
        "recent_popularity": {
            str(p["menu_item"]): p["recent_count"] for p in recent_purchases
        },
    }

    cache.set("recommendation:menu_stats", stats, timeout=3600)

    return {
        "status": "success",
        "items_analyzed": len(purchases),
        "recent_orders_analyzed": len(recent_purchases),
    }


@shared_task(name="menu.warm_recommendation_cache")
def warm_recommendation_cache():
    """
    Warm up all recommendation caches.

    Convenience task that runs all cache-building tasks in sequence.
    Should be run on application startup or after cache clear.
    """
    results = {}

    # Step 1: Build affinity matrix
    results["affinity"] = rebuild_affinity_matrix()

    # Step 2: Update popularity scores
    results["popularity"] = update_item_popularity_scores()

    # Step 3: Cache top recommendations
    results["recommendations"] = cache_top_recommendations()

    return results
