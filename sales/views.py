from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from .models import Order
from .serializers import OrderSerializer
from inventory.models import Product

# 1. Summary (Total Sales, Top Product, Growth %, Pending Orders)
@api_view(['GET'])
def sales_summary(request):
    total_sales = Order.objects.aggregate(total=Sum("order_value"))["total"] or 0

    # Top product by sales
    top_product = (
        Order.objects.values("product__name")
        .annotate(total_sales=Sum("order_value"))
        .order_by("-total_sales")
        .first()
    )

    # Growth = (this_month - prev_month) / prev_month
    current_month_sales = (
        Order.objects.filter(order_date__month=5)  # Example: May
        .aggregate(total=Sum("order_value"))["total"] or 0
    )
    prev_month_sales = (
        Order.objects.filter(order_date__month=4)  # Example: April
        .aggregate(total=Sum("order_value"))["total"] or 0
    )
    growth = (
        ((current_month_sales - prev_month_sales) / prev_month_sales * 100)
        if prev_month_sales > 0 else 0
    )

    pending_orders = Order.objects.filter(status="Pending").count()

    data = {
        "total_sales": total_sales,
        "top_product": top_product,
        "growth_vs_prev": round(growth, 2),
        "pending_orders": pending_orders,
    }
    return Response(data)

# 2. Sales Trend (line chart by month & product)
@api_view(['GET'])
def sales_trend(request):
    sales = (
        Order.objects
        .annotate(month=TruncMonth("order_date"))
        .values("month", "product__name")
        .annotate(total_sales=Sum("order_value"))
        .order_by("month")
    )
    return Response(sales)

# 3. Sales by Product (bar chart - latest month)
@api_view(['GET'])
def sales_by_product(request):
    latest_month = Order.objects.latest("order_date").order_date.month
    sales = (
        Order.objects.filter(order_date__month=latest_month)
        .values("product__name")
        .annotate(total_sales=Sum("order_value"))
        .order_by("-total_sales")
    )
    return Response(sales)

# 4. Recent Orders (table)
@api_view(['GET'])
def recent_orders(request):
    orders = Order.objects.order_by("-order_date")[:10]
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)
