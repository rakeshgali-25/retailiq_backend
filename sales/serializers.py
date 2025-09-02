from rest_framework import serializers
from .models import Order

class OrderSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    vendor_name = serializers.CharField(source="vendor.name", read_only=True)

    class Meta:
        model = Order
        fields = [
            "order_id", "product_name", "vendor_name",
            "quantity", "order_value", "order_date", "status"
        ]
