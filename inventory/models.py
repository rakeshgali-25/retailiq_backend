from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name

class Inventory(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="inventory")
    stock_level = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=0)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)  # For inventory value
    last_updated = models.DateTimeField(auto_now=True)

    def status(self):
        return "Low" if self.stock_level < self.reorder_level else "OK"

    def __str__(self):
        return f"{self.product.name} - {self.stock_level}"
