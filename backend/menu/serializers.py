"""
Serializers for the Menu app.
"""

from rest_framework import serializers
from .models import MenuSection, MenuItem, Order, OrderItem, CustomerActivity


# ============ Menu Section Serializers ============


class MenuSectionSerializer(serializers.ModelSerializer):
    """Serializer for MenuSection model"""

    items_count = serializers.SerializerMethodField()

    class Meta:
        model = MenuSection
        fields = [
            "id",
            "name",
            "description",
            "display_order",
            "is_active",
            "items_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "items_count"]

    def get_items_count(self, obj):
        return obj.items.filter(is_active=True).count()


class MenuSectionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating MenuSection"""

    class Meta:
        model = MenuSection
        fields = ["name", "description", "display_order", "is_active"]


# ============ Menu Item Serializers ============


class MenuItemListSerializer(serializers.ModelSerializer):
    """Serializer for listing menu items (lightweight)"""

    section_name = serializers.CharField(source="section.name", read_only=True)
    margin = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = MenuItem
        fields = [
            "id",
            "title",
            "price",
            "section",
            "section_name",
            "category",
            "ai_confidence",
            "is_active",
            "margin",
        ]


class MenuItemDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed menu item view"""

    section_name = serializers.CharField(source="section.name", read_only=True)
    margin = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    margin_percentage = serializers.FloatField(read_only=True)

    class Meta:
        model = MenuItem
        fields = [
            "id",
            "title",
            "description",
            "price",
            "cost",
            "section",
            "section_name",
            "display_order",
            "is_active",
            "category",
            "ai_confidence",
            "last_analyzed",
            "total_purchases",
            "total_revenue",
            "margin",
            "margin_percentage",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "category",
            "ai_confidence",
            "last_analyzed",
            "total_purchases",
            "total_revenue",
            "created_at",
            "updated_at",
        ]


class MenuItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating menu items"""

    class Meta:
        model = MenuItem
        fields = [
            "title",
            "description",
            "price",
            "cost",
            "section",
            "display_order",
            "is_active",
        ]

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value

    def validate_cost(self, value):
        if value < 0:
            raise serializers.ValidationError("Cost cannot be negative.")
        return value

    def validate(self, data):
        if data.get("cost") and data.get("price"):
            if data["cost"] >= data["price"]:
                raise serializers.ValidationError(
                    {"cost": "Cost should be less than price for positive margin."}
                )
        return data


class MenuItemAnalysisSerializer(serializers.Serializer):
    """Serializer for AI analysis response"""

    category = serializers.CharField()
    confidence = serializers.FloatField()
    recommendations = serializers.ListField(child=serializers.CharField())


# ============ Order Item Serializers ============


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order items"""

    menu_item_title = serializers.CharField(source="menu_item.title", read_only=True)
    line_total = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "menu_item",
            "menu_item_title",
            "quantity",
            "price_at_order",
            "line_total",
            "notes",
        ]
        read_only_fields = ["id", "line_total"]


class OrderItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating order items"""

    class Meta:
        model = OrderItem
        fields = ["menu_item", "quantity", "notes"]

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value


# ============ Order Serializers ============


class OrderListSerializer(serializers.ModelSerializer):
    """Serializer for listing orders"""

    created_by_name = serializers.SerializerMethodField()
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "status",
            "table_number",
            "total",
            "created_by",
            "created_by_name",
            "items_count",
            "created_at",
        ]

    def get_created_by_name(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}"
        return None

    def get_items_count(self, obj):
        return obj.items.count()


class OrderDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed order view"""

    items = OrderItemSerializer(many=True, read_only=True)
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "status",
            "table_number",
            "notes",
            "subtotal",
            "tax",
            "total",
            "created_by",
            "created_by_name",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "subtotal",
            "tax",
            "total",
            "created_at",
            "updated_at",
        ]

    def get_created_by_name(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}"
        return None


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating orders"""

    items = OrderItemCreateSerializer(many=True, write_only=True)

    class Meta:
        model = Order
        fields = ["table_number", "notes", "items"]

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        user = self.context["request"].user

        # Create order
        order = Order.objects.create(created_by=user, **validated_data)

        # Create order items
        for item_data in items_data:
            menu_item = item_data["menu_item"]
            OrderItem.objects.create(
                order=order,
                menu_item=menu_item,
                quantity=item_data["quantity"],
                price_at_order=menu_item.price,
                notes=item_data.get("notes", ""),
            )

            # Update menu item statistics
            menu_item.total_purchases += item_data["quantity"]
            menu_item.total_revenue += menu_item.price * item_data["quantity"]
            menu_item.save(update_fields=["total_purchases", "total_revenue"])

        # Calculate totals
        order.calculate_totals()

        return order


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating order status"""

    class Meta:
        model = Order
        fields = ["status"]


# ============ Customer Activity Serializers ============


class CustomerActivitySerializer(serializers.ModelSerializer):
    """Serializer for customer activity"""

    menu_item_title = serializers.CharField(source="menu_item.title", read_only=True)

    class Meta:
        model = CustomerActivity
        fields = [
            "id",
            "session_id",
            "event_type",
            "menu_item",
            "menu_item_title",
            "timestamp",
            "metadata",
        ]
        read_only_fields = ["id", "timestamp"]


class CustomerActivityCreateSerializer(serializers.ModelSerializer):
    """Serializer for logging customer activity"""

    class Meta:
        model = CustomerActivity
        fields = ["session_id", "event_type", "menu_item", "metadata"]
