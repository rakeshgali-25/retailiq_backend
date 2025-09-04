from django.urls import path
from . import views

urlpatterns = [
    path("summary/", views.inventory_summary, name="inventory-summary"),
    path("stock-vs-reorder/", views.stock_vs_reorder, name="stock-vs-reorder"),
    path("distribution/", views.inventory_distribution, name="inventory-distribution"),
    path("details/", views.stock_details, name="stock-details"),
    path("products/", views.product_list, name="product-list"),
]
