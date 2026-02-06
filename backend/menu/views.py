"""
API Views for the Menu app with role-based permissions.

Permissions:
- Managers/Admins: Full access to menu management, analytics, AI analysis
- Staff: Can create orders, view menu
- Customers (unauthenticated): Can only view menu sections and items (read-only)
"""

from rest_framework import viewsets, status
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
from .permissions import (
    IsAdminOrManager,
    IsStaffOrAbove,
)


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
        description="Run AI analysis on a menu item. Managers only.",
    )
    @action(detail=True, methods=["post"])
    def analyze(self, request, pk=None):
        """
        Analyze a single menu item using the ML service.

        Returns category (Star/Plowhorse/Puzzle/Dog), confidence score, and recommendations.
        """
        item = self.get_object()

        try:
            # Call ML service
            result = ml_service.predict_sync(
                price=float(item.price),
                purchases=item.total_purchases,
                margin=float(item.margin),
                description_length=len(item.description) if item.description else 0,
            )

            # Update item with prediction
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
                }
            )

        except MLServiceError as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

    @extend_schema(description="Analyze all active menu items. Managers only.")
    @action(detail=False, methods=["post"])
    def bulk_analyze(self, request):
        """
        Analyze all active menu items using the ML service.
        """
        items = MenuItem.objects.filter(is_active=True)

        if not items.exists():
            return Response({"message": "No items to analyze"})

        # Prepare batch data
        batch_data = [
            {
                "price": float(item.price),
                "purchases": item.total_purchases,
                "margin": float(item.margin),
                "description_length": len(item.description) if item.description else 0,
            }
            for item in items
        ]

        try:
            predictions = ml_service.batch_predict_sync(batch_data)

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

        except MLServiceError as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

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
