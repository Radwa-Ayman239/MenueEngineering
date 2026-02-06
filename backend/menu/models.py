import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class MenuSection(models.Model):
    """Menu sections like 'Appetizers', 'Main Courses', 'Desserts', etc."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("Section Name"), max_length=255)
    description = models.TextField(_("Description"), blank=True)
    display_order = models.PositiveIntegerField(_("Display Order"), default=0)
    is_active = models.BooleanField(_("Is Active"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name = _("Menu Section")
        verbose_name_plural = _("Menu Sections")

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    """Individual menu items with AI-generated classification"""

    class CategoryChoices(models.TextChoices):
        STAR = "Star", _("Star")  # High popularity, high profit
        PLOWHORSE = "Plowhorse", _("Plowhorse")  # High popularity, low profit
        PUZZLE = "Puzzle", _("Puzzle")  # Low popularity, high profit
        DOG = "Dog", _("Dog")  # Low popularity, low profit

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


    # MODIFICATION: Added external_id to map to 'item_id' in your CSV
    external_id = models.IntegerField(
        _("External ID"), 
        unique=True, 
        null=True, 
        blank=True,
        help_text=_("The ID from the source CSV or POS system")
    )


    title = models.CharField(_("Title"), max_length=255)
    description = models.TextField(_("Description"), blank=True)
    price = models.DecimalField(_("Price"), max_digits=10, decimal_places=2)
    cost = models.DecimalField(
        _("Cost"),
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text=_("Actual cost to prepare this item"),
    )
    section = models.ForeignKey(
        MenuSection,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("Menu Section"),
    )
    display_order = models.PositiveIntegerField(_("Display Order"), default=0)
    is_active = models.BooleanField(_("Is Active"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # AI-generated fields
    category = models.CharField(
        _("Category"),
        max_length=20,
        choices=CategoryChoices.choices,
        blank=True,
        null=True,
        help_text=_("AI-generated menu engineering category"),
    )
    ai_confidence = models.FloatField(
        _("AI Confidence"),
        null=True,
        blank=True,
        help_text=_("Confidence score (0-1) of the AI prediction"),
    )
    last_analyzed = models.DateTimeField(
        _("Last Analyzed"),
        null=True,
        blank=True,
        help_text=_("When this item was last analyzed by the AI model"),
    )
    
    # Computed fields (updated periodically or on order)
    total_purchases = models.PositiveIntegerField(_("Total Purchases"), default=0)
    total_revenue = models.DecimalField(
        _("Total Revenue"), max_digits=12, decimal_places=2, default=0
    )
    total_profit = models.DecimalField(
        _("Total Profit"), max_digits=12, decimal_places=2, default=0
    )
    class Meta:
        ordering = ["section", "display_order", "title"]
        verbose_name = _("Menu Item")
        verbose_name_plural = _("Menu Items")

        # MODIFICATION: Added index for faster analysis queries
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['external_id']),
        ]

    def __str__(self):
        return f"{self.title} (${self.price})"
    

    @property
    def contribution_margin(self):
        """The actual dollar amount contributed to profit per unit sold"""
        return self.price - self.cost

    @property
    def margin(self):
        """Calculate profit margin"""
        return self.price - self.cost

    @property
    def margin_percentage(self):
        """Calculate profit margin as percentage"""
        if self.price == 0:
            return 0
        return ((self.price - self.cost) / self.price) * 100


class Order(models.Model):
    """Customer orders created by staff"""

    class StatusChoices(models.TextChoices):
        PENDING = "pending", _("Pending")
        CONFIRMED = "confirmed", _("Confirmed")
        PREPARING = "preparing", _("Preparing")
        READY = "ready", _("Ready")
        COMPLETED = "completed", _("Completed")
        CANCELLED = "cancelled", _("Cancelled")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_by = models.ForeignKey(
        "users.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        related_name="orders_created",
        verbose_name=_("Created By"),
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
    )
    table_number = models.CharField(
        _("Table Number"), max_length=20, blank=True, null=True
    )
    notes = models.TextField(_("Notes"), blank=True)
    subtotal = models.DecimalField(
        _("Subtotal"), max_digits=10, decimal_places=2, default=0
    )
    tax = models.DecimalField(_("Tax"), max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(_("Total"), max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")

    def __str__(self):
        return f"Order {self.id} - {self.status}"

    def calculate_totals(self):
        """Recalculate order totals from items"""
        self.subtotal = sum(item.line_total for item in self.items.all())
        self.tax = self.subtotal * 0
        self.total = self.subtotal + self.tax
        self.save(update_fields=["subtotal", "tax", "total"])


class OrderItem(models.Model):
    """Individual line items in an order"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items", verbose_name=_("Order")
    )
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.SET_NULL,
        null=True,  # Required when using SET_NULL
        related_name="order_items",
        verbose_name=_("Menu Item"),
    )
    quantity = models.PositiveIntegerField(_("Quantity"), default=1)
    price_at_order = models.DecimalField(
        _("Price at Order"),
        max_digits=10,
        decimal_places=2,
        help_text=_("Price captured at time of order"),
    )
    notes = models.CharField(_("Notes"), max_length=255, blank=True)

    class Meta:
        verbose_name = _("Order Item")
        verbose_name_plural = _("Order Items")

    def __str__(self):
        item_name = self.menu_item.title if self.menu_item else "Deleted Item"
        return f"{self.quantity}x {item_name}"

    @property
    def line_total(self):
        """Calculate line item total"""
        return self.quantity * self.price_at_order


class CustomerActivity(models.Model):
    """Track customer interactions for ML model updates and analytics"""

    class EventType(models.TextChoices):
        VIEW = "view", _("View")
        CLICK = "click", _("Click")
        ADD_TO_CART = "add_to_cart", _("Add to Cart")
        REMOVE_FROM_CART = "remove_from_cart", _("Remove from Cart")
        PURCHASE = "purchase", _("Purchase")
        RATING = "rating", _("Rating")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_id = models.CharField(
        _("Session ID"),
        max_length=255,
        db_index=True,
        help_text=_("Anonymous session identifier"),
    )
    event_type = models.CharField(
        _("Event Type"), max_length=50, choices=EventType.choices
    )
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activities",
        verbose_name=_("Menu Item"),
    )
    timestamp = models.DateTimeField(_("Timestamp"), auto_now_add=True, db_index=True)
    metadata = models.JSONField(
        _("Metadata"),
        default=dict,
        blank=True,
        help_text=_("Additional event data (e.g., rating value, duration)"),
    )

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = _("Customer Activity")
        verbose_name_plural = _("Customer Activities")
        indexes = [
            models.Index(fields=["session_id", "timestamp"]),
            models.Index(fields=["event_type", "timestamp"]),
        ]

    def __str__(self):
        item_name = self.menu_item.title if self.menu_item else "No item"
        return f"{self.event_type} - {item_name} ({self.timestamp})"
