# expenses/urls.py - کد کامل

from django.urls import path
from . import views

urlpatterns = [
    # صفحات اصلی هزینه‌ها
    path('', views.expense_list, name='expense_list'),
    path('dashboard/', views.expense_dashboard, name='expense_dashboard'),
    path('add/', views.add_expense, name='add_expense'),
    path('edit/<int:pk>/', views.edit_expense, name='edit_expense'),
    path('delete/<int:pk>/', views.delete_expense, name='delete_expense'),
    path('detail/<int:pk>/', views.expense_detail, name='expense_detail'),
    
    # دسته‌بندی هزینه‌ها
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.add_category, name='add_category'),
    path('categories/edit/<int:pk>/', views.edit_category, name='edit_category'),
    path('categories/delete/<int:pk>/', views.delete_category, name='delete_category'),
    
    # APIها
    path('api/expense-data/', views.expense_api, name='expense_api'),
    path('api/chart-data/', views.expense_chart_data, name='expense_chart_data'),
    
    # خروجی گرفتن
    path('export/csv/', views.export_expenses_csv, name='export_expenses_csv'),
    path('export/excel/', views.export_expenses_excel, name='export_expenses_excel'),
]