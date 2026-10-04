from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import resolve, reverse

from menu_product.models import Category, Product
from system_order.models import Order, OrderItem

from .models import Transaction
from .views import create_transaction


class TransactionRouteAndCartTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Minuman")
        self.product = Product.objects.create(category=category, name="Espresso", price=18000)

    def test_payment_url_uses_payment_transaction_namespace(self):
        url = reverse("payment_transaction:payment", args=[1])
        self.assertEqual(resolve(url).func, create_transaction)

    def test_cart_mutation_endpoints_post_only(self):
        self.assertEqual(self.client.get(reverse("payment_transaction:cart_add", args=[self.product.pk])).status_code, 405)
        self.assertEqual(self.client.get(reverse("payment_transaction:cart_increase", args=[self.product.pk])).status_code, 405)
        self.assertEqual(self.client.get(reverse("payment_transaction:cart_decrease", args=[self.product.pk])).status_code, 405)
        self.assertEqual(self.client.get(reverse("payment_transaction:cart_remove", args=[self.product.pk])).status_code, 405)

    def test_unavailable_product_cannot_be_added(self):
        self.product.is_available = False
        self.product.save()
        self.client.post(reverse("payment_transaction:cart_add", args=[self.product.pk]))
        self.assertNotIn(str(self.product.pk), self.client.session.get("cart", {}))

    def test_cart_quantity_never_below_one(self):
        self.client.post(reverse("payment_transaction:cart_add", args=[self.product.pk]))
        self.client.post(reverse("payment_transaction:cart_decrease", args=[self.product.pk]))
        self.assertEqual(self.client.session["cart"][str(self.product.pk)], 1)

    def test_checkout_uses_current_database_price_snapshot(self):
        self.client.post(reverse("payment_transaction:cart_add", args=[self.product.pk]))
        self.product.price = 20000
        self.product.save(update_fields=["price"])
        response = self.client.post(reverse("payment_transaction:checkout"), {"customer_name": "Sinta"})
        self.assertEqual(response.status_code, 302)
        order = Order.objects.latest("id")
        self.assertEqual(order.items.get().price, 20000)
        self.assertEqual(self.client.session.get("cart"), {})


class TransactionPaymentFlowTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Kopi")
        self.product = Product.objects.create(category=category, name="Latte", price=25000)
        self.order = Order.objects.create(customer_name="Naufal")
        OrderItem.objects.create(order=self.order, product=self.product, quantity=2, price=25000)

    def test_cash_payment_success_and_change(self):
        response = self.client.post(
            reverse("payment_transaction:payment", args=[self.order.pk]),
            {"payment_method": "CASH", "amount_paid": "60000"},
        )
        self.assertEqual(response.status_code, 302)
        payment = Transaction.objects.get()
        self.assertEqual(payment.change_amount, Decimal("10000.00"))
        self.assertEqual(payment.status, "SUCCESS")
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "PAID")

    def test_cash_insufficient_rejected(self):
        response = self.client.post(
            reverse("payment_transaction:payment", args=[self.order.pk]),
            {"payment_method": "CASH", "amount_paid": "20000"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pembayaran tidak mencukupi.")
        self.assertFalse(Transaction.objects.exists())
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "PENDING")

    def test_non_cash_requires_exact_amount_and_reference(self):
        response = self.client.post(
            reverse("payment_transaction:payment", args=[self.order.pk]),
            {"payment_method": "QRIS", "amount_paid": "50000"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Referensi pembayaran wajib diisi.")
        self.assertFalse(Transaction.objects.exists())

    def test_non_cash_success_has_zero_change(self):
        response = self.client.post(
            reverse("payment_transaction:payment", args=[self.order.pk]),
            {"payment_method": "TRANSFER", "amount_paid": "50000", "payment_reference": "TRF-123"},
        )
        self.assertEqual(response.status_code, 302)
        payment = Transaction.objects.get()
        self.assertEqual(payment.change_amount, Decimal("0.00"))
        self.assertEqual(payment.payment_reference, "TRF-123")

    def test_order_cannot_be_paid_twice(self):
        self.client.post(
            reverse("payment_transaction:payment", args=[self.order.pk]),
            {"payment_method": "CASH", "amount_paid": "50000"},
        )
        response = self.client.post(
            reverse("payment_transaction:payment", args=[self.order.pk]),
            {"payment_method": "CASH", "amount_paid": "50000"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Transaction.objects.filter(status="SUCCESS").count(), 1)

    def test_cancelled_order_cannot_be_paid(self):
        self.order.status = "CANCELLED"
        self.order.save(update_fields=["status"])
        response = self.client.post(
            reverse("payment_transaction:payment", args=[self.order.pk]),
            {"payment_method": "CASH", "amount_paid": "50000"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Transaction.objects.exists())

    def test_transaction_list_detail_and_receipt_render(self):
        payment = Transaction.objects.create(
            order=self.order,
            payment_method="CASH",
            amount_due=self.order.total_amount,
            amount_paid=self.order.total_amount,
            status="SUCCESS",
        )
        response = self.client.get(reverse("payment_transaction:list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "payment_transaction/transaction_list.html")
        self.assertContains(response, payment.transaction_code)

        detail_response = self.client.get(reverse("payment_transaction:detail", args=[payment.pk]))
        self.assertEqual(detail_response.status_code, 200)
        self.assertTemplateUsed(detail_response, "payment_transaction/transaction_detail.html")

        receipt_response = self.client.get(reverse("payment_transaction:receipt", args=[payment.pk]))
        self.assertEqual(receipt_response.status_code, 200)
        self.assertTemplateUsed(receipt_response, "payment_transaction/receipt.html")

    def test_model_non_cash_change_and_reference_validation(self):
        payment = Transaction(
            order=self.order,
            payment_method="DEBIT",
            amount_due=self.order.total_amount,
            amount_paid=self.order.total_amount + Decimal("1.00"),
            status="SUCCESS",
            payment_reference="",
        )
        with self.assertRaises(ValidationError):
            payment.full_clean()
