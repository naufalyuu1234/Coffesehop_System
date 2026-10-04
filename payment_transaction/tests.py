from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from menu_product.models import Category, Product
from system_order.models import Order, OrderItem

from .models import Transaction


class TransactionFlowTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Minuman")
        self.product = Product.objects.create(category=category, name="Espresso", price=18000)
        self.order = Order.objects.create(customer_name="Naufal")
        OrderItem.objects.create(order=self.order, product=self.product, quantity=2, price=18000)

    def test_cash_payment_calculates_change_and_marks_order_paid(self):
        response = self.client.post(
            reverse("system_order:payment", args=[self.order.pk]),
            {"payment_method": "CASH", "amount_paid": "40000"},
        )
        self.assertEqual(response.status_code, 302)
        payment = Transaction.objects.get()
        self.assertEqual(payment.change_amount, Decimal("4000.00"))
        self.order.refresh_from_db()
        self.assertEqual(payment.status, "SUCCESS")
        self.assertEqual(self.order.status, "PAID")

    def test_insufficient_cash_is_rejected(self):
        response = self.client.post(
            reverse("system_order:payment", args=[self.order.pk]),
            {"payment_method": "CASH", "amount_paid": "10000"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Transaction.objects.exists())

    def test_paid_order_cannot_be_paid_twice(self):
        self.client.post(
            reverse("system_order:payment", args=[self.order.pk]),
            {"payment_method": "CASH", "amount_paid": "40000"},
        )
        response = self.client.post(
            reverse("system_order:payment", args=[self.order.pk]),
            {"payment_method": "CASH", "amount_paid": "40000"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Transaction.objects.count(), 1)

    def test_cart_checkout_uses_database_price_snapshot(self):
        self.client.post(reverse("payment_transaction:cart_add", args=[self.product.pk]))
        response = self.client.post(
            reverse("payment_transaction:checkout"),
            {"customer_name": "Sinta"},
        )
        self.assertEqual(response.status_code, 302)
        order = Order.objects.exclude(pk=self.order.pk).get()
        item = order.items.get()
        self.assertEqual(item.price, 18000)
        self.assertEqual(self.client.session.get("cart"), {})

    def test_unavailable_product_cannot_be_added(self):
        self.product.is_available = False
        self.product.save()
        response = self.client.post(reverse("payment_transaction:cart_add", args=[self.product.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(str(self.product.pk), self.client.session.get("cart", {}))
