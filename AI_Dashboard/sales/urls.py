
# sales/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # صفحات اصلی فروش
    path('', views.sales_list, name='sales_list'),
    path('dashboard/', views.sales_dashboard, name='sales_dashboard'),
    path('add/', views.add_sale, name='add_sale'),
    path('edit/<int:pk>/', views.edit_sale, name='edit_sale'),
    path('delete/<int:pk>/', views.delete_sale, name='delete_sale'),
    path('detail/<int:pk>/', views.sale_detail, name='sale_detail'),
    
    # تراکنش‌ها
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/add/', views.add_transaction, name='add_transaction'),
    
    # APIها
    path('api/sales-data/', views.sales_api, name='sales_api'),
    path('api/chart-data/', views.sales_chart_data, name='sales_chart_data'),
    
    # خروجی گرفتن
    path('export/csv/', views.export_sales_csv, name='export_sales_csv'),
    path('export/excel/', views.export_sales_excel, name='export_sales_excel'),
]