from decimal import Decimal

from django import forms

from .models import Transaction


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ["payment_method", "amount_paid", "payment_reference", "notes"]
        widgets = {
            "amount_paid": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, order=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.order = order

    def clean(self):
        cleaned = super().clean()
        method = cleaned.get("payment_method")
        amount_paid = cleaned.get("amount_paid")
        if self.order is None:
            raise forms.ValidationError("Order tidak ditemukan.")
        if amount_paid is None:
            return cleaned
        if amount_paid < self.order.total_amount:
            self.add_error("amount_paid", "Pembayaran tidak mencukupi.")
        if method != "CASH" and amount_paid != self.order.total_amount:
            self.add_error("amount_paid", "Pembayaran non-tunai harus sama dengan total order.")
        if method != "CASH" and not cleaned.get("payment_reference"):
            self.add_error("payment_reference", "Referensi pembayaran wajib diisi.")
        return cleaned

    def save(self, commit=True, cashier=None):
        payment = super().save(commit=False)
        payment.order = self.order
        payment.cashier = cashier
        payment.amount_due = self.order.total_amount
        payment.change_amount = (
            payment.amount_paid - payment.amount_due
            if payment.payment_method == "CASH"
            else Decimal("0")
        )
        payment.status = "SUCCESS"
        if commit:
            payment.full_clean()
            payment.save()
        return payment
