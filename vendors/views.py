
from .serializers import VendorSerializer

from django.db.models import Count,Sum, Avg, F, ExpressionWrapper, FloatField, Case, When, IntegerField
from django.db.models.functions import Cast
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Vendor
from sales.models import Order   # assuming orders are in sales app

@api_view(["GET"])
def vendor_details(request):
    vendors = Vendor.objects.all()

    vendor_data = []

    for v in vendors:
        # Orders for this vendor
        orders = Order.objects.filter(vendor=v)

        total_orders = orders.count()

        # On-time %
        on_time_count = orders.filter(delay_minutes__lte=15).count()  # <=15 mins = on-time
        on_time_percent = (on_time_count / total_orders * 100) if total_orders > 0 else 0

        # Avg delay (in hours)
        avg_delay = orders.aggregate(avg_delay=Avg("delay_minutes"))["avg_delay"] or 0
        avg_delay_hours = round(avg_delay / 60, 2) if avg_delay else 0

        # Products supplied (distinct product count)
        products_supplied = orders.values("product").distinct().count()

        vendor_data.append({
            "id": v.id,
            "vendor_name": v.name,
            "products_supplied": products_supplied,
            "on_time_percent": round(on_time_percent, 2),
            "avg_delay": avg_delay_hours,
            "total_orders": total_orders,
            "status": "Active" if total_orders > 0 else "Inactive",
        })

    return Response(vendor_data)



# 1. Summary
@api_view(['GET'])
def vendor_summary(request):
    total_vendors = Vendor.objects.count()
    total_orders = Order.objects.count()

    # Avg On-Time % = (Completed orders without delay) / total completed
    completed_orders = Order.objects.filter(status="Completed")
    on_time_orders = completed_orders.filter(delay_minutes__lte=15).count()  # example threshold 15 min
    avg_on_time = (on_time_orders / completed_orders.count() * 100) if completed_orders.exists() else 0

    # Avg delay
    avg_delay = completed_orders.aggregate(avg_delay=Avg("delay_minutes"))["avg_delay"] or 0

    pending_orders = Order.objects.filter(status="Pending").count()

    data = {
        "total_vendors": total_vendors,
        "avg_on_time_percent": round(avg_on_time, 2),
        "avg_delay_minutes": round(avg_delay, 2),
        "pending_orders": pending_orders,
    }
    return Response(data)

# 2. Vendor On-Time % (bar chart)
@api_view(['GET'])
def vendor_on_time(request):
    vendors = Vendor.objects.all()
    data = []
    for v in vendors:
        completed = Order.objects.filter(vendor=v, status="Completed")
        if completed.exists():
            on_time = completed.filter(delay_minutes__lte=15).count()
            on_time_percent = on_time / completed.count() * 100
        else:
            on_time_percent = 0
        data.append({"vendor": v.name, "on_time_percent": round(on_time_percent, 2)})
    return Response(data)

# 3. Vendor Supply Contribution (pie chart)
@api_view(['GET'])
def vendor_supply_contribution(request):
    contribution = (
        Order.objects.values("vendor__name")
        .annotate(total_supply=Sum("order_value"))
        .order_by("-total_supply")
    )
    return Response(contribution)

