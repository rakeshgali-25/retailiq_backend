from django.urls import path
from . import views

urlpatterns = [
    path('summary/', views.dashboard_summary, name="dashboard-summary"),
    path('sales-over-time/', views.sales_over_time, name="sales-over-time"),
    path('inventory-levels/', views.inventory_levels, name="inventory-levels"),
    path('vendor-contribution/', views.vendor_contribution, name="vendor-contribution"),
]
