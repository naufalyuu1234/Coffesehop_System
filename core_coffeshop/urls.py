from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('menu_product/', include('menu_product.urls')),
    path('orders/', include('system_order.urls')),
    path('', include('dashboard.urls'))
]
