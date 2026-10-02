from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum
from system_order.models import Order
    
def index(request):
    today = timezone.localdate()
    today_orders = Order.objects.filter(created_at__date=today)
    total_orders_today = today_orders.count()
    pending_orders_today = today_orders.filter(status='PENDING').count()
    revenue_aggregate = today_orders.filter( status__in=['PAID', 'COMPLETED'] ).aggregate(total=Sum('total_amount'))['total'] or 0
    formatted_revenue = f"{int(revenue_aggregate):,}".replace(",", ".")
    
    context = {
        'total_orders_today': total_orders_today,
        'pending_orders_today': pending_orders_today,
        'revenue_today': formatted_revenue,
        }
    return render(request, 'dashboard/index.html', context)