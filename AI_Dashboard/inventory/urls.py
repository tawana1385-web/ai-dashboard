# inventory/urls.py - نسخه صحیح

from django.urls import path
from . import views

urlpatterns = [
    # صفحات اصلی موجودی
    path('', views.product_list, name='product_list'),
    path('dashboard/', views.inventory_dashboard, name='inventory_dashboard'),
    
    # مدیریت محصولات
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.add_product, name='add_product'),
    path('products/edit/<int:pk>/', views.edit_product, name='edit_product'),
    path('products/delete/<int:pk>/', views.delete_product, name='delete_product'),
    path('products/detail/<int:pk>/', views.product_detail, name='product_detail'),
    
    # حرکات انبار
    path('movements/', views.movement_list, name='movement_list'),
    path('movements/add/', views.add_movement, name='add_movement'),
    
    # گزارشات
    path('reports/low-stock/', views.low_stock_report, name='low_stock_report'),
    path('reports/inventory-value/', views.inventory_value_report, name='inventory_value_report'),
    
    # APIها
    path('api/products/', views.products_api, name='products_api'),
    path('api/movements/', views.movements_api, name='movements_api'),
    
    # خروجی گرفتن
    path('export/csv/', views.export_inventory_csv, name='export_inventory_csv'),
    path('export/excel/', views.export_inventory_excel, name='export_inventory_excel'),
]