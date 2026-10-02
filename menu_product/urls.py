from django.urls import path
from . import views

app_name = 'menu_product'

urlpatterns = [
    path('product/', views.product_list, name='menu')
]