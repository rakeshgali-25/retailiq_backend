from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.utils.timezone import now
from rest_framework.permissions import IsAuthenticated

from .models import Order
from .serializers import OrderSerializer


# ---------------------------
# 1. Summary
# ---------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sales_summary(request):
    total_sales = Order.objects.aggregate(total=Sum("order_value"))["total"] or 0

    top_product = (
        Order.objects.values("product__name")   # ✅ use relation
        .annotate(total_sales=Sum("order_value"))
        .order_by("-total_sales")
        .first()
    )

    current_month_sales = (
        Order.objects.filter(order_date__month=now().month)
        .aggregate(total=Sum("order_value"))["total"] or 0
    )
    prev_month_sales = (
        Order.objects.filter(order_date__month=now().month - 1)
        .aggregate(total=Sum("order_value"))["total"] or 0
    )

    growth = ((current_month_sales - prev_month_sales) / prev_month_sales * 100) if prev_month_sales > 0 else 0

    pending_orders = Order.objects.filter(status="Pending").count()

    data = {
        "total_sales": total_sales,
        "top_product": top_product,
        "growth_vs_prev": round(growth, 2),
        "pending_orders": pending_orders,
    }
    return Response(data)


# ---------------------------
# 2. Sales Trend
# ---------------------------
@api_view(['GET'])
def sales_trend(request):
    sales = (
        Order.objects
        .annotate(month=TruncMonth("order_date"))
        .values("month", "product__name")   # ✅ use relation
        .annotate(total_sales=Sum("order_value"))
        .order_by("month")
    )
    return Response(sales)


# ---------------------------
# 3. Sales by Product
# ---------------------------
@api_view(['GET'])
def sales_by_product(request):
    today = now().date()
    sales = (
        Order.objects
        .filter(order_date__year=today.year, order_date__month=today.month)
        .values("product__name")   # ✅ use relation
        .annotate(total_sales=Sum("order_value"))
        .order_by("-total_sales")
    )
    return Response(sales)


# ---------------------------
# 4. Recent Orders
# ---------------------------
@api_view(['GET'])
def recent_orders(request):
    orders = Order.objects.select_related("product", "vendor").order_by("-order_date")[:10]
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)


# ---------------------------
# 5. CRUD Operations for Orders
# ---------------------------
@api_view(['GET', 'POST'])
def order_list(request):
    if request.method == 'GET':
        qs = (
            Order.objects
            .select_related("product", "vendor")  # ✅ optimize FK fetch
            .order_by('-order_date', '-id')
        )
        serializer = OrderSerializer(qs, many=True)
        return Response(serializer.data)

    # POST (Create)
    serializer = OrderSerializer(data=request.data)
    if serializer.is_valid():
        obj = serializer.save()
        return Response(OrderSerializer(obj).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def order_detail(request, pk):
    try:
        order = (
            Order.objects
            .select_related("product", "vendor")
            .get(pk=pk)
        )
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(OrderSerializer(order).data)

    if request.method == 'PUT':
        serializer = OrderSerializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            obj = serializer.save()
            return Response(OrderSerializer(obj).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # DELETE
    order.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
