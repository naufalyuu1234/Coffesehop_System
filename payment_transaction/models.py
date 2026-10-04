from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Transaction(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ("CASH", "Cash"),
        ("QRIS", "QRIS"),
        ("DEBIT", "Debit"),
        ("CREDIT", "Credit"),
        ("TRANSFER", "Transfer"),
    ]
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
        ("CANCELLED", "Cancelled"),
        ("REFUNDED", "Refunded"),
    ]

    transaction_code = models.CharField(max_length=30, unique=True, editable=False)
    order = models.ForeignKey("system_order.Order", on_delete=models.PROTECT, related_name="transactions")
    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="coffee_transactions",
    )
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES)
    amount_due = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    change_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")
    payment_reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.transaction_code

    def save(self, *args, **kwargs):
        if not self.transaction_code:
            stamp = timezone.localdate().strftime("%Y%m%d")
            prefix = f"TRX-{stamp}-"
            last = type(self).objects.filter(transaction_code__startswith=prefix).order_by("-transaction_code").first()
            sequence = int(last.transaction_code.rsplit("-", 1)[-1]) + 1 if last else 1
            self.transaction_code = f"{prefix}{sequence:04d}"
        super().save(*args, **kwargs)

    def clean(self):
        if self.order_id:
            if self.order.status != "PENDING" and self.status == "SUCCESS":
                raise ValidationError("Order ini sudah tidak dapat dibayar.")
            if not self.order.items.exists():
                raise ValidationError("Order harus memiliki minimal satu item.")
            if self.order.transactions.filter(status="SUCCESS").exclude(pk=self.pk).exists():
                raise ValidationError("Order ini sudah memiliki transaksi sukses.")
            if self.amount_due != self.order.total_amount:
                raise ValidationError("Nominal tagihan tidak sesuai dengan total order.")
        if self.amount_due is None or self.amount_paid is None:
            return
        if self.amount_due < 0 or self.amount_paid < 0:
            raise ValidationError("Nominal pembayaran tidak boleh negatif.")
        if self.amount_paid < self.amount_due:
            raise ValidationError("Pembayaran tidak mencukupi.")
        self.change_amount = (
            self.amount_paid - self.amount_due if self.payment_method == "CASH" else Decimal("0")
        )
        if self.status == "SUCCESS" and not self.paid_at:
            self.paid_at = timezone.now()
