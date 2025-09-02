from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Sum, Avg
from django.db.models.functions import TruncMonth
from sales.models import Order

# 1. Summary KPIs
@api_view(['GET'])
def analytics_summary(request):
    total_sales = Order.objects.aggregate(total=Sum("order_value"))["total"] or 0

    # Top 2 products contribution
    product_sales = (
        Order.objects.values("product__name")
        .annotate(total_sales=Sum("order_value"))
        .order_by("-total_sales")
    )
    top2_sales = sum([p["total_sales"] for p in product_sales[:2]]) if product_sales else 0
    top2_contribution = (top2_sales / total_sales * 100) if total_sales > 0 else 0

    # On-time fulfillment (Completed orders without delay)
    completed_orders = Order.objects.filter(status="Completed")
    on_time_orders = completed_orders.filter(delay_minutes__lte=15).count()
    on_time_percent = (on_time_orders / completed_orders.count() * 100) if completed_orders.exists() else 0

    # Avg order value
    avg_order_value = Order.objects.aggregate(avg=Avg("order_value"))["avg"] or 0

    # Growth vs previous month
    if Order.objects.exists():
        latest_month = Order.objects.latest("order_date").order_date.month
        prev_month = latest_month - 1 if latest_month > 1 else 12

        current_sales = Order.objects.filter(order_date__month=latest_month).aggregate(total=Sum("order_value"))["total"] or 0
        prev_sales = Order.objects.filter(order_date__month=prev_month).aggregate(total=Sum("order_value"))["total"] or 0

        growth = ((current_sales - prev_sales) / prev_sales * 100) if prev_sales > 0 else 0
    else:
        growth = 0

    data = {
        "top2_contribution_percent": round(top2_contribution, 2),
        "on_time_fulfillment_percent": round(on_time_percent, 2),
        "avg_order_value": round(avg_order_value, 2),
        "growth_vs_prev": round(growth, 2),
    }
    return Response(data)

# 2. Sales Trend (month-wise total sales)
@api_view(['GET'])
def sales_trend(request):
    sales = (
        Order.objects
        .annotate(month=TruncMonth("order_date"))
        .values("month")
        .annotate(total_sales=Sum("order_value"))
        .order_by("month")
    )
    return Response(sales)

# 3. Product Contribution (pie chart)
@api_view(['GET'])
def product_contribution(request):
    contribution = (
        Order.objects.values("product__name")
        .annotate(total_sales=Sum("order_value"))
        .order_by("-total_sales")
    )
    return Response(contribution)

# 4. Vendor Delays by Product (bar chart)
@api_view(['GET'])
def vendor_delays_by_product(request):
    delays = (
        Order.objects
        .values("product__name")
        .annotate(avg_delay=Avg("delay_minutes"))
        .order_by("-avg_delay")
    )
    return Response(delays)

# 5. Insights (text generation from KPIs)
@api_view(['GET'])
def analytics_insights(request):
    total_sales = Order.objects.aggregate(total=Sum("order_value"))["total"] or 0
    product_sales = (
        Order.objects.values("product__name")
        .annotate(total_sales=Sum("order_value"))
        .order_by("-total_sales")
    )

    insights = []
    if product_sales:
        top_product = product_sales[0]
        percent = round((top_product["total_sales"] / total_sales * 100), 2) if total_sales > 0 else 0
        insights.append(f"{top_product['product__name']} contributed {percent}% of total sales.")

    completed_orders = Order.objects.filter(status="Completed")
    if completed_orders.exists():
        avg_delay = completed_orders.aggregate(avg=Avg("delay_minutes"))["avg"] or 0
        insights.append(f"Average delay across vendors is {round(avg_delay, 2)} minutes.")

    if not insights:
        insights.append("No sufficient data to generate insights.")

    return Response({"insights": insights})
