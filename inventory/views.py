from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Sum, Count
from .models import Inventory
from .serializers import InventorySerializer

# 1. Summary cards
@api_view(['GET'])
def inventory_summary(request):
    total_units = Inventory.objects.aggregate(total=Sum("stock_level"))["total"] or 0
    inventory_value = Inventory.objects.aggregate(value=Sum("stock_level" * 1))  # Fix below

    inventory_value = sum(item.stock_level * float(item.unit_price) for item in Inventory.objects.all())

    low_stock_count = Inventory.objects.filter(stock_level__lt=models.F("reorder_level")).count()
    total_products = Inventory.objects.count()
    low_stock_percent = (low_stock_count / total_products * 100) if total_products > 0 else 0

    # Stock coverage = total units / average daily usage (assume usage ~ reorder_level for simplicity)
    avg_reorder = Inventory.objects.aggregate(avg=Sum("reorder_level"))["avg"] or 1
    stock_coverage = int(total_units / avg_reorder) if avg_reorder > 0 else 0

    data = {
        "total_units": total_units,
        "inventory_value": inventory_value,
        "stock_coverage": stock_coverage,
        "low_stock_percent": round(low_stock_percent, 2),
    }
    return Response(data)

# 2. Stock vs Reorder Levels
@api_view(['GET'])
def stock_vs_reorder(request):
    data = Inventory.objects.values("product__name", "stock_level", "reorder_level")
    return Response(list(data))

# 3. Inventory Distribution (pie chart)
@api_view(['GET'])
def inventory_distribution(request):
    distribution = Inventory.objects.values("product__name").annotate(total_stock=Sum("stock_level"))
    return Response(list(distribution))

# 4. Stock Details (table)
@api_view(['GET'])
def stock_details(request):
    stocks = Inventory.objects.all()
    serializer = InventorySerializer(stocks, many=True)
    return Response(serializer.data)
