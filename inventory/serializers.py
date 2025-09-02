from rest_framework import serializers
from .models import Inventory, Product

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "category"]

class InventorySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = Inventory
        fields = ["id", "product_name", "stock_level", "reorder_level", "unit_price", "last_updated"]
