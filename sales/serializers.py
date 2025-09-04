# sales/serializers.py
from rest_framework import serializers
from django.db.models import Max
from .models import Order

class OrderSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    vendor_name  = serializers.CharField(source="vendor.name", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "order_id",
            "product", "vendor",
            "product_name", "vendor_name",
            "quantity", "order_value", "order_date", "status", "delay_minutes",
        ]
        read_only_fields = ["order_id", "product_name", "vendor_name"]
        extra_kwargs = {
            "delay_minutes": {"required": False},   # <-- make optional on input
        }

    def _next_order_id(self):
        # Safer than count(); handles deletions
        max_id = Order.objects.aggregate(m=Max("id"))["m"] or 0
        return f"ORD-{max_id + 1:03d}"

    def create(self, validated_data):
        # default delay_minutes if not provided
        validated_data.setdefault("delay_minutes", 0)

        # auto-generate order_id if missing
        if not validated_data.get("order_id"):
            validated_data["order_id"] = self._next_order_id()

        return super().create(validated_data)

    def update(self, instance, validated_data):
        # also default in update if API omits it
        if "delay_minutes" not in validated_data:
            validated_data["delay_minutes"] = instance.delay_minutes or 0
        return super().update(instance, validated_data)
