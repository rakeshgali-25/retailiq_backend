# sales/views.py
from datetime import date
from calendar import monthrange
from django.utils.timezone import now
from django.core.cache import cache

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import LimitOffsetPagination


from django.db.models import Sum
from django.db.models.functions import TruncMonth

from .models import Order
from .serializers import OrderSerializer
from rest_framework import generics, permissions
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from .models import Order
from .serializers import OrderSerializer




CACHE_TIMEOUT = 60  # seconds - adjust as needed


def _month_range_for(dt):
    """Return (month_start_date, next_month_start_date). dt is a date-like object."""
    month_start = dt.replace(day=1)
    if month_start.month == 12:
        next_month = month_start.replace(year=month_start.year + 1, month=1, day=1)
    else:
        next_month = month_start.replace(month=month_start.month + 1, day=1)
    return month_start, next_month



class OrdersLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 20  # change to desired default
    max_limit = 100

# /orders/ → GET (list), POST (create)
class OrderListAPIView(generics.ListCreateAPIView):
    queryset = Order.objects.select_related('product', 'vendor').order_by('-order_date', '-id')
    serializer_class = OrderSerializer
    permission_classes = (permissions.IsAuthenticated,)   # or remove if open
    pagination_class = OrdersLimitOffsetPagination


# /orders/<pk>/ → GET (retrieve), PUT/PATCH (update), DELETE
class OrderDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.select_related('product', 'vendor')
    serializer_class = OrderSerializer
    permission_classes = (permissions.IsAuthenticated,)
# ---------------------------
# 1. Summary
# ---------------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def sales_summary(request):
    """
    Aggregated dashboard numbers:
    - total sales
    - top product (name + total)
    - growth vs previous month (safe date arithmetic)
    - pending orders count
    Caches the computed result for CACHE_TIMEOUT seconds to reduce DB load.
    """
    cache_key = "sales_summary_v1"
    data = cache.get(cache_key)
    if data is not None:
        return Response(data)

    # total sales
    total_sales = Order.objects.aggregate(total=Sum("order_value"))["total"] or 0

    # top product (by order_value)
    top_product = (
        Order.objects.values("product__name")
        .annotate(total_sales=Sum("order_value"))
        .order_by("-total_sales")
        .first()
    )
    # top_product is a dict like {'product__name': 'X', 'total_sales': Decimal(...)}

    # current & previous month totals using date ranges (handles year boundaries)
    today = now().date()
    curr_start, next_start = _month_range_for(today)
    prev_start, _ = _month_range_for(curr_start.replace(day=1) - (today - curr_start))  # helper below doesn't break

    # simpler reliable prev month calculation:
    if curr_start.month == 1:
        prev_start = curr_start.replace(year=curr_start.year - 1, month=12, day=1)
    else:
        prev_start = curr_start.replace(month=curr_start.month - 1, day=1)

    curr_total = (
        Order.objects.filter(order_date__gte=curr_start, order_date__lt=next_start)
        .aggregate(total=Sum("order_value"))["total"] or 0
    )
    prev_next = curr_start  # previous month end is current month start
    prev_total = (
        Order.objects.filter(order_date__gte=prev_start, order_date__lt=prev_next)
        .aggregate(total=Sum("order_value"))["total"] or 0
    )

    growth = ( (curr_total - prev_total) / prev_total * 100 ) if prev_total else 0

    pending_orders = Order.objects.filter(status="Pending").count()

    data = {
        "total_sales": total_sales,
        "top_product": top_product,
        "current_month_sales": curr_total,
        "previous_month_sales": prev_total,
        "growth_vs_prev": round(growth, 2),
        "pending_orders": pending_orders,
    }

    cache.set(cache_key, data, CACHE_TIMEOUT)
    return Response(data)


# ---------------------------
# 2. Sales Trend
# ---------------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def sales_trend(request):
    """
    Returns monthly totals per product.
    Cached for short time to avoid repeated heavy aggregations.
    """
    cache_key = "sales_trend_v1"
    cached = cache.get(cache_key)
    if cached is not None:
        return Response(cached)

    qs = (
        Order.objects
        .annotate(month=TruncMonth("order_date"))
        .values("month", "product__name")
        .annotate(total_sales=Sum("order_value"))
        .order_by("month")
    )
    # convert QuerySet to list of dicts (month will be a date/datetime)
    result = [
        {"month": r["month"].date().isoformat() if hasattr(r["month"], "date") else r["month"].isoformat(),
         "product": r["product__name"],
         "total_sales": r["total_sales"]}
        for r in qs
    ]
    cache.set(cache_key, result, CACHE_TIMEOUT)
    return Response(result)


# ---------------------------
# 3. Sales by Product (current month)
# ---------------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def sales_by_product(request):
    cache_key = "sales_by_product_current_month_v1"
    cached = cache.get(cache_key)
    if cached is not None:
        return Response(cached)

    today = now().date()
    month_start, next_month_start = _month_range_for(today)

    qs = (
        Order.objects
        .filter(order_date__gte=month_start, order_date__lt=next_month_start)
        .values("product__name")
        .annotate(total_sales=Sum("order_value"))
        .order_by("-total_sales")
    )

    result = [{"product": r["product__name"], "total_sales": r["total_sales"]} for r in qs]
    cache.set(cache_key, result, CACHE_TIMEOUT)
    return Response(result)


# ---------------------------
# 4. Recent Orders
# ---------------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def recent_orders(request):
    """
    Returns the most recent 10 orders. Uses select_related to avoid N+1 on product/vendor.
    """
    orders = (
        Order.objects
        .select_related("product", "vendor")
        .only("id", "order_id", "order_date", "order_value", "status", "product_id", "vendor_id", "quantity", "delay_minutes")
        .order_by("-order_date", "-id")[:10]
    )
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)


# ---------------------------
# 5. CRUD Operations for Orders (list uses pagination)
# ---------------------------
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def order_list(request):
    if request.method == "GET":
        qs = (
            Order.objects
            .select_related("product", "vendor")
            .only("id", "order_id", "order_date", "order_value", "status", "product_id", "vendor_id", "quantity", "delay_minutes")
            .order_by("-order_date", "-id")
        )

        # pagination with DRF LimitOffsetPagination
        paginator = LimitOffsetPagination()
        paginated = paginator.paginate_queryset(qs, request, view=None)
        if paginated is not None:
            serializer = OrderSerializer(paginated, many=True)
            return paginator.get_paginated_response(serializer.data)
        serializer = OrderSerializer(paginated, many=True)
        return paginator.get_paginated_response(serializer.data)

    # POST (Create)
    serializer = OrderSerializer(data=request.data)
    if serializer.is_valid():
        obj = serializer.save()
        return Response(OrderSerializer(obj).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([IsAuthenticated])
def order_detail(request, pk):
    try:
        order = (
            Order.objects
            .select_related("product", "vendor")
            .only("id", "order_id", "order_date", "order_value", "status", "product_id", "vendor_id", "quantity", "delay_minutes")
            .get(pk=pk)
        )
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(OrderSerializer(order).data)

    if request.method == "PUT":
        serializer = OrderSerializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            obj = serializer.save()
            return Response(OrderSerializer(obj).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # DELETE
    order.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
