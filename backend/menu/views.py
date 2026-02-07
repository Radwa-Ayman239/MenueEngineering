"""
API Views for the Menu app with role-based permissions.

Permissions:
- Managers/Admins: Full access to menu management, analytics, AI analysis
- Staff: Can create orders, view menu
- Customers (unauthenticated): Can only view menu sections and items (read-only)
"""

from rest_framework import viewsets, status
from rest_framework.pagination import PageNumberPagination  
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, SAFE_METHODS
from rest_framework.views import APIView
from knox.auth import TokenAuthentication
from django.utils import timezone
from django.db.models import Sum, Count
from drf_spectacular.utils import extend_schema


from .models import MenuSection, MenuItem, Order, CustomerActivity
from .serializers import (
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
    CustomerActivitySerializer,
    CustomerActivityCreateSerializer,
)
from .services import ml_service, MLServiceError
from .menu_classifier import classify_menu_item, classify_menu_items_batch
from .permissions import (
    IsAdminOrManager,
    IsStaffOrAbove,
)

# 1. Define the Pagination Class first
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 50 
    page_size_query_param = 'page_size'
    max_page_size = 100

# ============ Menu Section Views ============


class MenuSectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for MenuSection CRUD operations.

    Permissions:
    - GET (list/retrieve): Public (unauthenticated allowed)
    - POST/PUT/PATCH/DELETE: Managers and Admins only

    Endpoints:
    - GET    /sections/          - List all sections
    - POST   /sections/          - Create a section (managers only)
    - GET    /sections/{id}/     - Get section details
    - PUT    /sections/{id}/     - Update a section (managers only)
    - DELETE /sections/{id}/     - Delete a section (managers only)
    """

    queryset = MenuSection.objects.all()

    def get_authenticators(self):
        """Allow unauthenticated access for safe methods"""
        if getattr(self, "request", None) and self.request.method in SAFE_METHODS:
            return []
        return [TokenAuthentication()]

    def get_permissions(self):
        """
        - Read operations: Public
        - Write operations: Managers/Admins only
        """
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAuthenticated(), IsAdminOrManager()]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return MenuSectionCreateSerializer
        return MenuSectionSerializer

    def get_queryset(self):
        queryset = MenuSection.objects.all()

        # Filter by active status
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")

        # For public access, only show active sections
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)

        return queryset.order_by("display_order", "name")


# ============ Menu Item Views ============


class MenuItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for MenuItem CRUD operations with AI analysis.

    Permissions:
    - GET (list/retrieve): Public (unauthenticated allowed)
    - POST/PUT/PATCH/DELETE: Managers and Admins only
    - analyze/bulk_analyze/stats: Managers and Admins only

    Endpoints:
    - GET    /items/                  - List all items (public)
    - POST   /items/                  - Create item (managers only)
    - GET    /items/{id}/             - Get item details (public)
    - PUT    /items/{id}/             - Update item (managers only)
    - DELETE /items/{id}/             - Delete item (managers only)
    - POST   /items/{id}/analyze/     - AI analysis (managers only)
    - POST   /items/bulk_analyze/     - Bulk AI analysis (managers only)
    - GET    /items/stats/            - Category stats (managers only)
    """

    queryset = MenuItem.objects.all()

    def get_authenticators(self):
        """Allow unauthenticated access for safe methods"""
        action = getattr(self, "action", None)
        request = getattr(self, "request", None)
        if request and request.method in SAFE_METHODS and action not in ["stats"]:
            return []
        return [TokenAuthentication()]

    def get_permissions(self):
        """
        - Read operations (list, retrieve): Public
        - Stats, analyze: Managers/Admins only
        - Write operations: Managers/Admins only
        """
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        if self.action in ["stats", "analyze", "bulk_analyze"]:
            return [IsAuthenticated(), IsAdminOrManager()]
        return [IsAuthenticated(), IsAdminOrManager()]

    def get_serializer_class(self):
        if self.action == "list":
            return MenuItemListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return MenuItemCreateSerializer
        elif self.action == "analyze":
            return MenuItemAnalysisSerializer
        return MenuItemDetailSerializer

    def get_queryset(self):
        queryset = MenuItem.objects.select_related("section").all()

        # Filter by section
        section_id = self.request.query_params.get("section")
        if section_id:
            queryset = queryset.filter(section_id=section_id)

        # Filter by category
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category=category)

        # Filter by active status
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")

        # For public access, only show active items
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)

        return queryset.order_by("section", "display_order", "title")

    @extend_schema(
        responses={200: MenuItemAnalysisSerializer},
        description="Run Menu Engineering analysis on a menu item. Managers only.",
    )
    @action(detail=True, methods=["post"])
    def analyze(self, request, pk=None):
        """
        Analyze a single menu item using the Menu Engineering Matrix.

        Returns category (Star/Plowhorse/Puzzle/Dog), confidence score, and recommendations.
        """
        item = self.get_object()

        # Use local classifier
        result = classify_menu_item(
            purchases=item.total_purchases,
            price=float(item.price),
            cost=float(item.cost),
            description_length=len(item.description) if item.description else 0,
        )

        # Update item with classification
        item.category = result["category"].lower()
        item.ai_confidence = result["confidence"]
        item.last_analyzed = timezone.now()
        item.save(update_fields=["category", "ai_confidence", "last_analyzed"])

        return Response(
            {
                "id": str(item.id),
                "title": item.title,
                "category": result["category"],
                "confidence": result["confidence"],
                "recommendations": result["recommendations"],
                "metrics": result["metrics"],
            }
        )

    @extend_schema(description="Analyze all active menu items. Managers only.")
    @action(detail=False, methods=["post"])
    def bulk_analyze(self, request):
        """
        Analyze all active menu items using the Menu Engineering Matrix.
        Uses batch averages for more accurate threshold-based classification.
        """
        items = list(MenuItem.objects.filter(is_active=True))

        if not items:
            return Response({"message": "No items to analyze"})

        # Prepare batch data
        batch_data = [
            {
                "purchases": item.total_purchases,
                "price": float(item.price),
                "cost": float(item.cost),
                "description_length": len(item.description) if item.description else 0,
            }
            for item in items
        ]

        # Classify using batch averages for thresholds
        predictions = classify_menu_items_batch(batch_data)

        # Update all items
        results = []
        for item, prediction in zip(items, predictions):
            item.category = prediction["category"].lower()
            item.ai_confidence = prediction["confidence"]
            item.last_analyzed = timezone.now()
            item.save(update_fields=["category", "ai_confidence", "last_analyzed"])

            results.append(
                {
                    "id": str(item.id),
                    "title": item.title,
                    "category": prediction["category"],
                    "confidence": prediction["confidence"],
                }
            )

        return Response({"analyzed_count": len(results), "results": results})

    @extend_schema(description="Get menu item statistics. Managers only.")
    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get menu item statistics grouped by category."""
        stats = (
            MenuItem.objects.filter(is_active=True)
            .values("category")
            .annotate(
                count=Count("id"),
                total_revenue=Sum("total_revenue"),
                total_purchases=Sum("total_purchases"),
            )
        )

        return Response(
            {
                "categories": list(stats),
                "total_items": MenuItem.objects.filter(is_active=True).count(),
            }
        )
    


# ============ Order Views ============


class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Order CRUD operations.

    Permissions:
    - All operations: Staff, Managers, and Admins only
    - Stats: Managers and Admins only

    Endpoints:
    - GET    /orders/                     - List orders (staff+)
    - POST   /orders/                     - Create order (staff+)
    - GET    /orders/{id}/                - Get order details (staff+)
    - PATCH  /orders/{id}/update_status/  - Update status (staff+)
    - GET    /orders/stats/               - Order stats (managers only)
    """

    queryset = Order.objects.all()
    authentication_classes = [TokenAuthentication]

    def get_permissions(self):
        """
        - Stats: Managers/Admins only
        - All other operations: Any staff member
        """
        if self.action == "stats":
            return [IsAuthenticated(), IsAdminOrManager()]
        return [IsAuthenticated(), IsStaffOrAbove()]

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        elif self.action == "create":
            return OrderCreateSerializer
        elif self.action == "update_status":
            return OrderStatusUpdateSerializer
        return OrderDetailSerializer

    def get_queryset(self):
        queryset = Order.objects.select_related("created_by").prefetch_related(
            "items__menu_item"
        )

        # Staff can only see their own orders, managers/admins can see all
        if self.request.user.type == "staff":
            queryset = queryset.filter(created_by=self.request.user)

        # Filter by status
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by date range
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

        return queryset.order_by("-created_at")

    @extend_schema(
        request=OrderStatusUpdateSerializer,
        responses={200: OrderDetailSerializer},
        description="Update the status of an order.",
    )
    @action(detail=True, methods=["patch"])
    def update_status(self, request, pk=None):
        """Update order status."""
        order = self.get_object()
        serializer = OrderStatusUpdateSerializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(OrderDetailSerializer(order).data)

    @extend_schema(description="Get order statistics. Managers only.")
    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get order statistics."""
        from django.db.models import Avg

        today = timezone.now().date()

        stats = {
            "today": {
                "count": Order.objects.filter(created_at__date=today).count(),
                "revenue": Order.objects.filter(created_at__date=today).aggregate(
                    total=Sum("total")
                )["total"]
                or 0,
            },
            "by_status": list(
                Order.objects.values("status").annotate(count=Count("id"))
            ),
            "average_order_value": Order.objects.aggregate(avg=Avg("total"))["avg"]
            or 0,
        }

        return Response(stats)


# ============ Customer Activity Views ============


class CustomerActivityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for tracking customer activities.

    Permissions:
    - POST (create): Public (for logging customer interactions)
    - GET (list/stats): Managers and Admins only

    Endpoints:
    - GET  /activities/       - List activities (managers only)
    - POST /activities/       - Log activity (public)
    - GET  /activities/stats/ - Activity stats (managers only)
    """

    queryset = CustomerActivity.objects.all()
    http_method_names = ["get", "post", "head", "options"]  # No update/delete

    def get_authenticators(self):
        """Allow unauthenticated access for creating activities"""
        action = getattr(self, "action", None)
        if action == "create":
            return []
        return [TokenAuthentication()]

    def get_permissions(self):
        """
        - Create: Public (for logging)
        - List/Stats: Managers/Admins only
        """
        if self.action == "create":
            return [AllowAny()]
        return [IsAuthenticated(), IsAdminOrManager()]

    def get_serializer_class(self):
        if self.action == "create":
            return CustomerActivityCreateSerializer
        return CustomerActivitySerializer

    def get_queryset(self):
        queryset = CustomerActivity.objects.select_related("menu_item")

        # Filter by event type
        event_type = self.request.query_params.get("event_type")
        if event_type:
            queryset = queryset.filter(event_type=event_type)

        # Filter by menu item
        menu_item_id = self.request.query_params.get("menu_item")
        if menu_item_id:
            queryset = queryset.filter(menu_item_id=menu_item_id)

        # Filter by session
        session_id = self.request.query_params.get("session")
        if session_id:
            queryset = queryset.filter(session_id=session_id)

        return queryset.order_by("-timestamp")[:1000]  # Limit for performance

    @extend_schema(description="Get activity statistics. Managers only.")
    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get activity statistics."""
        stats = CustomerActivity.objects.values("event_type").annotate(
            count=Count("id")
        )

        # Most viewed items
        most_viewed = (
            CustomerActivity.objects.filter(event_type="view", menu_item__isnull=False)
            .values("menu_item__id", "menu_item__title")
            .annotate(views=Count("id"))
            .order_by("-views")[:10]
        )

        return Response(
            {"by_event_type": list(stats), "most_viewed_items": list(most_viewed)}
        )


# ============ ML Service Health Check ============


class MLServiceHealthView(APIView):
    """
    Check ML service health status.

    This endpoint is public for monitoring purposes.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        health = ml_service.health_check()
        status_code = (
            status.HTTP_200_OK
            if health.get("status") == "healthy"
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )
        return Response(health, status=status_code)


