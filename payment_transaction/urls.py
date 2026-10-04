from django.urls import path

from . import views

app_name = "payment_transaction"

urlpatterns = [
    path("", views.transaction_list, name="list"),
    path("<int:pk>/", views.transaction_detail, name="detail"),
    path("<int:pk>/receipt/", views.transaction_receipt, name="receipt"),
    path("cart/", views.cart, name="cart"),
    path("cart/add/<int:product_id>/", views.cart_add, name="cart_add"),
    path("cart/increase/<int:product_id>/", views.cart_increase, name="cart_increase"),
    path("cart/decrease/<int:product_id>/", views.cart_decrease, name="cart_decrease"),
    path("cart/remove/<int:product_id>/", views.cart_remove, name="cart_remove"),
    path("checkout/", views.checkout, name="checkout"),
    path("orders/<int:order_id>/payment/", views.create_transaction, name="payment"),
]
