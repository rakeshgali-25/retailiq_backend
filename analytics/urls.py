from django.urls import path
from . import views

urlpatterns = [
    path("summary/", views.analytics_summary, name="analytics-summary"),
    path("sales-trend/", views.sales_trend, name="analytics-sales-trend"),
    path("product-contribution/", views.product_contribution, name="analytics-product-contribution"),
    path("vendor-delays/", views.vendor_delays_by_product, name="analytics-vendor-delays"),
    path("insights/", views.analytics_insights, name="analytics-insights"),
]
    