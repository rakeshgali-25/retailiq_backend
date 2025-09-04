from django.urls import path
from . import views

urlpatterns = [
    path("summary/", views.sales_summary, name="sales-summary"),
    path("trend/", views.sales_trend, name="sales-trend"),
    path("by-product/", views.sales_by_product, name="sales-by-product"),
    path("recent-orders/", views.recent_orders, name="recent-orders"),

    # CRUD for Orders
   path('orders/', views.order_list, name='order-list'),            # GET, POST
    path('orders/<int:pk>/', views.order_detail, name='order-detail')# GET, PUT, DELETE
]
