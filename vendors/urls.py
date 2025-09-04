from django.urls import path
from . import views

urlpatterns = [
    path("summary/", views.vendor_summary, name="vendor-summary"),
    path("on-time/", views.vendor_on_time, name="vendor-on-time"),
    path("supply-contribution/", views.vendor_supply_contribution, name="vendor-supply"),
    path("details/", views.vendor_details, name="vendor-details"),
    path("vendors/", views.vendor_list, name="vendor-list")
]
