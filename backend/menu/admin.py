from django.contrib import admin
from .models import MenuSection, MenuItem, Order, OrderItem, CustomerActivity


@admin.register(MenuSection)
class MenuSectionAdmin(admin.ModelAdmin):
    list_display = ("name", "display_order", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    ordering = ("display_order", "name")


# @admin.register(MenuItem)
# class MenuItemAdmin(admin.ModelAdmin):
#     list_display = (
#         #"external_id",
#         "title",
#         "section",
#         "price",
#         "cost",
#         "margin_display",
#         #"category",
#         "total_revenue", # Added
#         "total_profit",  # Added
#         "ai_confidence_display",
#         "is_active",
#     )
#     list_filter = ("section", "category", "is_active")
#     search_fields = ("title", "description")
#     ordering = ("section", "display_order", "title")
#     readonly_fields = (
#         "external_id",
#         "category",
#         "ai_confidence",
#         "last_analyzed",
#         "total_purchases",
#         "total_revenue",
#         "total_profit", # Added
#     )

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    # These are the fields populated by your CSV
    list_display = (
        "title",
        "category",
        "price",
        "total_purchases",
        "total_revenue",
        "total_profit",
    )
    
    # CRITICAL: Pagination and performance for 87k items
    list_per_page = 50
    show_full_result_count = False 
    
    # Filter by the categories found in your CSV (Star, Dog, etc.)
    list_filter = ("category", "is_active")
    search_fields = ("title", "external_id")
    
    # Standardize ordering to prevent database strain
    ordering = ("title",)

    # Make imported stats viewable but not editable
    readonly_fields = (
        "category",
        "total_purchases",
        "total_revenue",
        "total_profit",
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "description",
                    "section",
                    "display_order",
                    "is_active",
                )
            },
        ),
        ("Pricing", {"fields": ("price", "cost")}),
        (
            "AI Analysis",
            {
                "fields": ("category", "ai_confidence", "last_analyzed"),
                "classes": ("collapse",),
            },
        ),
        (
            "Statistics",
            {"fields": ("total_purchases", "total_revenue"), "classes": ("collapse",)},
        ),
    )

    @admin.display(description="Margin")
    def margin_display(self, obj):
        return f"${obj.margin:.2f}"

    @admin.display(description="AI Confidence")
    def ai_confidence_display(self, obj):
        if obj.ai_confidence:
            return f"{obj.ai_confidence * 100:.1f}%"
        return "-"


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("price_at_order", "line_total_display")

    @admin.display(description="Line Total")
    def line_total_display(self, obj):
        return f"${obj.line_total:.2f}"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "table_number", "total", "created_by", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("id", "table_number", "notes")
    ordering = ("-created_at",)
    readonly_fields = ("subtotal", "tax", "total", "created_at", "updated_at")
    inlines = [OrderItemInline]

    fieldsets = (
        (None, {"fields": ("status", "table_number", "created_by", "notes")}),
        ("Totals", {"fields": ("subtotal", "tax", "total")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(CustomerActivity)
class CustomerActivityAdmin(admin.ModelAdmin):
    list_display = ("event_type", "menu_item", "session_id", "timestamp")
    list_filter = ("event_type", "timestamp")
    search_fields = ("session_id", "menu_item__title")
    ordering = ("-timestamp",)
    readonly_fields = ("session_id", "event_type", "menu_item", "timestamp", "metadata")
