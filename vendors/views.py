
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
            "on_time_percent": 0,   # placeholder
            "avg_delay": 0,         # placeholder
            "total_orders": total_orders,
            "status": "Active" if total_orders > 0 else "Inactive",
        })

    return Response(vendor_data)


@api_view(['GET'])
def vendor_summary(request):
    total_vendors = Vendor.objects.count()
    pending_orders = Order.objects.filter(status="Pending").count()

    data = {
        "total_vendors": total_vendors,
        "avg_on_time_percent": 0,
        "avg_delay_minutes": 0,
        "pending_orders": pending_orders,
    }
    return Response(data)


@api_view(['GET'])
def vendor_on_time(request):
    vendors = Vendor.objects.all()
    data = [{"vendor": v.name, "on_time_percent": 0} for v in vendors]
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