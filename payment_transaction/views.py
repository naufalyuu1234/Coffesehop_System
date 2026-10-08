from decimal import Decimal

from django.contrib import messages
from django.db import transaction as db_transaction
from django.db.models import Q
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.contrib.auth.decorators import login_required

from menu_product.models import Product
from system_order.models import Order, OrderItem

from .forms import PaymentForm
from .models import Transaction


def _cart(request):
    return request.session.setdefault("cart", {})


def _cart_items(request):
    products = Product.objects.filter(pk__in=_cart(request), is_available=True)
    items = []
    total = Decimal("0")
    for product in products:
        quantity = int(_cart(request).get(str(product.pk), 0))
        subtotal = product.price * quantity
        items.append({"product": product, "quantity": quantity, "subtotal": subtotal})
        total += subtotal
    return items, total


def cart(request):
    items, total = _cart_items(request)
    return render(request, "payment_transaction/cart.html", {"items": items, "total": total})


def cart_add(request, product_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    product = get_object_or_404(Product, pk=product_id)
    if not product.is_available:
        messages.error(request, f"Produk {product.name} sudah tidak tersedia.")
        return redirect("payment_transaction:cart")
    current = _cart(request)
    key = str(product.pk)
    current[key] = int(current.get(key, 0)) + 1
    request.session.modified = True
    return redirect("payment_transaction:cart")


def _change_quantity(request, product_id, delta):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    key = str(product_id)
    current = _cart(request)
    if key in current:
        current[key] = max(1, int(current[key]) + delta)
        request.session.modified = True
    return redirect("payment_transaction:cart")


def cart_increase(request, product_id):
    return _change_quantity(request, product_id, 1)


def cart_decrease(request, product_id):
    return _change_quantity(request, product_id, -1)


def cart_remove(request, product_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    _cart(request).pop(str(product_id), None)
    request.session.modified = True
    return redirect("payment_transaction:cart")


def checkout(request):
    if request.method == "GET":
        items, total = _cart_items(request)
        return render(request, "payment_transaction/checkout.html", {"items": items, "total": total})
    if request.method != "POST":
        return HttpResponseNotAllowed(["GET", "POST"])
    cart_data = dict(_cart(request))
    if not cart_data:
        messages.error(request, "Keranjang masih kosong.")
        return redirect("payment_transaction:cart")
    try:
        with db_transaction.atomic():
            products = list(Product.objects.select_for_update().filter(pk__in=cart_data))
            if len(products) != len(cart_data) or any(not product.is_available for product in products):
                raise ValueError("Salah satu produk sudah tidak tersedia.")
            order = Order.objects.create(customer_name=request.POST.get("customer_name", "").strip() or "Pelanggan")
            for product in products:
                OrderItem.objects.create(order=order, product=product, quantity=int(cart_data[str(product.pk)]), price=product.price)
        request.session["cart"] = {}
        request.session.modified = True
    except (ValueError, TypeError):
        messages.error(request, "Checkout gagal. Periksa kembali ketersediaan produk.")
        return redirect("payment_transaction:cart")
    return redirect("payment_transaction:payment", order_id=order.pk)


def create_transaction(request, order_id):
    if request.method not in ("GET", "POST"):
        return HttpResponseNotAllowed(["GET", "POST"])
    if request.method == "GET":
        order = get_object_or_404(Order, pk=order_id)
        if order.status != "PENDING":
            messages.error(request, "Order ini tidak bisa dibayar lagi.")
            return redirect("system_order:detail", pk=order.pk)
        return render(request, "payment_transaction/payment_form.html", {"order": order, "form": PaymentForm(order=order)})
    with db_transaction.atomic():
        order = get_object_or_404(Order.objects.select_for_update(), pk=order_id)
        if (
            order.status != "PENDING"
            or not order.items.exists()
            or Transaction.objects.select_for_update().filter(order=order, status="SUCCESS").exists()
        ):
            messages.error(request, "Order ini sudah dibayar atau tidak dapat diproses.")
            return redirect("system_order:detail", pk=order.pk)
        form = PaymentForm(request.POST, order=order)
        if form.is_valid():
            payment = form.save(cashier=request.user if request.user.is_authenticated else None)
            order.mark_as_paid()
            messages.success(request, "Transaksi berhasil.")
            return redirect("payment_transaction:detail", pk=payment.pk)
    return render(request, "payment_transaction/payment_form.html", {"order": order, "form": form})


def transaction_list(request):
    queryset = Transaction.objects.select_related("order", "cashier")
    status = request.GET.get("status")
    method = request.GET.get("payment_method")
    search = request.GET.get("q")
    date = request.GET.get("date")
    if status:
        queryset = queryset.filter(status=status)
    if method:
        queryset = queryset.filter(payment_method=method)
    if search:
        queryset = queryset.filter(Q(transaction_code__icontains=search) | Q(order__customer_name__icontains=search))
    if date:
        queryset = queryset.filter(created_at__date=date)
    context = {
        "transactions": queryset,
        "status_choices": Transaction.STATUS_CHOICES,
        "payment_method_choices": Transaction.PAYMENT_METHOD_CHOICES,
        "filters": {"status": status or "", "payment_method": method or "", "q": search or "", "date": date or ""},
    }
    return render(request, "payment_transaction/transaction_list.html", context)


def transaction_detail(request, pk):
    payment = get_object_or_404(Transaction.objects.select_related("order", "cashier"), pk=pk)
    return render(request, "payment_transaction/transaction_detail.html", {"transaction": payment})


def transaction_receipt(request, pk):
    payment = get_object_or_404(Transaction.objects.select_related("order", "cashier"), pk=pk)
    return render(request, "payment_transaction/receipt.html", {"transaction": payment})

