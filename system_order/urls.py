from django.urls import path
from . import views

app_name = 'system_order'

urlpatterns = [
    path("", views.order_list, name='list'),
    path("<int:pk>/", views.order_detail, name='detail'),
]