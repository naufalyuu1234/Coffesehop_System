from django.contrib import admin

from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("transaction_code", "order", "payment_method", "amount_due", "amount_paid", "status", "cashier", "created_at")
    list_filter = ("status", "payment_method", "created_at")
    search_fields = ("transaction_code", "order__customer_name", "payment_reference")
    readonly_fields = (
        "transaction_code", "order", "cashier", "amount_due", "amount_paid",
        "change_amount", "status", "paid_at", "created_at", "updated_at",
    )
