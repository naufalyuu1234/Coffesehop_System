from django.db import models
from menu_product.models import Product

# order models
class Order(models.Model):
    customer_name = models.CharField(max_length=100)
    # Data Pemilihan Status
    STATUS_CHOICES = [
        ("PENDING", "pending"),
        ("PAID", "paid"),
        ("COMPLETED", "completed"),
        ("CANCELLED", "cancelled")
    ]
    status = models.CharField(
        max_length=20,
        default="PENDING",
        choices=STATUS_CHOICES,
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - {self.customer_name}"

    def update_total_amount(self):
        total = sum(item.quantity * item.price for item in self.items.all() if item.price)
        self.total_amount = total
        self.save(update_fields=['total_amount'])

    def mark_as_paid(self):
        if self.status != "PENDING":
            raise ValueError("Order ini tidak dapat dibayar.")
        self.status = "PAID"
        self.save(update_fields=["status", "updated_at"])

    def mark_as_completed(self):
        if self.status != "PAID":
            raise ValueError("Hanya order PAID yang dapat diselesaikan.")
        self.status = "COMPLETED"
        self.save(update_fields=["status", "updated_at"])

    @property
    def formatted_total(self):
        return f"{int(self.total_amount):,}".replace(",", ".")

#OrderItems Model
class OrderItem(models.Model):
    order = models.ForeignKey(
        'system_order.Order',
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'menu_product.Product',
        on_delete=models.PROTECT,
        related_name='order_items'
    )
    quantity = models.PositiveIntegerField(default=1)
    price = models.PositiveIntegerField(editable=False)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    def save(self, *args, **kwargs):
        if self.price is None and self.product:
            self.price = self.product.price
        super().save(*args, **kwargs)
        # Update total harga setelah di save
        if hasattr(self.order, 'update_total_amount'):
            self.order.update_total_amount()

    def delete(self, *args, **kwargs):
        order = self.order
        super().delete(*args, **kwargs)
        if hasattr(order, 'update_total_amount'):
            order.update_total_amount()