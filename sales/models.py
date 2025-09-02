from django.db import models
from vendors.models import Vendor
from inventory.models import Product

class Order(models.Model):
    order_id = models.CharField(max_length=50, unique=True)
    product = models.ForeignKey("inventory.Product", on_delete=models.CASCADE)
    vendor = models.ForeignKey("vendors.Vendor", on_delete=models.CASCADE)
    quantity = models.IntegerField()
    order_value = models.DecimalField(max_digits=12, decimal_places=2)
    order_date = models.DateField()
    status = models.CharField(max_length=20, choices=[("Completed", "Completed"), ("Pending", "Pending"),('Cancelled', 'Cancelled')])
    delay_minutes = models.IntegerField(default=0)   # <-- add this line

    def __str__(self):
        return self.order_id

