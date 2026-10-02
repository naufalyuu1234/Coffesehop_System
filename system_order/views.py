from django.shortcuts import render, get_object_or_404
from .models import Order

# Create your views here.
def order_list(request):
    orders = Order.objects.all().order_by('created_at')
    return render(request, 'orders/order-list.html', {'orders': orders})

def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    return render(request, 'orders/order-detail.html', {'orders': order})