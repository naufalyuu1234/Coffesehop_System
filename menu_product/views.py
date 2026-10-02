from django.shortcuts import render
from .models import Category,Product
from django.db.models import Prefetch

# Create your views here.
def product_list(request):
    categories = Category.objects.prefetch_related(
        Prefetch('products', queryset=Product.objects.filter(is_available=True))
    ).all()
    return render(request, 'menu_products/product_list.html', {
        'categories': categories
    })