# ============ Public Menu View (for customers) ============


class PublicMenuView(APIView):
    """
    Public endpoint to get the full menu for customers.

    Returns all active sections with their active items.
    No authentication required.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        sections = MenuSection.objects.filter(is_active=True).order_by("display_order")

        menu = []
        for section in sections:
            items = (
                MenuItem.objects.filter(section=section, is_active=True)
                .order_by("display_order")
                .values("id", "title", "description", "price")
            )

            menu.append(
                {
                    "id": str(section.id),
                    "name": section.name,
                    "description": section.description,
                    "items": list(items),
                }
            )

        return Response({"menu": menu})


# ============ AI-Powered Views ============


class EnhanceDescriptionView(APIView):
    """
    Use AI to enhance a menu item's description.

    Permissions: Managers and Admins only
    Method: POST

    Request body:
        {
            "item_id": "uuid" (optional, to auto-fetch item details),
            "item_name": "string",
            "current_description": "string",
            "category": "Star|Plowhorse|Puzzle|Dog",
            "price": 18.99,
            "cuisine_type": "American"
        }

    Returns enhanced description with selling points and tips.
    """

    permission_classes = [IsAuthenticated, IsAdminOrManager]

    def post(self, request):
        item_id = request.data.get("item_id")

        # If item_id provided, fetch details from database
        if item_id:
            try:
                item = MenuItem.objects.get(id=item_id)
                item_name = item.title
                current_description = item.description or ""
                category = item.category or "Unknown"
                price = float(item.price)
            except MenuItem.DoesNotExist:
                return Response(
                    {"error": "Menu item not found"}, status=status.HTTP_404_NOT_FOUND
                )
        else:
            item_name = request.data.get("item_name")
            current_description = request.data.get("current_description", "")
            category = request.data.get("category", "Unknown")
            price = float(request.data.get("price", 0))

        cuisine_type = request.data.get("cuisine_type", "restaurant")

        if not item_name:
            return Response(
                {"error": "item_name is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = ml_service.enhance_description_sync(
                item_name=item_name,
                current_description=current_description,
                category=category,
                price=price,
                cuisine_type=cuisine_type,
            )
            return Response(result)
        except MLServiceError as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


class SalesSuggestionsView(APIView):
    """
    Get AI-powered sales suggestions for a menu item.

    Permissions: Managers and Admins only
    Method: POST

    Request body:
        {
            "item_id": "uuid" (optional, to auto-fetch item details),
            "item_name": "string",
            "category": "Star|Plowhorse|Puzzle|Dog",
            "price": 45.99,
            "cost": 18.00,
            "purchases": 120
        }

    Returns priority, suggested price, actions, marketing tips.
    """

    permission_classes = [IsAuthenticated, IsAdminOrManager]

    def post(self, request):
        item_id = request.data.get("item_id")

        if item_id:
            try:
                item = MenuItem.objects.get(id=item_id)
                item_name = item.title
                category = item.category or "Unknown"
                price = float(item.price)
                cost = float(item.cost) if item.cost else price * 0.4
                purchases = item.total_purchases
            except MenuItem.DoesNotExist:
                return Response(
                    {"error": "Menu item not found"}, status=status.HTTP_404_NOT_FOUND
                )
        else:
            item_name = request.data.get("item_name")
            category = request.data.get("category", "Unknown")
            price = request.data.get("price")
            cost = request.data.get("cost")
            purchases = request.data.get("purchases")

            # Validate required fields when not using item_id
            if not item_name or price is None or cost is None or purchases is None:
                return Response(
                    {"error": "item_name, price, cost, and purchases are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            price = float(price)
            cost = float(cost)
            purchases = int(purchases)

        if not item_name:
            return Response(
                {"error": "item_name is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = ml_service.get_sales_suggestions_sync(
                item_name=item_name,
                category=category,
                price=price,
                cost=cost,
                purchases=purchases,
                section_avg_price=request.data.get("section_avg_price"),
                section_avg_sales=request.data.get("section_avg_sales"),
            )
            return Response(result)
        except MLServiceError as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


class MenuStructureAnalysisView(APIView):
    """
    Analyze menu structure and get optimization recommendations.

    Permissions: Managers and Admins only
    Method: POST

    Request body (optional, auto-fetches if not provided):
        {
            "sections": [
                {
                    "name": "Appetizers",
                    "items": [{"name": "Wings", "price": 12.99, "category": "Star"}]
                }
            ]
        }

    Returns overall score, recommendations, items to highlight/reconsider.
    """

    permission_classes = [IsAuthenticated, IsAdminOrManager]

    def post(self, request):
        sections_data = request.data.get("sections")

        # Auto-fetch from database if not provided
        if not sections_data:
            sections = MenuSection.objects.filter(is_active=True).order_by(
                "display_order"
            )
            sections_data = []

            for section in sections:
                items = MenuItem.objects.filter(
                    section=section, is_active=True
                ).order_by("display_order")

                items_data = [
                    {
                        "name": item.title,
                        "price": float(item.price),
                        "category": item.category or "Unknown",
                        "purchases": item.total_purchases,
                    }
                    for item in items
                ]

                sections_data.append({"name": section.name, "items": items_data})

        if not sections_data:
            return Response(
                {"error": "No menu sections found"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = ml_service.analyze_menu_structure_sync(sections_data)
            return Response(result)
        except MLServiceError as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


class CustomerRecommendationsView(APIView):
    """
    Get personalized item recommendations for a customer.

    Permissions: Public (for customer use)
    Method: POST

    Request body:
        {
            "current_items": ["Burger", "Fries"],
            "budget_remaining": 15.00,
            "preferences": ["vegetarian", "spicy"]
        }

    Returns top recommendation, alternatives, upsells.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        current_items = request.data.get("current_items", [])
        budget_remaining = request.data.get("budget_remaining")
        preferences = request.data.get("preferences")

        # Fetch active menu items
        items = MenuItem.objects.filter(is_active=True).values(
            "title", "price", "section__name"
        )

        menu_items = [
            {
                "name": item["title"],
                "price": float(item["price"]),
                "section": item["section__name"],
            }
            for item in items
        ]

        if not menu_items:
            return Response(
                {"error": "No menu items available"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = ml_service.get_customer_recommendations_sync(
                current_items=current_items,
                menu_items=menu_items,
                budget_remaining=budget_remaining,
                preferences=preferences,
            )
            return Response(result)
        except MLServiceError as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


class OwnerReportView(APIView):
    """
    Generate an AI-powered insights report for owners.

    Permissions: Managers and Admins only
    Method: POST

    Request body:
        {
            "period": "daily|weekly|monthly",
            "summary_data": {} (optional, auto-generated if not provided)
        }

    Returns executive summary, highlights, concerns, recommendations.
    """

    permission_classes = [IsAuthenticated, IsAdminOrManager]

    def post(self, request):
        period = request.data.get("period", "weekly")
        summary_data = request.data.get("summary_data")

        # Auto-generate summary if not provided
        if not summary_data:
            from django.db.models import Sum, Count, Avg
            from datetime import datetime, timedelta

            # Calculate date range based on period
            if period == "daily":
                start_date = datetime.now() - timedelta(days=1)
            elif period == "monthly":
                start_date = datetime.now() - timedelta(days=30)
            else:  # weekly
                start_date = datetime.now() - timedelta(days=7)

            # Get order stats
            orders = Order.objects.filter(created_at__gte=start_date)
            order_stats = orders.aggregate(
                total_orders=Count("id"),
                total_revenue=Sum("total"),
                avg_order_value=Avg("total"),
            )

            # Get category breakdown
            category_breakdown = {}
            for category in ["Star", "Plowhorse", "Puzzle", "Dog"]:
                count = MenuItem.objects.filter(
                    category=category, is_active=True
                ).count()
                category_breakdown[category] = count

            # Get top items
            top_items = list(
                MenuItem.objects.filter(is_active=True)
                .order_by("-total_purchases")[:5]
                .values_list("title", flat=True)
            )

            summary_data = {
                "period": period,
                "total_orders": order_stats["total_orders"] or 0,
                "total_revenue": float(order_stats["total_revenue"] or 0),
                "average_order_value": float(order_stats["avg_order_value"] or 0),
                "category_breakdown": category_breakdown,
                "top_items": top_items,
            }

        try:
            result = ml_service.generate_owner_report_sync(
                summary_data=summary_data, period=period
            )
            return Response(result)
        except MLServiceError as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


# ============ Recommendation Views ============


class RecommendationViewSet(viewsets.ViewSet):
    """
    ViewSet for AI-powered menu recommendations.

    Endpoints:
    - GET /recommendations/ - Get general recommendations
    - POST /recommendations/for-cart/ - Get recommendations based on cart items
    - GET /items/{id}/frequently-together/ - Get frequently bought together items
    """

    def get_permissions(self):
        # All recommendation endpoints are public (for customer use)
        return [AllowAny()]

    def get_authenticators(self):
        # Allow unauthenticated access for all recommendation endpoints
        return []

    def list(self, request):
        """
        Get general menu recommendations.

        Query Parameters:
        - limit: Number of recommendations (default 5, max 20)
        - strategy: Recommendation strategy (balanced, upsell, cross_sell)
        - section_id: Filter to specific section
        """
        from .recommendation_engine import recommendation_engine

        limit = min(int(request.query_params.get("limit", 5)), 20)
        strategy = request.query_params.get("strategy", "balanced")
        section_id = request.query_params.get("section_id")

        recommendations = recommendation_engine.get_recommendations(
            limit=limit,
            strategy=strategy,
            section_id=section_id,
        )

        # Serialize results
        results = []
        for rec in recommendations:
            results.append(
                {
                    "item": {
                        "id": rec.item.id,
                        "title": rec.item.title,
                        "price": rec.item.price,
                        "category": rec.item.category,
                        "section_name": (
                            rec.item.section.name if rec.item.section else None
                        ),
                    },
                    "score": rec.score,
                    "reason": rec.reason,
                    "category_score": rec.category_score,
                    "margin_score": rec.margin_score,
                    "copurchase_score": rec.copurchase_score,
                    "popularity_score": rec.popularity_score,
                    "context_score": rec.context_score,
                    "profit_impact": rec.profit_impact,
                }
            )

        return Response({"recommendations": results})

    @action(detail=False, methods=["post"], url_path="for-cart")
    def for_cart(self, request):
        """
        Get recommendations based on current cart items.

        Request Body:
        {
            "item_ids": ["uuid1", "uuid2", ...],
            "limit": 5,
            "strategy": "balanced"  // balanced, upsell, cross_sell
        }

        Returns recommendations with total potential margin increase.
        """
        from .recommendation_engine import recommendation_engine
        from .serializers import CartRecommendationRequestSerializer
        from decimal import Decimal

        serializer = CartRecommendationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        item_ids = serializer.validated_data.get("item_ids", [])
        limit = serializer.validated_data.get("limit", 5)
        strategy = serializer.validated_data.get("strategy", "balanced")

        recommendations = recommendation_engine.get_recommendations(
            current_items=item_ids,
            limit=limit,
            strategy=strategy,
        )

        # Calculate total potential margin
        total_margin = Decimal("0")
        results = []
        for rec in recommendations:
            if rec.profit_impact:
                total_margin += rec.profit_impact
            results.append(
                {
                    "item": {
                        "id": rec.item.id,
                        "title": rec.item.title,
                        "price": rec.item.price,
                        "category": rec.item.category,
                        "section_name": (
                            rec.item.section.name if rec.item.section else None
                        ),
                    },
                    "score": rec.score,
                    "reason": rec.reason,
                    "category_score": rec.category_score,
                    "margin_score": rec.margin_score,
                    "copurchase_score": rec.copurchase_score,
                    "popularity_score": rec.popularity_score,
                    "context_score": rec.context_score,
                    "profit_impact": rec.profit_impact,
                }
            )

        return Response(
            {
                "recommendations": results,
                "total_potential_margin": total_margin,
            }
        )


class FrequentlyBoughtTogetherView(APIView):
    """
    Get items frequently bought together with a specific item.

    GET /items/{item_id}/frequently-together/
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, item_id):
        """
        Get frequently bought together items for a menu item.

        Query Parameters:
        - limit: Number of associations to return (default 3, max 10)
        """
        from .recommendation_engine import recommendation_engine
        from .models import MenuItem

        limit = min(int(request.query_params.get("limit", 3)), 10)

        # Get the source item
        try:
            source_item = MenuItem.objects.get(id=item_id, is_active=True)
        except MenuItem.DoesNotExist:
            return Response(
                {"error": "Menu item not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Get frequently bought together
        associations = recommendation_engine.get_frequently_bought_together(
            item_id, limit=limit
        )

        # Format response
        fbt_items = []
        for assoc in associations:
            fbt_items.append(
                {
                    "item": {
                        "id": assoc.item.id,
                        "title": assoc.item.title,
                        "price": assoc.item.price,
                        "category": assoc.item.category,
                        "section_name": (
                            assoc.item.section.name if assoc.item.section else None
                        ),
                    },
                    "confidence": round(assoc.confidence, 3),
                    "lift": round(assoc.lift, 2),
                    "support": round(assoc.support, 4),
                    "order_count": assoc.order_count,
                    "message": assoc.message,
                }
            )

        return Response(
            {
                "source_item": {
                    "id": source_item.id,
                    "title": source_item.title,
                },
                "frequently_bought_together": fbt_items,
            }
        )
