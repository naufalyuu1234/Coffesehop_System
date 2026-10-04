from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum
from system_order.models import Order
from payment_transaction.models import Transaction
    
def index(request):
    today = timezone.localdate()
    today_orders = Order.objects.filter(created_at__date=today)
    total_orders_today = today_orders.count()
    pending_orders_today = today_orders.filter(status='PENDING').count()
    successful_transactions = Transaction.objects.filter(status='SUCCESS', created_at__date=today)
    revenue_aggregate = successful_transactions.aggregate(total=Sum('amount_due'))['total'] or 0
    formatted_revenue = f"{int(revenue_aggregate):,}".replace(",", ".")
    
    context = {
        'total_orders_today': total_orders_today,
        'pending_orders_today': pending_orders_today,
        'revenue_today': formatted_revenue,
        'successful_transactions_today': successful_transactions.count(),
        'cash_revenue_today': successful_transactions.filter(payment_method='CASH').aggregate(total=Sum('amount_due'))['total'] or 0,
        'qris_revenue_today': successful_transactions.filter(payment_method='QRIS').aggregate(total=Sum('amount_due'))['total'] or 0,
        'debit_revenue_today': successful_transactions.filter(payment_method='DEBIT').aggregate(total=Sum('amount_due'))['total'] or 0,
        'transfer_revenue_today': successful_transactions.filter(payment_method='TRANSFER').aggregate(total=Sum('amount_due'))['total'] or 0,
        }
    return render(request, 'dashboard/index.html', context)