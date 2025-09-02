from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Sum, Count
from sales.models import Order
from inventory.models import Inventory
from vendors.models import Vendor
from django.db.models.functions import TruncMonth

# Summary: total sales, active vendors, pending orders
@api_view(['GET'])
def dashboard_summary(request):
    total_sales = Order.objects.aggregate(total=Sum('order_value'))['total'] or 0
    active_vendors = Vendor.objects.count()
    pending_orders = Order.objects.filter(status='Pending').count()

    data = {
        "total_sales": total_sales,
        "active_vendors": active_vendors,
        "pending_orders": pending_orders
    }
    return Response(data)

# Sales over time (monthly trend)
@api_view(['GET'])
def sales_over_time(request):
    sales = (
        Order.objects
        .annotate(month=TruncMonth('order_date'))
        .values('month')
        .annotate(total_sales=Sum('order_value'))
        .order_by('month')
    )
    return Response(sales)

# Inventory levels (sum by category)
@api_view(['GET'])
def inventory_levels(request):
    data = (
        Inventory.objects
        .values('product__category')  # <-- follow relation to Product
        .annotate(total_stock=Sum('stock_level'))
        .order_by('product__category')
    )
    return Response(data)       

# Vendor contribution (sales by vendor)
@api_view(['GET'])
def vendor_contribution(request):
    contribution = (
        Order.objects
        .values('vendor__name')
        .annotate(total_sales=Sum('order_value'))
        .order_by('-total_sales')
    )
    return Response(contribution)
