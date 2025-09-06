# sales/models.py
from django.db import models
from vendors.models import Vendor
from inventory.models import Product

# sales/models.py (patch)
class Order(models.Model):
    order_id = models.CharField(max_length=50)
    product  = models.ForeignKey(Product, on_delete=models.CASCADE)
    vendor   = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    order_value = models.DecimalField(max_digits=12, decimal_places=2)
    order_date = models.DateField(db_index=True)        # << added index
    status = models.CharField(max_length=50, db_index=True)  # << added index
    delay_minutes = models.IntegerField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["-order_date", "id"], name="order_date_id_idx"),
        ]

