from django.urls import path
from . import views
from payment_transaction.views import create_transaction

app_name = 'system_order'

urlpatterns = [
    path("", views.order_list, name='list'),
    path("<int:pk>/", views.order_detail, name='detail'),
    path("<int:order_id>/payment/", create_transaction, name="payment"),
]