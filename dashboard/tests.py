from django.test import TestCase
from django.urls import reverse

from menu_product.models import Category, Product
from payment_transaction.models import Transaction
from system_order.models import Order, OrderItem


class DashboardRevenueTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Minuman")
        product = Product.objects.create(category=category, name="Americano", price=15000)
        self.order = Order.objects.create(customer_name="A")
        OrderItem.objects.create(order=self.order, product=product, quantity=2, price=15000)

    def test_dashboard_revenue_counts_success_transaction_only(self):
        Transaction.objects.create(
            order=self.order,
            payment_method="CASH",
            amount_due=self.order.total_amount,
            amount_paid=self.order.total_amount,
            status="FAILED",
        )
        Transaction.objects.create(
            order=self.order,
            payment_method="CASH",
            amount_due=self.order.total_amount,
            amount_paid=self.order.total_amount,
            status="SUCCESS",
        )
        response = self.client.get(reverse("dashboard:index"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["successful_transactions_today"], 1)
        self.assertEqual(response.context["revenue_today"], "30.000")
