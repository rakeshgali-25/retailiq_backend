# sales/models.py
from django.db import models
from vendors.models import Vendor
from inventory.models import Product

class Order(models.Model):
    order_id = models.CharField(max_length=50)
    product  = models.ForeignKey(Product, on_delete=models.CASCADE)
    vendor   = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    order_value = models.DecimalField(max_digits=12, decimal_places=2)
    order_date = models.DateField()
    status = models.CharField(max_length=50)
    delay_minutes = models.IntegerField(null=True, blank=True)  # matches DB

    def __str__(self):
        return self.order_id
