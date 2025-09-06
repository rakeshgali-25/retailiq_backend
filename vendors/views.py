
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
        orders = Order.objects.filter(vendor=v)
        total_orders = orders.count()

        # Products supplied
        products_supplied = orders.values("product").distinct().count()

        vendor_data.append({
            "id": v.id,
            "vendor_name": v.name,
            "products_supplied": products_supplied,
            "on_time_percent": v.on_time_percent,  
            "avg_delay": v.avg_delay_hours,         # placeholder
            "total_orders": total_orders,
            "status": "Active" if total_orders > 0 else "Inactive",
        })

    return Response(vendor_data)


@api_view(['GET'])
# @permission_classes([IsAuthenticated])   # enable if you want auth
def vendor_summary(request):
    """
    Return dashboard summary:
      - total_vendors: total count of vendor rows
      - avg_on_time_percent: average of vendor.on_time_percent (0-100)
      - avg_delay_minutes: average vendor.avg_delay_hours converted to minutes
      - pending_orders: count of orders with status 'Pending'
    """
    total_vendors = Vendor.objects.count()
    pending_orders = Order.objects.filter(status="Pending").count()

    # Use DB aggregation to compute averages (fast)
    agg = Vendor.objects.aggregate(
        avg_on_time=Avg('on_time_percent'),
        avg_delay_hours=Avg('avg_delay_hours'),
    )

    # aggregate values may be None when there are no vendors / values
    avg_on_time = agg.get('avg_on_time') or 0.0
    avg_delay_hours = agg.get('avg_delay_hours') or 0.0

    # convert avg_delay_hours to minutes (float) and round nicely
    avg_delay_minutes = float(avg_delay_hours) * 60.0

    data = {
        "total_vendors": total_vendors,
        # round to 2 decimals for neat frontend display
        "avg_on_time_percent": round(float(avg_on_time), 2),
        "avg_delay_minutes": round(avg_delay_minutes, 2),
        "pending_orders": pending_orders,
    }
    return Response(data)


@api_view(['GET'])
def vendor_on_time(request):
    vendors = Vendor.objects.all()
    data = [{"vendor": v.name, "on_time_percent": v.on_time_percent} for v in vendors]
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

# GET /vendors/
@api_view(['GET'])
def vendor_list(request):
    vendors = Vendor.objects.all().values("id", "name")
    return Response(list(vendors))